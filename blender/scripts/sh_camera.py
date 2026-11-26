"""Camera move presets (config/camera_presets.json).

compute_keyframes() is pure Python and unit-tested. build_camera_move() creates or
updates a camera in Blender that aims at a target empty via Track To, with Bezier
(eased) keyframes. Safe to rerun with the same name.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CAMERA_PRESETS = REPO / "config" / "camera_presets.json"


def load_moves(path: Path = CAMERA_PRESETS) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))["moves"]


def _add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def compute_keyframes(move: str, target=(0.0, 0.0, 0.0), fps: int = 30, frame_start: int = 1,
                      duration_s: float | None = None, moves: dict | None = None,
                      lens_mm: float | None = None) -> list[dict]:
    """Return [{frame, location, lens}] for a named move. The final framing is held for hold_s."""
    spec = (moves or load_moves())[move]
    duration = float(duration_s if duration_s is not None else spec["duration_s"])
    hold = min(float(spec.get("hold_s", 0.0)), duration * 0.5)
    move_frames = round((duration - hold) * fps)
    end_frame = frame_start + round(duration * fps)
    lens = lens_mm or spec.get("lens_mm", 35)
    keys: list[dict] = []
    if "orbit" in spec:
        o = spec["orbit"]
        steps = 6
        for i in range(steps + 1):
            t = i / steps
            a = math.radians(o["start_deg"] + (o["end_deg"] - o["start_deg"]) * t)
            loc = _add(target, (o["radius_m"] * math.cos(a), o["radius_m"] * math.sin(a), o["height_m"]))
            keys.append({"frame": frame_start + round(t * move_frames), "location": loc, "lens": lens})
    else:
        for k in spec["keys"]:
            keys.append({"frame": frame_start + round(k["t"] * move_frames), "location": _add(target, k["offset"]),
                         "lens": lens})
    if keys[-1]["frame"] != end_frame:
        keys.append({"frame": end_frame, "location": keys[-1]["location"], "lens": lens})
    return keys


def compute_path_keyframes(keys: list[dict], fps: int = 30, frame_start: int = 1) -> list[dict]:
    """Explicit camera keys -> [{frame, location, target, lens, relative_to}].

    Each key: t_s (seconds from frame_start), location and target in metres, optional lens_mm
    (carried forward), optional relative_to (object name: location/target are in that object's
    local space, so the camera can ride a moving vehicle)."""
    out: list[dict] = []
    lens = 35.0
    last_t = -1.0
    for k in keys:
        t = float(k["t_s"])
        if t <= last_t:
            raise ValueError(f"camera keys must have increasing t_s (got {t} after {last_t})")
        last_t = t
        lens = float(k.get("lens_mm", lens))
        out.append({"frame": frame_start + round(t * fps), "location": tuple(k["location"]),
                    "target": tuple(k["target"]), "lens": lens, "relative_to": k.get("relative_to")})
    return out


# ---------------------------------------------------------------- Blender-only

def _ensure_camera(scene, name: str):
    import bpy
    cam = bpy.data.objects.get(name)
    if cam is None:
        cam = bpy.data.objects.new(name, bpy.data.cameras.new(name))
        scene.collection.objects.link(cam)
    aim = bpy.data.objects.get(f"{name}_Target")
    if aim is None:
        aim = bpy.data.objects.new(f"{name}_Target", None)
        aim.empty_display_size = 0.5
        scene.collection.objects.link(aim)
    for ob in (cam, aim):
        ob.animation_data_clear()
    cam.data.animation_data_clear()
    con = cam.constraints.get("SH_Aim") or cam.constraints.new("TRACK_TO")
    con.name = "SH_Aim"
    con.target = aim
    con.track_axis = "TRACK_NEGATIVE_Z"
    con.up_axis = "UP_Y"
    return cam, aim


def build_keyed_camera(scene, keys: list[dict], name: str = "SH_Camera", make_active: bool = True,
                       bake_step: int = 5):
    """Camera from explicit keys (see compute_path_keyframes). Between two keys relative to the same
    object, extra keys are baked every bake_step frames so the camera stays locked to it."""
    from mathutils import Vector
    frames = compute_path_keyframes(keys, scene.render.fps, scene.frame_start)
    cam, aim = _ensure_camera(scene, name)

    def world(obj_name, local, frame):
        if not obj_name:
            return Vector(local)
        scene.frame_set(frame)
        return scene.objects[obj_name].matrix_world @ Vector(local)

    samples = []  # (frame, cam_local, aim_local, lens, relative_to)
    for a, b in zip(frames, frames[1:] + [None]):
        samples.append((a["frame"], a["location"], a["target"], a["lens"], a["relative_to"]))
        if b and a["relative_to"] and a["relative_to"] == b["relative_to"]:
            for f in range(a["frame"] + bake_step, b["frame"], bake_step):
                u = (f - a["frame"]) / (b["frame"] - a["frame"])
                lerp = lambda p, q: tuple(x + (y - x) * u for x, y in zip(p, q))  # noqa: E731
                samples.append((f, lerp(a["location"], b["location"]), lerp(a["target"], b["target"]),
                                a["lens"] + (b["lens"] - a["lens"]) * u, a["relative_to"]))
    resolved = [(f, world(rel, loc, f), world(rel, tgt, f), lens, rel) for f, loc, tgt, lens, rel in samples]
    for f, loc, tgt, lens, _ in resolved:
        cam.location = loc
        cam.keyframe_insert("location", frame=f)
        aim.location = tgt
        aim.keyframe_insert("location", frame=f)
        cam.data.lens = lens
        cam.data.keyframe_insert("lens", frame=f)
    baked = {f for f, *_rest, rel in resolved if rel}
    for ob in (cam, aim, cam.data):
        for fc in _fcurves(ob.animation_data.action):
            for kp in fc.keyframe_points:
                # locked-on stretches stay linear so the camera does not wobble against its vehicle
                kp.interpolation = "LINEAR" if int(round(kp.co.x)) in baked and fc.data_path == "location" else "BEZIER"
                kp.handle_left_type = kp.handle_right_type = "AUTO_CLAMPED"
            fc.update()
    scene.frame_set(scene.frame_start)
    if make_active:
        scene.camera = cam
    return cam, frames


def _fcurves(action):
    """F-curves of an action under both the legacy and the layered (4.4+/5.x) animation APIs."""
    if hasattr(action, "fcurves"):
        try:
            return list(action.fcurves)
        except (AttributeError, RuntimeError):
            pass
    curves = []
    for layer in getattr(action, "layers", []):
        for strip in layer.strips:
            for bag in getattr(strip, "channelbags", []):
                curves.extend(bag.fcurves)
    return curves


def build_camera_move(scene, move: str, target=(0.0, 0.0, 0.0), frame_start: int | None = None,
                      duration_s: float | None = None, name: str = "SH_Camera", make_active: bool = True,
                      lens_mm: float | None = None):
    import bpy
    moves = load_moves()
    spec = moves[move]
    frame_start = scene.frame_start if frame_start is None else frame_start
    keys = compute_keyframes(move, target, scene.render.fps, frame_start, duration_s, moves, lens_mm)

    cam = bpy.data.objects.get(name)
    if cam is None:
        cam = bpy.data.objects.new(name, bpy.data.cameras.new(name))
        scene.collection.objects.link(cam)
    cam.animation_data_clear()
    cam.data.animation_data_clear()
    aim = bpy.data.objects.get(f"{name}_Target")
    if aim is None:
        aim = bpy.data.objects.new(f"{name}_Target", None)
        aim.empty_display_size = 0.5
        scene.collection.objects.link(aim)
    aim.location = target
    con = cam.constraints.get("SH_Aim") or cam.constraints.new("TRACK_TO")
    con.name = "SH_Aim"
    con.target = aim
    con.track_axis = "TRACK_NEGATIVE_Z"
    con.up_axis = "UP_Y"

    for k in keys:
        cam.location = k["location"]
        cam.keyframe_insert("location", frame=k["frame"])
        cam.data.lens = k["lens"]
        cam.data.keyframe_insert("lens", frame=k["frame"])
    for fc in _fcurves(cam.animation_data.action):
        for kp in fc.keyframe_points:
            kp.interpolation = "BEZIER"
            kp.handle_left_type = kp.handle_right_type = "AUTO_CLAMPED"
        fc.update()
    drift = spec.get("drift_cm", 0.0)
    if drift:
        for fc in _fcurves(cam.animation_data.action):
            if fc.data_path == "location":
                mod = fc.modifiers.new("NOISE")
                mod.strength = drift / 100.0
                mod.scale = 60.0
                mod.phase = fc.array_index * 17.0
    if make_active:
        scene.camera = cam
    return cam, keys
