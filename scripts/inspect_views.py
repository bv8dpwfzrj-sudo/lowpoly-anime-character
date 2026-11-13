"""inspect_views.py - fixed inspection cameras for the low-poly character.
   blender --factory-startup -b LOWPOLY_CHARACTER.blend --python inspect_views.py -- <out_prefix> <full|head> <tex|clay|sil> [views]
views (comma list) default: front,side,rear,q34,rq34,above,below   (head mode adds 'under')
Camera orbits the character (which faces -Y). yaw 90 = camera on the character's left (+X side)."""
import sys, os, math
import bpy
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:]
prefix, mode, shade = args[0], args[1], args[2]
VIEWS = {"front": (0, 0), "side": (90, 0), "side_r": (-90, 0), "rear": (180, 0), "q34": (35, 0), "rq34": (145, 0),
         "above": (30, 28), "below": (30, -24), "under": (25, -55), "q34s": (35, 0)}
nohair = len(args) > 4 and args[4] == "nohair"
names = args[3].split(",") if len(args) > 3 and args[3] != "-" else (["front", "side", "rear", "q34", "rq34", "above", "below"] +
                                                    (["under"] if mode == "head" else []))
scene = bpy.context.scene
try:
    scene.render.engine = "BLENDER_EEVEE"
except TypeError:
    scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.eevee.taa_render_samples = 16
scene.view_settings.view_transform = "Standard"
scene.render.film_transparent = False
if mode == "full":
    target, scale, W, H = Vector((0, 0, 0.80)), 1.78, 520, 860
else:
    target, scale, W, H = Vector((0, -0.01, 1.43)), 0.36, 600, 600
scene.render.resolution_x, scene.render.resolution_y = W, H

w = bpy.data.worlds.new("W"); scene.world = w; w.use_nodes = True
bg = w.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.78, 0.80, 0.83, 1); bg.inputs["Strength"].default_value = 0.6

rig = bpy.data.objects.new("Rig", None); scene.collection.objects.link(rig); rig.location = target
def light(name, rot, energy):
    ld = bpy.data.lights.new(name, "SUN"); ld.energy = energy; ld.angle = math.radians(3)
    ob = bpy.data.objects.new(name, ld); scene.collection.objects.link(ob)
    ob.rotation_euler = [math.radians(a) for a in rot]; ob.parent = rig
light("Key", (55, 0, -35), 2.2 if shade == "tex" else 1.4)
light("Fill", (70, 0, 60), 0.7)
cd = bpy.data.cameras.new("Cam"); cd.type = "ORTHO"; cd.ortho_scale = scale
cam = bpy.data.objects.new("Cam", cd); scene.collection.objects.link(cam); cam.parent = rig
cam.location = (0, -6, 0); cam.rotation_euler = (math.radians(90), 0, 0)
scene.camera = cam

if shade in ("clay", "sil"):
    m = bpy.data.materials.new("Clay"); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.0, 0.0, 0.0, 1) if shade == "sil" else (0.55, 0.55, 0.58, 1)
    b.inputs["Roughness"].default_value = 0.9
    if shade == "sil":
        nt.nodes.remove(b)
        e = nt.nodes.new("ShaderNodeEmission"); e.inputs["Color"].default_value = (0, 0, 0, 1)
        nt.links.new(e.outputs[0], nt.nodes["Material Output"].inputs[0])
        bg.inputs["Color"].default_value = (1, 1, 1, 1); bg.inputs["Strength"].default_value = 1.0
    bpy.context.view_layer.material_override = m

if nohair:
    for cn in ("Hair", "Accessories", "Clothing", "Body"):
        bpy.data.collections[cn].hide_render = True
    prefix = prefix + "_nohair"
for nm in names:
    yaw, el = VIEWS[nm]
    rig.rotation_euler = (math.radians(-el), 0, math.radians(yaw))
    bpy.context.view_layer.update()
    scene.render.filepath = f"{prefix}_{shade}_{nm}.png"
    bpy.ops.render.render(write_still=True)
print("INSPECT_DONE")
