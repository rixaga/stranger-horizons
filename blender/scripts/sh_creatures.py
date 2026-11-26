"""Procedural creatures for illustrated theories (original designs, no external assets).

Every creature is tagged sh_kind="creature" and carries the on-screen label it must be shown
with, so validation can check that imagined animals never appear unlabelled.

    make_shark(col, cfg)   -> {"rig", "mesh"}   tapered body, fins, lunate tail, eyes, countershading
    swim_cycle(rig, ...)   travelling side-to-side wave along the spine (head steady, tail sweeping)
    follow_path(obj, pts)  constant-speed path through points, nose along the direction of travel, banking

Conventions: the creature's nose points +X at rest, length runs toward -X, +Z is up.
"""
from __future__ import annotations

import math
import random

import bmesh
import bpy
from mathutils import Euler, Matrix, Vector

IMAGINED = "Imagined — theory, not evidence"


# ------------------------------------------------------------------ helpers

def _interp(table, t):
    """Piecewise-linear lookup in [(t, v), ...] with smoothstep easing between points."""
    if t <= table[0][0]:
        return table[0][1]
    for (t0, v0), (t1, v1) in zip(table, table[1:]):
        if t <= t1:
            u = (t - t0) / (t1 - t0)
            u = u * u * (3 - 2 * u)
            return v0 + (v1 - v0) * u
    return table[-1][1]


def _skin_material(name: str, top, belly, seed: int = 0):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    if bpy.app.version < (5, 0, 0) and not mat.use_nodes:
        mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    rng = nt.nodes.new("ShaderNodeMapRange")
    rng.clamp = True
    rng.inputs["From Min"].default_value = -0.35
    rng.inputs["From Max"].default_value = 0.25
    coord = nt.nodes.new("ShaderNodeTexCoord")
    mottle = nt.nodes.new("ShaderNodeTexNoise")
    mottle.inputs["Scale"].default_value = 0.9
    mottle.inputs["Detail"].default_value = 6.0
    mix_n = nt.nodes.new("ShaderNodeMath")
    mix_n.operation = "MULTIPLY_ADD"
    mix_n.inputs[1].default_value = 0.18
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*belly, 1)
    ramp.color_ramp.elements[1].color = (*top, 1)
    ramp.color_ramp.elements[0].position = 0.35
    ramp.color_ramp.elements[1].position = 0.6
    fine = nt.nodes.new("ShaderNodeTexNoise")
    fine.inputs["Scale"].default_value = 25.0
    fine.inputs["Detail"].default_value = 8.0
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.15
    L = nt.links
    L.new(geo.outputs["Normal"], sep.inputs[0])
    L.new(sep.outputs["Z"], rng.inputs["Value"])
    L.new(coord.outputs["Object"], mottle.inputs["Vector"])
    L.new(coord.outputs["Object"], fine.inputs["Vector"])
    L.new(mottle.outputs["Fac"], mix_n.inputs[0])
    L.new(rng.outputs["Result"], mix_n.inputs[2])
    L.new(mix_n.outputs[0], ramp.inputs["Fac"])
    L.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    L.new(fine.outputs["Fac"], bump.inputs["Height"])
    L.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    bsdf.inputs["Roughness"].default_value = 0.42
    L.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def _flat_material(name, color, roughness=0.2):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    if bpy.app.version < (5, 0, 0) and not mat.use_nodes:
        mat.use_nodes = True
    bsdf = next((n for n in mat.node_tree.nodes if n.bl_idname == "ShaderNodeBsdfPrincipled"), None)
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*color, 1)
        bsdf.inputs["Roughness"].default_value = roughness
    return mat


def _fin(bm, outline, thickness, orient: Matrix, origin: Vector):
    """Extruded fin from a 2D outline (u along body X, v away from the body); thinner toward the edge."""
    verts_a, verts_b = [], []
    cu = sum(p[0] for p in outline) / len(outline)
    cv = sum(p[1] for p in outline) / len(outline)
    for u, v in outline:
        edge = min(1.0, math.hypot(u - cu, v - cv) / (max(abs(v) for _, v in outline) + 1e-6))
        half = thickness * 0.5 * (1.0 - 0.75 * edge)
        p = Vector((u, v, 0.0))
        verts_a.append(bm.verts.new(origin + orient @ (p + Vector((0, 0, half)))))
        verts_b.append(bm.verts.new(origin + orient @ (p - Vector((0, 0, half)))))
    created = verts_a + verts_b
    bm.faces.new(verts_a)
    bm.faces.new(list(reversed(verts_b)))
    n = len(outline)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((verts_a[i], verts_b[i], verts_b[j], verts_a[j]))
    return created


# ------------------------------------------------------------------ shark

# half-height of the body as a fraction of total length, from nose (t=0) to tail base (t=1)
SHARK_HEIGHT = [(0.0, 0.006), (0.025, 0.021), (0.07, 0.043), (0.15, 0.068), (0.30, 0.092), (0.45, 0.095),
                (0.60, 0.080), (0.75, 0.052), (0.90, 0.024), (1.0, 0.017)]
SHARK_WIDTH_RATIO = [(0.0, 0.85), (0.3, 0.80), (0.7, 0.62), (1.0, 0.55)]


def make_shark(col, cfg: dict) -> dict:
    name = cfg.get("name", "CR_Shark")
    L = float(cfg.get("length_m", 15.0))
    rings, segs = int(cfg.get("rings", 72)), int(cfg.get("segments", 28))
    body_len = 0.87 * L
    rng = random.Random(cfg.get("seed", 1))
    bm = bmesh.new()
    parts: dict[str, list] = {}

    # body: superelliptic rings, belly a little flatter than the back, snout dipping slightly
    ring_verts = []
    for i in range(rings + 1):
        t = i / rings
        x = -t * body_len
        h = _interp(SHARK_HEIGHT, t) * L
        w = h * _interp(SHARK_WIDTH_RATIO, t)
        cz = -0.012 * L * max(0.0, 1 - t / 0.08)
        ring = []
        for k in range(segs):
            a = 2 * math.pi * k / segs
            s, c = math.sin(a), math.cos(a)
            z = h * (abs(s) ** 0.85) * math.copysign(1, s) * (1.0 if s > 0 else 0.82)
            y = w * (abs(c) ** 0.9) * math.copysign(1, c)
            ring.append(bm.verts.new((x, y, z + cz)))
        ring_verts.append(ring)
    for i in range(rings):
        a, b = ring_verts[i], ring_verts[i + 1]
        for k in range(segs):
            k2 = (k + 1) % segs
            bm.faces.new((a[k], b[k], b[k2], a[k2]))
    nose = bm.verts.new((0.006 * L, 0, -0.012 * L))
    for k in range(segs):
        bm.faces.new((nose, ring_verts[0][(k + 1) % segs], ring_verts[0][k]))
    tail_cap = bm.verts.new((-body_len - 0.002 * L, 0, 0))
    for k in range(segs):
        bm.faces.new((tail_cap, ring_verts[-1][k], ring_verts[-1][(k + 1) % segs]))
    parts["body"] = [v for r in ring_verts for v in r] + [nose, tail_cap]

    def top(t):
        return _interp(SHARK_HEIGHT, t) * L

    side = Matrix.Rotation(math.radians(90), 4, "X").to_3x3()  # fin plane = XZ (v -> +Z)
    th = 0.012 * L
    # first dorsal: tall, swept back, slightly concave trailing edge
    parts["fin_dorsal"] = _fin(bm, [(0.0, -0.01 * L), (-0.075 * L, 0.125 * L), (-0.095 * L, 0.115 * L),
                                    (-0.105 * L, 0.06 * L), (-0.14 * L, -0.005 * L)], th, side,
                               Vector((-0.34 * L, 0, top(0.38) - 0.01 * L)))
    parts["fin_dorsal2"] = _fin(bm, [(0.0, -0.005 * L), (-0.02 * L, 0.03 * L), (-0.03 * L, 0.028 * L),
                                     (-0.04 * L, 0.0)], th * 0.6, side, Vector((-0.70 * L, 0, top(0.80) - 0.004 * L)))
    down = Matrix.Rotation(math.radians(-90), 4, "X").to_3x3()  # v -> -Z
    parts["fin_anal"] = _fin(bm, [(0.0, -0.005 * L), (-0.02 * L, 0.03 * L), (-0.032 * L, 0.026 * L),
                                  (-0.04 * L, 0.0)], th * 0.6, down, Vector((-0.71 * L, 0, -top(0.81) * 0.82 + 0.004 * L)))
    # caudal: lunate, upper lobe longer (heterocercal)
    parts["fin_caudal"] = _fin(bm, [(0.03 * L, 0.02 * L), (-0.10 * L, 0.175 * L), (-0.115 * L, 0.165 * L),
                                    (-0.05 * L, 0.03 * L), (-0.10 * L, -0.135 * L), (-0.085 * L, -0.14 * L),
                                    (0.03 * L, -0.02 * L)], th * 0.8, side, Vector((-body_len + 0.02 * L, 0, 0.0)))
    # pectorals and pelvics, mirrored; angled down and back
    for sgn, tag in ((1, "L"), (-1, "R")):
        orient = (Matrix.Rotation(math.radians(-22 * sgn), 3, "X")
                  @ Matrix.Rotation(math.radians(0 if sgn > 0 else 180), 3, "X"))
        pect = [(0.0, 0.0), (-0.07 * L, 0.20 * L), (-0.10 * L, 0.205 * L), (-0.085 * L, 0.08 * L), (-0.09 * L, 0.0)]
        parts[f"fin_pectoral_{tag}"] = _fin(bm, pect, th, orient,
                                            Vector((-0.20 * L, sgn * 0.6 * _interp(SHARK_HEIGHT, 0.22) * L * 0.8,
                                                    -0.45 * top(0.22))))
        pelv = [(0.0, 0.0), (-0.025 * L, 0.04 * L), (-0.04 * L, 0.035 * L), (-0.04 * L, 0.0)]
        parts[f"fin_pelvic_{tag}"] = _fin(bm, pelv, th * 0.6, orient,
                                          Vector((-0.58 * L, sgn * 0.5 * top(0.62) * 0.7, -0.7 * top(0.62))))
    # eyes: small dark glossy spheres set into the head
    eye_parts = []
    for sgn in (1, -1):
        geom = bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=0.0115 * L)
        c = Vector((-0.075 * L, sgn * 0.80 * top(0.075) * 0.85, 0.30 * top(0.075)))
        for v in geom["verts"]:
            v.co += c
        eye_parts += geom["verts"]
        for f in {f for v in geom["verts"] for f in v.link_faces}:
            f.material_index = 1
    parts["eyes"] = eye_parts

    mesh = bpy.data.meshes.new(name)
    bm.normal_update()
    index_of = {}
    bm.verts.index_update()
    for key, verts in parts.items():
        index_of[key] = [v.index for v in verts]
    bm.to_mesh(mesh)
    bm.free()
    for p in mesh.polygons:
        p.use_smooth = True
    rest = mesh.attributes.new("rest_pos", "FLOAT_VECTOR", "POINT")   # markings stay put while the body bends
    rest.data.foreach_set("vector", [c for v in mesh.vertices for c in v.co])
    skin = _skin_material(f"{name}_skin", tuple(cfg.get("top_color", (0.055, 0.07, 0.08))),
                          tuple(cfg.get("belly_color", (0.40, 0.42, 0.43))), rng.randint(0, 99))
    _add_shark_markings(skin, L)
    mesh.materials.append(skin)
    mesh.materials.append(_flat_material(f"{name}_eye", (0.01, 0.01, 0.012), 0.08))
    obj = bpy.data.objects.new(name, mesh)
    col.objects.link(obj)
    obj["sh_kind"] = "creature"
    obj["sh_label"] = cfg.get("label", IMAGINED)
    obj["sh_parts"] = list(parts)
    for key, idx in index_of.items():
        if key.startswith("fin_"):
            obj.vertex_groups.new(name=key).add(idx, 1.0, "REPLACE")
    sub = obj.modifiers.new("Subdivision", "SUBSURF")
    sub.levels, sub.render_levels = 1, int(cfg.get("render_subdiv", 2))

    rig = _spine_rig(col, f"{name}_Rig", L, int(cfg.get("bones", 8)))
    _weight_to_spine(obj, rig, L)
    obj.parent = rig
    arm = obj.modifiers.new("Armature", "ARMATURE")
    arm.object = rig
    # armature before subdivision so the smooth surface follows the bend
    bpy.context.view_layer.objects.active = obj
    while obj.modifiers[0].name != "Armature":
        obj.modifiers.move(obj.modifiers.find("Armature"), 0)
    rig["sh_kind"] = "creature_rig"
    rig["sh_label"] = obj["sh_label"]
    return {"rig": rig, "mesh": obj}


def _add_shark_markings(mat, L):
    """Five gill slits and a mouth line, darkened into the base colour, mapped on the rest pose."""
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.bl_idname == "ShaderNodeBsdfPrincipled")
    base_link = next(l for l in nt.links if l.to_socket == bsdf.inputs["Base Color"])
    src = base_link.from_socket
    attr = nt.nodes.new("ShaderNodeAttribute")
    attr.attribute_name = "rest_pos"
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(attr.outputs["Vector"], sep.inputs[0])

    def math_node(op, a, b=None, clamp=False):
        n = nt.nodes.new("ShaderNodeMath")
        n.operation = op
        n.use_clamp = clamp
        for i, val in enumerate((a, b)):
            if val is None:
                continue
            if isinstance(val, (int, float)):
                n.inputs[i].default_value = val
            else:
                nt.links.new(val, n.inputs[i])
        return n.outputs[0]

    x, y, z = sep.outputs["X"], sep.outputs["Y"], sep.outputs["Z"]
    # gills: 5 thin vertical bands between x = -0.165L and -0.225L, on the sides only
    phase = math_node("MULTIPLY", math_node("ADD", x, 0.165 * L), 2 * math.pi / (0.015 * L))
    bands = math_node("GREATER_THAN", math_node("COSINE", phase), 0.82)
    in_x = math_node("MULTIPLY", math_node("GREATER_THAN", x, -0.226 * L), math_node("LESS_THAN", x, -0.162 * L))
    on_side = math_node("GREATER_THAN", math_node("ABSOLUTE", y), 0.035 * L)
    mid_z = math_node("LESS_THAN", math_node("ABSOLUTE", math_node("ADD", z, 0.006 * L)), 0.042 * L)
    gills = math_node("MULTIPLY", math_node("MULTIPLY", bands, in_x), math_node("MULTIPLY", on_side, mid_z))
    # mouth: a dark crescent under the snout, from x=-0.025L back to -0.11L, just below the side midline
    mouth_z = math_node("ADD", math_node("MULTIPLY", x, 0.20), -0.018 * L)      # line sloping down and back
    near = math_node("LESS_THAN", math_node("ABSOLUTE", math_node("SUBTRACT", z, mouth_z)), 0.0025 * L)
    m_x = math_node("MULTIPLY", math_node("LESS_THAN", x, -0.025 * L), math_node("GREATER_THAN", x, -0.11 * L))
    mouth = math_node("MULTIPLY", near, m_x)
    mark = math_node("MAXIMUM", gills, mouth)
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs["B"].default_value = (0.008, 0.008, 0.01, 1)
    nt.links.new(math_node("MULTIPLY", mark, 0.85), mix.inputs["Factor"])
    nt.links.new(src, mix.inputs["A"])
    nt.links.remove(base_link)
    nt.links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])


def _spine_rig(col, name, L, n):
    arm = bpy.data.armatures.new(name)
    rig = bpy.data.objects.new(name, arm)
    col.objects.link(rig)
    view_layer = bpy.context.view_layer
    view_layer.objects.active = rig
    prev_mode = rig.mode
    bpy.ops.object.mode_set(mode="EDIT")
    prev = None
    for i in range(n):
        b = arm.edit_bones.new(f"spine_{i}")
        b.head = (-i * L / n, 0, 0)
        b.tail = (-(i + 1) * L / n, 0, 0)
        b.roll = 0.0
        if prev:
            b.parent = prev
            b.use_connect = True
        prev = b
    bpy.ops.object.mode_set(mode=prev_mode if prev_mode != "EDIT" else "OBJECT")
    for pb in rig.pose.bones:
        pb.rotation_mode = "XYZ"
    return rig


def _weight_to_spine(obj, rig, L):
    n = len(rig.data.bones)
    groups = [obj.vertex_groups.new(name=f"spine_{i}") for i in range(n)]
    for v in obj.data.vertices:
        s = min(max(-v.co.x / L * n, 0.0), float(n))
        c = s - 0.5
        if c <= 0:
            groups[0].add([v.index], 1.0, "REPLACE")
        elif c >= n - 1:
            groups[n - 1].add([v.index], 1.0, "REPLACE")
        else:
            i = int(math.floor(c))
            f = c - i
            groups[i].add([v.index], 1.0 - f, "REPLACE")
            groups[i + 1].add([v.index], f, "REPLACE")


# ------------------------------------------------------------------ motion

def swim_cycle(rig, frame_start: int, frame_end: int, fps: int = 30, freq_hz: float = 0.35,
               head_deg: float = 2.0, tail_deg: float = 16.0, wave_per_bone: float = 0.55, step: int = 2):
    """Side-to-side travelling wave: amplitude grows quadratically from head to tail."""
    bones = sorted(rig.pose.bones, key=lambda b: int(b.name.split("_")[1]))
    n = len(bones)
    for f in range(frame_start, frame_end + 1, step):
        t = (f - frame_start) / fps
        for i, pb in enumerate(bones):
            amp = math.radians(head_deg + (tail_deg - head_deg) * (i / max(n - 1, 1)) ** 2)
            # local rotation adds up along the chain, so give each bone only its share of the bend
            share = amp / (1 + 0.6 * i)
            pb.rotation_euler = (0.0, 0.0, share * math.sin(2 * math.pi * freq_hz * t - wave_per_bone * i))
            pb.keyframe_insert("rotation_euler", index=2, frame=f)
    _set_interp(rig, "BEZIER")


def _catmull(pts, t):
    n = len(pts) - 1
    seg = min(int(t * n), n - 1)
    u = t * n - seg
    p0 = pts[max(seg - 1, 0)]
    p1, p2 = pts[seg], pts[seg + 1]
    p3 = pts[min(seg + 2, n)]
    return 0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3)


def follow_path(obj, points, frame_start: int, frame_end: int, bank_deg: float = 20.0, step: int = 2):
    """Constant-speed travel through points; nose (+X) along the tangent, rolling into turns."""
    pts = [Vector(p) for p in points]
    dense = [_catmull(pts, i / 400) for i in range(401)]
    cum = [0.0]
    for a, b in zip(dense, dense[1:]):
        cum.append(cum[-1] + (b - a).length)
    total = cum[-1]

    def at(d):
        d = min(max(d, 0.0), total)
        j = next(k for k in range(1, len(cum)) if cum[k] >= d) if d > 0 else 1
        f = (d - cum[j - 1]) / max(cum[j] - cum[j - 1], 1e-9)
        return dense[j - 1].lerp(dense[j], f)

    obj.rotation_mode = "XYZ"
    span = frame_end - frame_start
    prev_eul = None
    frames = list(range(frame_start, frame_end + 1, step))
    if frames[-1] != frame_end:
        frames.append(frame_end)
    for fr in frames:
        d = total * (fr - frame_start) / span
        p = at(d)
        ahead, behind = at(d + 0.5), at(d - 0.5)
        tangent = (ahead - behind).normalized()
        q = tangent.to_track_quat("X", "Z")
        # curvature in the horizontal plane sets the bank
        a2, b2 = at(d + 3.0) - p, p - at(d - 3.0)
        turn = math.atan2(a2.x * b2.y - a2.y * b2.x, a2.x * b2.x + a2.y * b2.y) if a2.length and b2.length else 0.0
        roll = max(-1.0, min(1.0, turn / math.radians(25))) * math.radians(bank_deg)
        eul = (q.to_matrix() @ Matrix.Rotation(-roll, 3, "X")).to_euler("XYZ")
        if prev_eul is not None:
            eul.make_compatible(prev_eul)
        prev_eul = eul
        obj.location = p
        obj.rotation_euler = eul
        obj.keyframe_insert("location", frame=fr)
        obj.keyframe_insert("rotation_euler", frame=fr)
    _set_interp(obj, "LINEAR")


def _set_interp(obj, kind):
    action = obj.animation_data.action if obj.animation_data else None
    if not action:
        return
    curves = list(getattr(action, "fcurves", []) or [])
    if not curves:
        for layer in getattr(action, "layers", []):
            for strip in layer.strips:
                for bag in getattr(strip, "channelbags", []):
                    curves.extend(bag.fcurves)
    for fc in curves:
        for kp in fc.keyframe_points:
            kp.interpolation = kind
