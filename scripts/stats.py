"""stats.py - read the SAVED .blend and write LOWPOLY_CHARACTER_STATS.txt (counts from the evaluated, triangulated meshes).
   blender --factory-startup -b LOWPOLY_CHARACTER.blend --python stats.py -- <out.txt>"""
import sys, bpy, math
out = sys.argv[sys.argv.index("--") + 1]
dg = bpy.context.evaluated_depsgraph_get()
rows, tot = [], [0, 0, 0]
mods = []
for ob in sorted(bpy.data.objects, key=lambda o: (o.users_collection[0].name, o.name)):
    if ob.type != "MESH":
        continue
    mods += [f"{ob.name}:{m.type}" for m in ob.modifiers]
    me = ob.evaluated_get(dg).to_mesh()
    me.calc_loop_triangles()
    t, v, f = len(me.loop_triangles), len(me.vertices), len(me.polygons)
    ob.evaluated_get(dg).to_mesh_clear()
    rows.append((ob.users_collection[0].name, ob.name, t, v, f))
    tot[0] += t; tot[1] += v; tot[2] += f
groups = {}
for c, n, t, v, f in rows:
    groups.setdefault(c, 0); groups[c] += t
# head-profile landmarks straight from the Head mesh (mid-sagittal vertices, x == 0), in cm
head = bpy.data.objects["Head"].data
mid = sorted([(v.co.z * 100, -v.co.y * 100) for v in head.vertices if abs(v.co.x) < 1e-4 and -v.co.y > 0], reverse=True)
L = []
L.append("LOW-POLY ANIME CHARACTER - STATISTICS")
L.append("=" * 52)
L.append(f"Blender version      : {bpy.app.version_string}")
L.append(f"File                 : {bpy.data.filepath}")
L.append("")
L.append(f"TOTAL TRIANGLES      : {tot[0]}   (budget 512 - 1024: {'PASS' if 512 <= tot[0] <= 1024 else 'FAIL'})")
L.append(f"TOTAL VERTICES       : {tot[1]}")
L.append(f"TOTAL FACES (polys)  : {tot[2]}   (quads + tris + 2 n-gons; triangles above = triangulated count)")
L.append(f"Modifiers in file    : {', '.join(mods) if mods else 'none (no subdivision, no mirror, no decimate)'}")
L.append(f"Mesh objects         : {len(rows)}   (every mesh object in the file is counted)")
L.append("")
L.append("Triangles per collection (component group):")
for c, t in groups.items():
    L.append(f"  {c:<12} {t:>5}  ({100.0 * t / tot[0]:.1f}%)")
L.append("")
L.append(f"{'collection':<12} {'object':<16} {'tris':>5} {'verts':>6} {'faces':>6}")
for c, n, t, v, f in rows:
    L.append(f"{c:<12} {n:<16} {t:>5} {v:>6} {f:>6}")
L.append("")
L.append("Head mid-sagittal profile vertices (z up from ground, forward depth from ear axis), cm:")
for z, f in mid:
    L.append(f"  z={z:7.2f}  forward={f:6.2f}")
L.append("")
L.append("Texture              : 1 x 512x512 hand-painted atlas, packed into the .blend, nearest-neighbour sampling")
L.append("Material             : 1 (LowPoly_Atlas: image -> diffuse + 0.42 emission, flat-shaded faces)")
L.append("Modeling approach    : procedural vertex-by-vertex construction in Python (bmesh): 12-vertex head ring")
L.append("                       loops incl. a tilted jaw-border loop, 8-vertex torso rings, 6-vertex limb rings,")
L.append("                       zig-zag pleated skirt, hair = low cap + 24 triangular-section clumps.")
L.append("                       No subdivision, no decimation, no sculpting. Scripts: LowPolyCharacter/scripts/")
open(out, "w").write("\n".join(L) + "\n")
print("\n".join(L[:20]))
