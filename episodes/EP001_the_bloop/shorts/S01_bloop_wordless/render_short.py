"""Composite the EP001 wordless Short: toon plates + animated overlay -> MP4 with NOAA audio (+ music).

    python3 render_short.py                     # full Short -> render/EP001_S01_short.mp4
    python3 render_short.py --stills 30,200,400 # check frames only -> render/check/
    python3 render_short.py --music PATH.mp3    # add the owner's YouTube Audio Library track

Needs Pillow and FFmpeg. Plates come from build_short_3d.py (render/<plate>/frame_####.png).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EP = HERE.parents[1]
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO / "pipeline"))
from PIL import Image  # noqa: E402

from shpipe.shorts import locate_frame, shot_ranges, validate_short  # noqa: E402
from shpipe.shorts_render import render_frame  # noqa: E402

SHORT = json.loads((HERE / "short.json").read_text())
RENDER = HERE / "render"


def plate_path(shot, local_frame):
    folder = RENDER / shot["plate"]
    if shot["plate"] == "backdrop":
        return folder / "frame_0001.png"
    return folder / f"frame_{local_frame + 1:04d}.png"


def tracks_for(plate, cache={}):  # noqa: B006 - deliberate tiny cache
    if plate not in cache:
        p = RENDER / "tracks" / f"{plate}.json"
        cache[plate] = json.loads(p.read_text()) if p.is_file() else {}
    return cache[plate]


def frame_image(i):
    sid, lf, t = locate_frame(SHORT, i)
    shot = next(s for s in SHORT["shots"] if s["id"] == sid)
    plate = Image.open(plate_path(shot, lf)).convert("RGB")
    if plate.size != (SHORT["width"], SHORT["height"]):
        plate = plate.resize((SHORT["width"], SHORT["height"]))
    return render_frame(plate, shot, t, tracks_for(shot["plate"]), lf, base_dir=EP)


def audio_filter(music: Path | None, total_s: float):
    starts = {sid: a / SHORT["fps"] for sid, a, _ in shot_ranges(SHORT)}
    inputs, parts = [], []
    for k, cue in enumerate(SHORT["audio"]["cues"]):
        inputs += ["-i", str(EP / cue["file"])]
        delay = int((starts[cue["shot"]] + cue["at_s"]) * 1000)
        parts.append(f"[{k + 1}:a]atrim={cue['from_s']}:{cue['from_s'] + cue['dur_s']},asetpts=PTS-STARTPTS,"
                     f"afade=t=out:st={cue['dur_s'] - 0.4}:d=0.4,aresample=48000,aformat=channel_layouts=stereo,"
                     f"volume={cue.get('gain_db', 0)}dB,adelay={delay}|{delay}[c{k}]")
    labels = [f"[c{k}]" for k in range(len(SHORT["audio"]["cues"]))]
    if music:
        k = len(SHORT["audio"]["cues"]) + 1
        inputs += ["-i", str(music)]
        # music ducks under the real recording (sidechain) so the Bloop stays audible
        parts.append(f"[{k}:a]atrim=0:{total_s},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,"
                     f"afade=t=out:st={total_s - 1.5}:d=1.5,volume=-8dB[m]")
        parts.append(f"{''.join(labels)}amix=inputs={len(labels)}:normalize=0,asplit[fx][key]")
        parts.append("[m][key]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=400[md]")
        parts.append("[fx][md]amix=inputs=2:normalize=0[pre]")
    else:
        parts.append(f"{''.join(labels)}amix=inputs={len(labels)}:normalize=0[pre]")
    parts.append(f"[pre]apad,atrim=0:{total_s},loudnorm=I=-14:TP=-1.5:LRA=11[aout]")
    return inputs, ";".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stills", default="")
    ap.add_argument("--music", type=Path)
    ap.add_argument("--out", type=Path, default=RENDER / "EP001_S01_short.mp4")
    a = ap.parse_args()
    ledger = json.loads((EP / "research" / "claim_ledger.json").read_text())
    problems = validate_short(SHORT, ledger)
    if problems:
        sys.exit("short.json problems:\n" + "\n".join(problems))
    total = shot_ranges(SHORT)[-1][2]
    if a.stills:
        out = RENDER / "check"
        out.mkdir(parents=True, exist_ok=True)
        for i in (int(x) for x in a.stills.split(",")):
            frame_image(i).save(out / f"check_{i:04d}.jpg", quality=90)
        print("STILLS_DONE", out)
        return
    W, H, fps = SHORT["width"], SHORT["height"], SHORT["fps"]
    video = RENDER / "EP001_S01_video.partial.mp4"
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(fps), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
                            "-pix_fmt", "yuv420p", "-color_primaries", "bt709", "-color_trc", "bt709",
                            "-colorspace", "bt709", "-movflags", "+faststart", str(video)], stdin=subprocess.PIPE)
    for i in range(total):
        enc.stdin.write(frame_image(i).tobytes())
        if i % 60 == 0:
            print(f"frame {i}/{total}", flush=True)
    enc.stdin.close()
    if enc.wait() != 0:
        sys.exit("video encode failed")
    inputs, graph = audio_filter(a.music, total / fps)
    tmp = a.out.with_suffix(".partial.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video), *inputs, "-filter_complex", graph,
                    "-map", "0:v", "-map", "[aout]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                    "-shortest", str(tmp)], check=True)
    tmp.replace(a.out)
    video.unlink(missing_ok=True)
    print("SHORT_DONE", a.out)


if __name__ == "__main__":
    main()
