"""EP001 prototype: check → build set → build shot → validate → timing test → render → encode → report.

Runs inside Blender in background mode. Rerunnable; each run overwrites its outputs.

    blender --background --factory-startup --python episodes/EP001_ocean_prototype/scripts/run_ep001.py -- [options]

Options:
    --stages        comma list of: build,test,render,encode   (default: all)
    --resolution    auto | 1080 | 720   auto = 1080 unless the timing test predicts more than --budget-min
    --budget-min    minutes allowed for the full render in auto mode (default 60)
    --test-frames   frames timed before the full render (default 1,150,300)
    --engine        override the profile engine, e.g. CYCLES for machines without a GPU (look checks only)
    --samples       override render samples
    --percent       resolution percentage override (look checks only)
    --frames        render only these frames, e.g. 1,150,300, into renders/preview/stills/ (look checks)

Writes: blender/EP001_set.blend, blender/shots/S01.blend, renders/preview/S01/frame_####.png,
renders/preview/S01/render_log.json, renders/preview/progress.json, final/EP001_preview.mp4,
final/EP001_contact_sheet.jpg, final/EP001_render_report.json, logs/run_ep001.log
"""
from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

EP = Path(__file__).resolve().parents[1]
REPO = EP.parents[1]
for p in (REPO / "blender" / "scripts", REPO / "pipeline"):
    sys.path.insert(0, str(p))

import bpy  # noqa: E402

import sh_build_shot  # noqa: E402
import sh_environment_kit as kit  # noqa: E402
from sh_render import available_engines, load_profile, resolve_engine, write_render_log  # noqa: E402
from sh_validate_scene import validate_scene  # noqa: E402
from shpipe import ffmpeg  # noqa: E402
from shpipe.errors import ShError  # noqa: E402

SCENE_ID = "S01"
SET_BLEND = EP / "blender" / "EP001_set.blend"
RENDER_DIR = EP / "renders" / "preview" / SCENE_ID
FINAL = EP / "final"
LOG = EP / "logs" / "run_ep001.log"
REPORT = FINAL / "EP001_render_report.json"
PROGRESS = EP / "renders" / "preview" / "progress.json"


def log(msg: str) -> None:
    line = f"{datetime.now().isoformat(timespec='seconds')} {msg}"
    print(line, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def _args(argv):
    import argparse
    ap = argparse.ArgumentParser(prog="run_ep001.py")
    ap.add_argument("--stages", default="build,test,render,encode")
    ap.add_argument("--resolution", choices=["auto", "1080", "720"], default="auto")
    ap.add_argument("--budget-min", type=float, default=60.0)
    ap.add_argument("--test-frames", default="1,150,300")
    ap.add_argument("--engine")
    ap.add_argument("--samples", type=int)
    ap.add_argument("--percent", type=int)
    ap.add_argument("--frames")
    ap.add_argument("--tag", default="", help="suffix for final outputs, e.g. v2 → EP001_preview_v2.mp4")
    return ap.parse_args(argv)


def environment() -> dict:
    info = {"blender": bpy.app.version_string, "blender_python": sys.version.split()[0],
            "platform": f"{platform.system()} {platform.release()} {platform.machine()}",
            "engines": available_engines(), "cpu_count": os.cpu_count()}
    try:
        info["ffmpeg"] = ffmpeg.find("ffmpeg")
    except ShError as exc:
        info["ffmpeg"] = None
        info["ffmpeg_error"] = str(exc)
    info["disk_free_gb"] = round(shutil.disk_usage(EP).free / 1e9, 1)
    try:
        if platform.system() == "Darwin":
            info["memory_gb"] = round(int(subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True,
                                                         text=True).stdout) / 2**30, 1)
            info["chip"] = subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True,
                                          text=True).stdout.strip()
        else:
            kb = next(int(l.split()[1]) for l in open("/proc/meminfo") if l.startswith("MemTotal"))
            info["memory_gb"] = round(kb / 2**20, 1)
    except Exception as exc:  # informational only
        info["memory_error"] = str(exc)
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        gpus = {}
        for backend in ("METAL", "OPTIX", "CUDA", "HIP", "ONEAPI"):
            try:
                prefs.compute_device_type = backend
            except TypeError:
                continue
            prefs.refresh_devices()
            names = [d.name for d in prefs.devices if d.type != "CPU"]
            if names:
                gpus[backend] = names
        info["gpu"] = gpus
    except Exception as exc:
        info["gpu_error"] = str(exc)
    return info


def build(profile: str) -> dict:
    cfg = json.loads((EP / "scripts" / "ep001_set.json").read_text(encoding="utf-8"))
    bpy.ops.wm.read_factory_settings(use_empty=True)
    t0 = time.time()
    set_info = kit.build_set(cfg)
    SET_BLEND.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(SET_BLEND))
    shot = sh_build_shot.build_shot(EP, SCENE_ID, "preview", save=True, profile=profile)
    report = validate_scene(bpy.context.scene, EP)
    log(f"built set {set_info} and shot {shot['blend']} in {time.time() - t0:.1f}s; validation {report['status']}")
    if report["status"] == "fail":
        raise RuntimeError(f"scene validation failed: {report['errors']}")
    return {"set": set_info, "shot": shot, "validation": report}


def _apply_overrides(a) -> None:
    scene = bpy.context.scene
    if a.engine:
        scene.render.engine = resolve_engine(a.engine, available_engines())
        if scene.render.engine == "CYCLES":
            scene.cycles.device = "CPU" if not a.engine.endswith("GPU") else "GPU"
            scene.cycles.use_denoising = True
    if a.samples:
        if scene.render.engine == "CYCLES":
            scene.cycles.samples = a.samples
        else:
            scene.eevee.taa_render_samples = a.samples
    if a.percent:
        scene.render.resolution_percentage = a.percent


def _render_still(frame: int, out: Path) -> float:
    scene = bpy.context.scene
    scene.frame_set(frame)
    scene.render.filepath = str(out)
    t0 = time.time()
    bpy.ops.render.render(write_still=True)
    return time.time() - t0


def timing_test(frames: list[int]) -> dict:
    out_dir = EP / "renders" / "preview" / "_timing"
    times = {f: round(_render_still(f, out_dir / f"frame_{f:04d}.png"), 2) for f in frames}
    warm = list(times.values())[1:] or list(times.values())
    per_frame = sum(warm) / len(warm)
    scene = bpy.context.scene
    total = scene.frame_end - scene.frame_start + 1
    log(f"timing test {times} → {per_frame:.2f} s/frame (excluding first), estimate {per_frame * total / 60:.1f} min")
    return {"frames": times, "seconds_per_frame": round(per_frame, 2),
            "estimated_minutes": round(per_frame * total / 60, 1),
            "resolution": [scene.render.resolution_x, scene.render.resolution_y]}


def render_full() -> dict:
    scene = bpy.context.scene
    RENDER_DIR.mkdir(parents=True, exist_ok=True)
    for old in RENDER_DIR.glob("frame_*.png"):
        old.unlink()
    scene.render.filepath = str(RENDER_DIR / "frame_")
    applied = {"engine": scene.render.engine, "resolution": [scene.render.resolution_x, scene.render.resolution_y],
               "resolution_percentage": scene.render.resolution_percentage, "fps": scene.render.fps,
               "samples": scene.eevee.taa_render_samples if "EEVEE" in scene.render.engine else scene.cycles.samples,
               "view_transform": scene.view_settings.view_transform, "look": scene.view_settings.look,
               "exposure": scene.view_settings.exposure, "profile": scene.get("sh_profile")}
    total = scene.frame_end - scene.frame_start + 1
    t0 = time.time()
    state = {"done": 0}

    def on_post(sc, *_):
        state["done"] += 1
        el = time.time() - t0
        PROGRESS.write_text(json.dumps({"frame": sc.frame_current, "done": state["done"], "total": total,
                                        "elapsed_s": round(el, 1),
                                        "eta_s": round(el / state["done"] * (total - state["done"]), 1)}) + "\n")

    bpy.app.handlers.render_post.append(on_post)
    try:
        bpy.ops.render.render(animation=True)
    finally:
        bpy.app.handlers.render_post.remove(on_post)
    seconds = time.time() - t0
    frames = sorted(RENDER_DIR.glob("frame_*.png"))
    applied.update({"render_seconds": round(seconds, 1), "frames_written": len(frames),
                    "seconds_per_frame": round(seconds / max(len(frames), 1), 2)})
    write_render_log(scene, applied, RENDER_DIR / "render_log.json")
    log(f"rendered {len(frames)}/{total} frames in {seconds / 60:.1f} min")
    if len(frames) != total:
        raise RuntimeError(f"only {len(frames)} of {total} frames were written")
    return applied


def render_stills(frames: list[int]) -> dict:
    out_dir = EP / "renders" / "preview" / "stills"
    return {f: round(_render_still(f, out_dir / f"frame_{f:04d}.png"), 1) for f in frames}


def encode(tag: str = "") -> dict:
    sfx = f"_{tag}" if tag else ""
    pattern = str(RENDER_DIR / "frame_%04d.png")
    mp4 = ffmpeg.encode_sequence(pattern, FINAL / f"EP001_preview{sfx}.mp4", fps=30, crf=18, preset="medium",
                                 start_number=1)
    sheet = FINAL / f"EP001_contact_sheet{sfx}.jpg"
    ffmpeg.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-framerate", "30", "-start_number", "1",
                "-i", pattern, "-vf", "select='not(mod(n\\,60))',scale=480:-1,tile=5x1", "-frames:v", "1",
                "-q:v", "3", str(sheet)])
    info = ffmpeg.probe(mp4)
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    out = {"mp4": str(mp4.relative_to(REPO)), "contact_sheet": str(sheet.relative_to(REPO)),
           "duration_s": float(info["format"]["duration"]), "size_mb": round(mp4.stat().st_size / 1e6, 1),
           "video": {k: v.get(k) for k in ("codec_name", "width", "height", "r_frame_rate", "pix_fmt",
                                           "color_space", "color_primaries", "color_transfer")}}
    log(f"encoded {out}")
    return out


def main(argv) -> int:
    a = _args(argv)
    stages = set(a.stages.split(","))
    report = {"started": datetime.now().isoformat(timespec="seconds"), "args": vars(a), "status": "running",
              "problems": []}
    try:
        report["environment"] = environment()
        log(f"environment {report['environment']}")
        profile = "preview" if a.resolution == "720" else "preview_hd"
        if "build" in stages or not (EP / "blender" / "shots" / f"{SCENE_ID}.blend").is_file():
            report["build"] = build(profile)
        else:
            bpy.ops.wm.open_mainfile(filepath=str(EP / "blender" / "shots" / f"{SCENE_ID}.blend"))
        _apply_overrides(a)
        if a.frames:
            report["stills"] = render_stills([int(f) for f in a.frames.split(",")])
            report["status"] = "stills_done"
            return 0
        if "test" in stages:
            report["timing"] = timing_test([int(f) for f in a.test_frames.split(",")])
            if a.resolution == "auto" and report["timing"]["estimated_minutes"] > a.budget_min:
                report["problems"].append(f"1080p estimate {report['timing']['estimated_minutes']} min exceeds "
                                          f"budget {a.budget_min} min; falling back to 1280x720")
                report["build"] = build("preview")
                _apply_overrides(a)
                report["timing_720"] = timing_test([int(f) for f in a.test_frames.split(",")][:2])
        if "render" in stages:
            report["render"] = render_full()
        if "encode" in stages:
            report["encode"] = encode(a.tag)
        report["status"] = "success"
        return 0
    except Exception as exc:
        report["status"] = "failed"
        report["error"] = f"{exc.__class__.__name__}: {exc}"
        report["traceback"] = traceback.format_exc()
        log(f"FAILED: {report['error']}\n{report['traceback']}")
        return 1
    finally:
        report["finished"] = datetime.now().isoformat(timespec="seconds")
        FINAL.mkdir(parents=True, exist_ok=True)
        out = REPORT.with_name(f"EP001_render_report_{a.tag}.json") if a.tag else REPORT
        out.write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")


if __name__ == "__main__":
    code = main(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    if bpy.app.background:
        sys.exit(code)
