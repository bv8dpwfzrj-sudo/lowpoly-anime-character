"""render_turntable.py - 360-degree turntable of the character (the MODEL rotates; camera + lights fixed).
   blender --factory-startup -b LOWPOLY_CHARACTER.blend --python render_turntable.py -- <out_dir> <full|head> <frames> <w> <h>"""
import sys, os, math
import bpy
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]
out, mode, n, W, H = a[0], a[1], int(a[2]), int(a[3]), int(a[4])
scene = bpy.context.scene
try:
    scene.render.engine = "BLENDER_EEVEE"
except TypeError:
    scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.eevee.taa_render_samples = 16
scene.view_settings.view_transform = "Standard"
scene.render.resolution_x, scene.render.resolution_y = W, H
w = bpy.data.worlds.new("W"); scene.world = w; w.use_nodes = True
bg = w.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.80, 0.82, 0.85, 1); bg.inputs["Strength"].default_value = 0.6
for nm, rot, e in (("Key", (55, 0, -35), 2.2), ("Fill", (70, 0, 60), 0.7)):
    ld = bpy.data.lights.new(nm, "SUN"); ld.energy = e; ld.angle = math.radians(3)
    ob = bpy.data.objects.new(nm, ld); scene.collection.objects.link(ob)
    ob.rotation_euler = [math.radians(v) for v in rot]
piv = bpy.data.objects.new("Turntable", None); scene.collection.objects.link(piv)
for ob in bpy.data.collections["LowPolyCharacter"].all_objects:
    if ob.parent is None:
        ob.parent = piv
target, scale = (Vector((0, 0, 0.80)), 1.80) if mode == "full" else (Vector((0, -0.01, 1.43)), 0.36)
cd = bpy.data.cameras.new("Cam"); cd.type = "ORTHO"; cd.ortho_scale = scale
cam = bpy.data.objects.new("Cam", cd); scene.collection.objects.link(cam)
cam.location = target + Vector((0, -6, 0)); cam.rotation_euler = (math.radians(90), 0, 0)
scene.camera = cam
os.makedirs(out, exist_ok=True)
for f in range(n):
    piv.rotation_euler = (0, 0, math.radians(-360.0 * f / n))     # frame n == frame 0: seamless
    bpy.context.view_layer.update()
    scene.render.filepath = os.path.join(out, f"f_{f:03d}.png")
    bpy.ops.render.render(write_still=True)
print("TT_DONE", out)
