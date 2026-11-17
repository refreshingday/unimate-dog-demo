"""Build a simple rigged, skinned dog in Blender (bpy) and export it as GLB.

Blender coordinates: Z up, the dog faces -Y, so its left side is +X.
Usage: python -I build_dog.py <out_dir>
"""
import sys, os, math
import bpy, bmesh
from mathutils import Vector

out_dir = sys.argv[-1]
os.makedirs(out_dir, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)

# ── Skeleton ────────────────────────────────────────────────────────────────
# name: (head, tail, parent)
B = {
    "Hips":   ((0, 0.30, 0.62), (0, 0.10, 0.64), None),
    "Spine":  ((0, 0.10, 0.64), (0, -0.10, 0.65), "Hips"),
    "Spine1": ((0, -0.10, 0.65), (0, -0.30, 0.66), "Spine"),
    "Neck":   ((0, -0.30, 0.66), (0, -0.42, 0.84), "Spine1"),
    "Head":   ((0, -0.42, 0.84), (0, -0.62, 0.86), "Neck"),
    "Jaw":    ((0, -0.48, 0.79), (0, -0.66, 0.78), "Head"),
    "Tail":   ((0, 0.34, 0.66), (0, 0.46, 0.74), "Hips"),
    "Tail1":  ((0, 0.46, 0.74), (0, 0.56, 0.82), "Tail"),
    "Tail2":  ((0, 0.56, 0.82), (0, 0.64, 0.88), "Tail1"),
}
for s, x in (("L", 1), ("R", -1)):
    B[f"Ear_{s}"] = ((0.06 * x, -0.45, 0.92), (0.10 * x, -0.43, 1.02), "Head")
    # front leg
    B[f"{s}_Shoulder"] = ((0.05 * x, -0.28, 0.62), (0.11 * x, -0.30, 0.50), "Spine1")
    B[f"{s}_UpperArm"] = ((0.11 * x, -0.30, 0.50), (0.11 * x, -0.29, 0.30), f"{s}_Shoulder")
    B[f"{s}_Forearm"] = ((0.11 * x, -0.29, 0.30), (0.11 * x, -0.31, 0.08), f"{s}_UpperArm")
    B[f"{s}_Hand"] = ((0.11 * x, -0.31, 0.08), (0.11 * x, -0.38, 0.03), f"{s}_Forearm")
    # hind leg
    B[f"{s}_Thigh"] = ((0.11 * x, 0.28, 0.56), (0.11 * x, 0.22, 0.34), "Hips")
    B[f"{s}_Calf"] = ((0.11 * x, 0.22, 0.34), (0.11 * x, 0.32, 0.12), f"{s}_Thigh")
    B[f"{s}_Foot"] = ((0.11 * x, 0.32, 0.12), (0.11 * x, 0.30, 0.04), f"{s}_Calf")
    B[f"{s}_Toe"] = ((0.11 * x, 0.30, 0.04), (0.11 * x, 0.23, 0.03), f"{s}_Foot")

arm_data = bpy.data.armatures.new("DogArmature")
arm = bpy.data.objects.new("Dog", arm_data)
bpy.context.scene.collection.objects.link(arm)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode="EDIT")
for name, (h, t, _) in B.items():
    eb = arm_data.edit_bones.new(name)
    eb.head, eb.tail = Vector(h), Vector(t)
for name, (h, _, p) in B.items():
    if p:
        eb = arm_data.edit_bones[name]
        eb.parent = arm_data.edit_bones[p]
        eb.use_connect = (Vector(arm_data.edit_bones[p].tail) - Vector(h)).length < 1e-6
bpy.ops.object.mode_set(mode="OBJECT")

# ── Body: skin-modifier graph → smooth mesh ─────────────────────────────────
verts, radii, edges = [], [], []
def v(p, r):
    verts.append(p); radii.append(r); return len(verts) - 1
def chain(*ids):
    edges.extend(zip(ids[:-1], ids[1:]))

rump  = v((0, 0.27, 0.61), 0.15)
mid   = v((0, 0.02, 0.63), 0.14)
chest = v((0, -0.27, 0.63), 0.165)
neck  = v((0, -0.37, 0.76), 0.10)
headb = v((0, -0.45, 0.86), 0.11)
headf = v((0, -0.58, 0.85), 0.075)
snout = v((0, -0.70, 0.82), 0.05)
tb    = v((0, 0.38, 0.67), 0.045)
tm    = v((0, 0.50, 0.77), 0.035)
tt    = v((0, 0.64, 0.88), 0.02)
chain(tt, tm, tb, rump, mid, chest, neck, headb, headf, snout)
for x in (1, -1):
    fs = v((0.09 * x, -0.28, 0.56), 0.075)
    fe = v((0.11 * x, -0.29, 0.30), 0.045)
    fw = v((0.11 * x, -0.31, 0.08), 0.035)
    fp = v((0.11 * x, -0.37, 0.035), 0.04)
    chain(chest, fs, fe, fw, fp)
    hs = v((0.09 * x, 0.27, 0.56), 0.095)
    hk = v((0.11 * x, 0.22, 0.34), 0.055)
    hh = v((0.11 * x, 0.32, 0.12), 0.035)
    hf = v((0.11 * x, 0.30, 0.045), 0.035)
    ht = v((0.11 * x, 0.235, 0.035), 0.04)
    chain(rump, hs, hk, hh, hf, ht)
    eb_ = v((0.06 * x, -0.45, 0.93), 0.035)
    et = v((0.10 * x, -0.43, 1.03), 0.02)
    chain(headb, eb_, et)

me = bpy.data.meshes.new("DogBody")
me.from_pydata(verts, edges, [])
body = bpy.data.objects.new("DogBody", me)
bpy.context.scene.collection.objects.link(body)
skin = body.modifiers.new("Skin", "SKIN")
for sv, r in zip(me.skin_vertices[0].data, radii):
    sv.radius = (r, r)
me.skin_vertices[0].data[rump].use_root = True
sub = body.modifiers.new("Sub", "SUBSURF"); sub.levels = 2
bpy.context.view_layer.objects.active = body
for m in list(body.modifiers):
    bpy.ops.object.modifier_apply(modifier=m.name)
bpy.ops.object.shade_smooth()

def material(name, rgb, rough=0.7):
    m = bpy.data.materials.new(name); m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*rgb, 1); bsdf.inputs["Roughness"].default_value = rough
    m.diffuse_color = (*rgb, 1); return m
body.data.materials.append(material("Fur", (0.55, 0.33, 0.15)))

# ── Skin weights: automatic (bone heat), envelope as fallback ───────────────
def bind(obj, mode):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True); arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.parent_set(type=mode)
bind(body, "ARMATURE_AUTO")
unweighted = sum(1 for vt in body.data.vertices if not any(g.weight > 1e-4 for g in vt.groups))
print(f"[dog] body verts={len(body.data.vertices)} unweighted after auto={unweighted}")
if unweighted > 0.02 * len(body.data.vertices):
    for vg in list(body.vertex_groups): body.vertex_groups.remove(vg)
    body.modifiers.clear(); body.parent = None
    bind(body, "ARMATURE_ENVELOPE")
    print("[dog] fell back to envelope weights")

# ── Eyes and nose: rigid to the head ────────────────────────────────────────
black = material("Black", (0.02, 0.02, 0.02), 0.3)
def rigid_part(name, loc, r):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=16, ring_count=8)
    o = bpy.context.active_object; o.name = name
    bpy.ops.object.shade_smooth()
    o.data.materials.append(black)
    vg = o.vertex_groups.new(name="Head"); vg.add(range(len(o.data.vertices)), 1.0, "REPLACE")
    o.parent = arm
    o.modifiers.new("Armature", "ARMATURE").object = arm
rigid_part("Nose", (0, -0.715, 0.825), 0.028)
for x in (1, -1):
    rigid_part(f"Eye_{'L' if x > 0 else 'R'}", (0.042 * x, -0.585, 0.885), 0.02)

# ── Export ───────────────────────────────────────────────────────────────────
glb = os.path.join(out_dir, "dog.glb")
bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(filepath=glb, export_format="GLB", export_skins=True,
                          export_animations=False, use_selection=False)
print("[dog] wrote", glb)

# ── Preview render (Workbench) ──────────────────────────────────────────────
scene = bpy.context.scene
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "MATERIAL"
scene.render.resolution_x, scene.render.resolution_y = 800, 600
scene.render.film_transparent = False
world = bpy.data.worlds.new("W"); scene.world = world
cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
scene.collection.objects.link(cam); scene.camera = cam
cam.location = (1.9, -1.7, 1.15)
direction = Vector((0, 0, 0.5)) - cam.location
cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
scene.render.filepath = os.path.join(out_dir, "dog_preview.png")
bpy.ops.render.render(write_still=True)
print("[dog] preview", scene.render.filepath)
