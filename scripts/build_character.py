"""build_character.py - original low-poly anime character, built vertex-by-vertex (no subdivision, no decimation).
   blender --factory-startup -b --python build_character.py -- <atlas.png> <out.blend>
Units: cm while building, x = character's left->right (+x = character's LEFT side when facing camera? no:
+x is screen-right in the front view), f = forward (face direction), z = up. Blender: (x, -f, z) * 0.01.
Head is modelled in its own frame (chin/menton at z=0, see HEAD_MODELING_GUIDE.md) and placed at HZ."""
import sys, os, math
import bpy, bmesh
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:]
ATLAS = os.path.abspath(args[0])
OUT = os.path.abspath(args[1])
S = 0.01
HK = 1.08           # head scale factor (head frame -> body frame)
HZ = 131.5          # body-frame height of the menton (head z = 0)
TEX = 512.0

# ------------------------------------------------------------------------------------------------
# atlas helpers (must match paint_textures.py)
# ------------------------------------------------------------------------------------------------
def px2uv(px, py):
    return (px / TEX, 1.0 - py / TEX)

SWATCH_ORDER = ["skin", "skin_sh", "teal", "red", "brown", "sole", "gold", "hair_dk", "cream",
                "red_dk", "brown_dk", "white", "collar", "shoe"]
def swatch(name, dy=16, dx=16):
    i = SWATCH_ORDER.index(name)
    return px2uv(256 + (i % 8) * 32 + dx, 384 + (i // 8) * 32 + dy)

def azimuth_u(x, f, cf=0.0):
    a = math.atan2(x, f - cf)                     # 0 = front, +pi/2 = +x
    return (a / (2 * math.pi)) + 0.5              # front -> 0.5, back -> 0 / 1

# ------------------------------------------------------------------------------------------------
# part builder
# ------------------------------------------------------------------------------------------------
ALL_PARTS = []
class Part:
    def __init__(self, name, coll):
        ALL_PARTS.append(self)
        self.name, self.coll = name, coll
        self.v = []            # body-frame cm
        self.f = []            # (idx tuple, uvfunc, ref point or None)

    def add(self, p):
        self.v.append(Vector(p))
        return len(self.v) - 1

    def face(self, idx, uv, ref=None):
        self.f.append((tuple(idx), uv, ref))

    def build(self, mat):
        me = bpy.data.meshes.new(self.name)
        bm = bmesh.new()
        bv = [bm.verts.new((p.x * S, -p.y * S, p.z * S)) for p in self.v]
        bm.verts.ensure_lookup_table()
        uvl = bm.loops.layers.uv.new("UVMap")
        for idx, uvf, ref in self.f:
            pts = [self.v[i] for i in idx]
            # orientation in cm-frame: normal (Newell) must point away from ref
            n = Vector((0, 0, 0))
            for a, b in zip(pts, pts[1:] + pts[:1]):
                n.x += (a.y - b.y) * (a.z + b.z); n.y += (a.z - b.z) * (a.x + b.x); n.z += (a.x - b.x) * (a.y + b.y)
            c = sum(pts, Vector()) / len(pts)
            if ref is not None and n.dot(c - Vector(ref)) < 0:
                idx = tuple(reversed(idx)); pts = list(reversed(pts)); n = -n
            nn = n.normalized() if n.length > 1e-9 else Vector((0, 0, 1))
            uvs = uvf(pts, nn, c)
            # Blender frame mirrors y (= -f): reverse winding so normals stay outward
            idx_b, uvs_b = list(reversed(idx)), list(reversed(uvs))
            try:
                bf = bm.faces.new([bv[i] for i in idx_b])
            except ValueError:
                print("SKIP_FACE", self.name, idx)
                continue
            for loop, uv in zip(bf.loops, uvs_b):
                loop[uvl].uv = uv
            bf.smooth = False
        bm.to_mesh(me)
        bm.free()
        ob = bpy.data.objects.new(self.name, me)
        self.coll.objects.link(ob)
        me.materials.append(mat)
        return ob

# UV functions --------------------------------------------------------------------------------
def uv_const(name):
    return lambda pts, n, c: [swatch(name)] * len(pts)

def uv_face(pts, n, c):
    """front projection for front-facing head faces, skin swatch otherwise."""
    if n.y > 0.35:
        out = []
        for p in pts:
            x, z = p.x / HK, (p.z - HZ) / HK
            out.append(px2uv((x + 8.0) / 16.0 * 255, (15.0 - z) / 22.0 * 255))
        return out
    shade = "skin_sh" if (c.z - HZ) / HK < -0.5 else "skin"
    return [swatch(shade)] * len(pts)

def seam_safe(us):
    """faces straddling the u=0/1 seam: unwrap to the high side and clamp (never average to the front!)."""
    if max(us) - min(us) > 0.5:
        return [min(u if u >= 0.5 else u + 1.0, 0.999) for u in us]
    return us

def uv_cyl(x0, y0, w, h, ztop, zbot, cf=0.0, cx=0.0):
    def f(pts, n, c):
        us = seam_safe([azimuth_u(p.x - cx, p.y, cf) for p in pts])
        return [px2uv(x0 + u * (w - 1), y0 + (ztop - p.z) / (ztop - zbot) * (h - 1)) for u, p in zip(us, pts)]
    return f

def uv_hair(pts, n, c):
    us = seam_safe([azimuth_u(p.x, p.y, -0.6 * HK) for p in pts])
    out = []
    for u, p in zip(us, pts):
        z = (p.z - HZ) / HK
        v = min(max((24.5 - z) / 36.0, 0.01), 0.99)
        out.append(px2uv(256 + u * 255, v * 255))
    return out

def uv_strip(x0, y0, w, h, ztop, zbot):
    def f(pts, n, c):
        return [px2uv(x0 + 8 + (i % 2) * (w - 16), y0 + min(max((ztop - p.z) / (ztop - zbot), 0), 1) * (h - 1))
                for i, p in enumerate(pts)]
    return f

# ------------------------------------------------------------------------------------------------
# collections + material
# ------------------------------------------------------------------------------------------------
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
root = bpy.data.collections.new("LowPolyCharacter")
scene.collection.children.link(root)
C = {}
for n in ("Head", "Hair", "Body", "Clothing", "Accessories"):
    C[n] = bpy.data.collections.new(n)
    root.children.link(C[n])

img = bpy.data.images.load(ATLAS)
img.pack()
mat = bpy.data.materials.new("LowPoly_Atlas")
mat.use_nodes = True
mat.use_backface_culling = False
nt = mat.node_tree
nt.nodes.clear()
o = nt.nodes.new("ShaderNodeOutputMaterial")
tx = nt.nodes.new("ShaderNodeTexImage"); tx.image = img; tx.interpolation = "Closest"; tx.extension = "EXTEND"
dif = nt.nodes.new("ShaderNodeBsdfDiffuse")
em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Strength"].default_value = 0.42
add = nt.nodes.new("ShaderNodeAddShader")
nt.links.new(tx.outputs["Color"], dif.inputs["Color"])
nt.links.new(tx.outputs["Color"], em.inputs["Color"])
nt.links.new(dif.outputs[0], add.inputs[0])
nt.links.new(em.outputs[0], add.inputs[1])
nt.links.new(add.outputs[0], o.inputs["Surface"])

# ------------------------------------------------------------------------------------------------
# HEAD + NECK  (head frame: menton z=0, f forward, ear-canal axis ~ f=0)  - see guide sections 3/5/6
# Each ring = half profile P0 (front centre) .. P6 (back centre); mirrored to 12 vertices.
# Rings are tilted (lower at the front) below the mouth so that one loop (R8) IS the jaw border:
# side plane above it, underside plane below it, neck behind.
# ------------------------------------------------------------------------------------------------
TOP = (0, -0.8, 22.0)
RINGS = [
    ("R1 crown",      [(0, 4.4, 20.8), (2.7, 3.8, 20.9), (4.7, 1.8, 21.0), (5.4, -1.0, 21.0), (4.7, -4.0, 20.9), (2.7, -6.0, 20.7), (0, -6.6, 20.6)]),
    ("R2 forehead",   [(0, 7.0, 17.6), (3.7, 6.2, 17.7), (6.3, 3.4, 17.8), (7.2, -0.8, 17.9), (6.6, -5.0, 17.8), (3.9, -7.8, 17.6), (0, -8.4, 17.5)]),
    ("R3 brow",       [(0, 7.9, 13.0), (3.6, 7.6, 13.0), (6.6, 4.6, 13.0), (7.4, -0.8, 13.0), (7.0, -5.2, 13.0), (4.2, -8.1, 13.0), (0, -8.6, 13.0)]),
    ("R4 eyes",       [(0, 7.7, 9.6), (3.4, 7.0, 9.8), (6.3, 4.9, 9.8), (7.0, 0.0, 9.8), (6.8, -4.8, 9.8), (4.0, -7.7, 9.6), (0, -8.1, 9.6)]),
    ("R5 nose/zyg",   [(0, 8.9, 6.3), (3.0, 7.2, 6.5), (5.8, 4.7, 6.8), (6.5, 0.2, 6.6), (6.2, -4.4, 6.6), (3.8, -7.0, 6.4), (0, -7.4, 6.2)]),
    ("R6 mouth",      [(0, 7.9, 3.8), (2.4, 7.1, 4.0), (4.8, 4.6, 4.6), (5.7, 0.5, 4.8), (5.3, -3.6, 4.9), (3.5, -6.2, 4.6), (0, -6.7, 4.5)]),
    ("R7a sulcus",    [(0, 8.05, 2.6), (2.0, 7.4, 2.85), (4.4, 4.7, 3.6), (5.5, 0.45, 4.15), (5.0, -3.3, 4.25), (3.3, -5.9, 3.9), (0, -6.3, 3.8)]),
    ("R7 chin/gonion",[(0, 8.8, 1.3), (1.7, 8.1, 1.55), (3.9, 5.0, 2.45), (5.3, 0.4, 3.5), (4.7, -3.1, 3.6), (3.1, -5.6, 3.25), (0, -6.0, 3.1)]),
    ("R8 jaw border", [(0, 7.7, 0.0), (1.5, 7.2, 0.2), (3.2, 4.2, 1.1), (4.0, 0.6, 1.9), (4.1, -3.0, 2.6), (3.0, -5.2, 2.5), (0, -5.7, 2.4)]),
    ("N1 throat",     [(0, 2.8, -1.2), (2.0, 2.3, -1.0), (3.4, 0.7, -0.6), (3.8, -1.2, 0.0), (3.4, -3.4, 0.8), (2.2, -4.8, 1.4), (0, -5.2, 1.6)]),
    ("N2 neck base",  [(0, 2.6, -6.5), (2.2, 2.0, -6.5), (3.6, 0.3, -6.5), (4.0, -1.4, -6.5), (3.6, -3.4, -6.5), (2.3, -4.6, -6.5), (0, -5.0, -6.5)]),
]

def full_ring(half):
    """P0, P1..P5 (+x), P6, P5..P1 (-x)"""
    pts = list(half)
    return pts + [(-x, f, z) for (x, f, z) in reversed(half[1:-1])]

def hb(p):            # head frame -> body frame (scaled about the menton)
    return (p[0] * HK, p[1] * HK, p[2] * HK + HZ)

head = Part("Head", C["Head"])
ring_idx = []
top_i = head.add(hb(TOP))
for name, half in RINGS:
    ring_idx.append([head.add(hb(p)) for p in full_ring(half)])
N = 12
r0 = ring_idx[0]
for i in range(N):
    head.face((top_i, r0[i], r0[(i + 1) % N]), uv_face, ref=(0, -0.6, HZ + 18))
for a, b in zip(ring_idx, ring_idx[1:]):
    for i in range(N):
        j = (i + 1) % N
        q = (a[i], a[j], b[j], b[i])
        zc = sum(head.v[k].z for k in q) / 4
        head.face(q, uv_face, ref=(0, -0.8, zc))
# (neck bottom stays open: it sits inside the torso's neck opening)

# ---- head surface lookup (for hair placement) ------------------------------------------------
def ring_poly(z):
    """interpolated planar-ish ring (head frame) at height z, using R1..R6 + TOP."""
    levels = [(22.0, [TOP] * 12)] + [(sum(p[2] for p in h) / 7.0, full_ring(h)) for _, h in RINGS[:6]]
    for (za, ra), (zb, rb) in zip(levels, levels[1:]):
        if zb <= z <= za:
            t = (za - z) / (za - zb)
            return [tuple(a[k] + (b[k] - a[k]) * t for k in range(3)) for a, b in zip(ra, rb)]
    return full_ring(RINGS[5][1]) if z < levels[-1][0] else [TOP] * 12

def surf(theta_deg, z, off=0.0, cf=-0.6):
    """point on the head surface at azimuth theta (0 = front, +90 = +x), height z, pushed out by off."""
    poly = ring_poly(z)
    th = math.radians(theta_deg)
    d = (math.sin(th), math.cos(th))
    best = None
    for a, b in zip(poly, poly[1:] + poly[:1]):
        ax, af = a[0], a[1] - cf; bx, bf = b[0], b[1] - cf
        ex, ef = bx - ax, bf - af
        den = d[0] * ef - d[1] * ex
        if abs(den) < 1e-9:
            continue
        t = (ax * ef - af * ex) / den
        s = (ax * d[1] - af * d[0]) / den
        if t > 0 and -1e-6 <= s <= 1 + 1e-6:
            best = t if best is None else max(best, t)
    r = (best or 0.0) + off
    return (d[0] * r, cf + d[1] * r, z)

# ------------------------------------------------------------------------------------------------
# HAIR: low-poly cap + individually shaped clumps (triangular cross-section blades)
# ------------------------------------------------------------------------------------------------
hair = Part("Hair", C["Hair"])
HC = (0, -0.6)

def push(p, off, cf=-0.6, cz=11.0):
    """radially (from the head centre) push a head-frame point out by off cm."""
    v = Vector((p[0], p[1] - cf, p[2] - cz)).normalized()
    return (p[0] + v.x * off, p[1] + v.y * off, p[2] + v.z * off)

# cap: crown pole + R1..R3 pushed out 0.9 cm + a tuck ring on the skin just below R3
def ring_th(p):
    return math.degrees(math.atan2(p[0], p[1] + 0.6))
cap_rings = [[hb(push(p, 0.9)) for p in full_ring(RINGS[k][1])] for k in range(2)]
r3, tk = [], []
for p in full_ring(RINGS[2][1]):
    th = ring_th(p)
    if abs(th) < 60:      # front: hairline, bangs hang from here
        r3.append(hb(surf(th, 17.0, 0.9))); tk.append(hb(surf(th, 16.2, 0.05)))
    else:                 # sides/back: down to the temples, then tucked onto the skin
        r3.append(hb(push(p, 0.9))); tk.append(hb(surf(th, 12.2, 0.05)))
cap_rings += [r3, tk]
ci = [[hair.add(p) for p in r] for r in cap_rings]
ct = hair.add(hb((0, -0.8, 23.1)))
for i in range(N):
    hair.face((ct, ci[0][i], ci[0][(i + 1) % N]), uv_hair, ref=(0, -0.6, HZ + 18))
for a, b in zip(ci, ci[1:]):
    for i in range(N):
        j = (i + 1) % N
        hair.face((a[i], a[j], b[j], b[i]), uv_hair, ref=(0, -0.6, HZ + 15))

def clump(path, widths, thick, normals):
    """path: list of head-frame points (base ... tip); widths per section (tip width ignored);
    normals: outward direction per section. Triangular cross-section: L, R (inner edge, against head) + ridge."""
    secs, cents = [], []
    for k, p in enumerate(path[:-1]):
        nxt = Vector(path[k + 1]); cur = Vector(p)
        prv = Vector(path[k - 1]) if k > 0 else cur
        tdir = (nxt - prv if k > 0 else nxt - cur).normalized()
        n = Vector(normals[k]).normalized()
        n = (n - tdir * n.dot(tdir)).normalized()
        side = tdir.cross(n).normalized()
        w = widths[k] / 2.0
        L = cur - side * w; R = cur + side * w; T = cur + n * thick[k]
        secs.append([hair.add(hb(L)), hair.add(hb(R)), hair.add(hb(T))])
        cents.append((L + R + T) / 3)
    tip = hair.add(hb(path[-1]))
    for k in range(len(secs) - 1):
        a, b = secs[k], secs[k + 1]
        ref = hb(tuple((cents[k] + cents[k + 1]) / 2))
        for (i0, i1) in ((0, 1), (1, 2), (2, 0)):
            hair.face((a[i0], a[i1], b[i1], b[i0]), uv_hair, ref=ref)
    last = secs[-1]
    ref = hb(tuple(cents[-1] * 0.7 + Vector(path[-1]) * 0.3))
    for (i0, i1) in ((0, 1), (1, 2), (2, 0)):
        hair.face((last[i0], last[i1], tip), uv_hair, ref=ref)

def radial(theta, up=0.0):
    th = math.radians(theta)
    return (math.sin(th), math.cos(th), up)

# bangs: 7 clumps from the hairline, varied lengths (centre short, side framing longer)
for th, zt, w, dth in [(0, 10.9, 4.0, 0), (16, 10.2, 3.8, 4), (-16, 10.4, 3.8, -4), (32, 11.2, 3.6, 5),
                       (-32, 11.0, 3.6, -5), (48, 8.6, 3.6, 8), (-48, 8.8, 3.6, -8)]:
    base = surf(th, 18.6, 0.4)
    mid = surf(th + dth * 0.5, (18.6 + zt) / 2 + 0.4, 1.5)
    tip = surf(th + dth, zt, 0.8)
    clump([base, mid, tip], [w, w * 0.85], [1.1, 0.9], [radial(th, 0.6), radial(th, 0.1)])

# side hair over the ears (stops above the jaw angle so the jawline stays visible)
for th, zt, w, off_t in [(72, 5.0, 4.2, 2.2), (-72, 5.0, 4.2, 2.2), (100, 3.0, 4.8, 2.8), (-100, 3.0, 4.8, 2.8)]:
    s = 1 if th > 0 else -1
    base = surf(th, 16.5, 0.4)
    mid = surf(th + s * 3, 10.5, 2.2)
    tip = surf(th + s * 8, max(zt, 4.6), off_t)
    tip = (tip[0], tip[1], zt)
    clump([base, mid, tip], [w, w * 0.8], [1.0, 0.9], [radial(th), radial(th)])

# long front side-locks: in front of the ears, outside the jaw, ending on the chest
for s in (1, -1):
    base = surf(s * 60, 15.0, 0.3)
    m1 = surf(s * 64, 9.5, 2.0)
    m2 = (s * 7.8, 3.4, 1.2)          # 2.5+ cm outside the jaw line at this height
    tip = (s * 8.2, 5.4, -10.0)
    clump([base, m1, m2, tip], [3.4, 3.2, 2.4], [1.0, 1.0, 0.8], [radial(s * 60), radial(s * 66), radial(s * 80)])

# back: bob-length clumps flaring slightly at the nape
for th in (115, 140, 160, 180, 200, 220, 245):
    base = surf(th, 18.0, 0.4)
    mid = surf(th, 10.0, 2.0)
    tipb = surf(th + (8 if th < 180 else -8 if th > 180 else 0), 4.8, 3.6)
    tip = (tipb[0], tipb[1], 2.4 + 0.8 * math.cos(math.radians(th * 3)))
    clump([base, mid, tip], [5.6, 4.6], [1.2, 1.1], [radial(th, 0.4), radial(th)])

# crown spikes (silhouette) + ahoge
for th, h in ((140, 1.6), (180, 2.4), (220, 1.6)):
    base = surf(th, 20.2, 0.6)
    tip = surf(th, 18.0, 4.6)
    tip = (tip[0], tip[1], 19.4 + h * 0.5)
    clump([base, tip], [4.2], [1.1], [radial(th, 0.8)])
clump([(0, -0.4, 22.6), (0, 1.6, 25.0), (0, 4.0, 25.2)], [1.4, 1.0], [0.5, 0.4], [(0, 0.3, 1), (0, 0, 1)])

# ------------------------------------------------------------------------------------------------
# TORSO (8-vert rings) - blouse + pelvis, closed at the crotch
# ------------------------------------------------------------------------------------------------
TORSO = [
    (126.6, [(0, 2.0), (2.4, 1.6), (3.4, -1.2), (2.4, -3.8), (0, -4.4)]),     # inside the neck
    (123.5, [(0, 5.8), (6.5, 4.6), (14.5, -0.6), (6.5, -5.4), (0, -6.0)]),    # shoulders / trapezius
    (114.0, [(0, 8.6), (7.2, 7.8), (12.0, 0.0), (7.4, -6.4), (0, -6.6)]),     # chest
    (106.0, [(0, 6.6), (6.6, 6.0), (10.6, -0.2), (6.8, -5.6), (0, -6.0)]),    # ribs
    (100.0, [(0, 5.4), (6.0, 4.8), (9.6, -0.3), (6.0, -5.0), (0, -5.6)]),     # waist
    (91.0,  [(0, 6.4), (8.0, 5.6), (13.0, -0.6), (8.4, -6.8), (0, -7.6)]),    # hips
    (83.0,  [(0, 4.6), (6.0, 4.0), (10.5, -0.6), (6.2, -5.6), (0, -6.0)]),    # crotch
]
def ring8(z, half):
    pts = [(x, f, z) for (x, f) in half]
    return pts + [(-x, f, z) for (x, f, _) in reversed(pts[1:-1])]

torso = Part("Torso_Blouse", C["Clothing"])
tr = [[torso.add(p) for p in ring8(z, h)] for z, h in TORSO]
uv_top = uv_cyl(0, 256, 256, 128, 127, 82, cf=0.0)
for a, b in zip(tr, tr[1:]):
    for i in range(8):
        j = (i + 1) % 8
        zc = (torso.v[a[i]].z + torso.v[b[i]].z) / 2
        torso.face((a[i], a[j], b[j], b[i]), uv_top, ref=(0, -0.5, zc))
bot = tr[-1]
torso.face(tuple(reversed(bot)), uv_const("hair_dk"), ref=(0, -0.5, 90))

def torso_surf(theta, z, off=0.0):
    zs = [t[0] for t in TORSO]
    for k in range(len(TORSO) - 1):
        if zs[k + 1] <= z <= zs[k]:
            t = (zs[k] - z) / (zs[k] - zs[k + 1])
            a, b = ring8(zs[k], TORSO[k][1]), ring8(zs[k + 1], TORSO[k + 1][1])
            poly = [(pa[0] + (pb[0] - pa[0]) * t, pa[1] + (pb[1] - pa[1]) * t) for pa, pb in zip(a, b)]
            break
    th = math.radians(theta); d = (math.sin(th), math.cos(th)); cf = -0.5
    best = 0
    for a, b in zip(poly, poly[1:] + poly[:1]):
        ax, af = a[0], a[1] - cf; bx, bf = b[0], b[1] - cf
        ex, ef = bx - ax, bf - af
        den = d[0] * ef - d[1] * ex
        if abs(den) < 1e-9:
            continue
        tt = (ax * ef - af * ex) / den; s = (ax * d[1] - af * d[0]) / den
        if tt > 0 and -1e-6 <= s <= 1 + 1e-6:
            best = max(best, tt)
    r = best + off
    return (d[0] * r, cf + d[1] * r, z)

# ------------------------------------------------------------------------------------------------
# SAILOR COLLAR + RIBBON (accessories / clothing detail)
# ------------------------------------------------------------------------------------------------
col = Part("Sailor_Collar", C["Clothing"])
def cuv_in(pts, n, c):
    return [swatch("collar", dy=(5 if (p.z > 124.0 or (abs(p.x) < 0.1 and p.z > 116)) else 26)) for p in pts]
iF = {s: col.add(torso_surf(s * 28, 125.0, 0.6)) for s in (1, -1)}
iS = {s: col.add(torso_surf(s * 90, 124.8, 0.6)) for s in (1, -1)}
iB = col.add(torso_surf(180, 124.8, 0.7))
oV = {s: col.add(torso_surf(s * 4, 114.5, 1.0)) for s in (1, -1)}
oSF = {s: col.add(torso_surf(s * 52, 120.5, 1.0)) for s in (1, -1)}
oSB = {s: col.add(torso_surf(s * 122, 120.5, 1.0)) for s in (1, -1)}
oC = {s: col.add(torso_surf(s * 138, 110.5, 1.1)) for s in (1, -1)}
oB = col.add(torso_surf(180, 110.5, 1.1))
mB = col.add(torso_surf(180, 117.5, 1.2))
for s in (1, -1):
    for tri in ((iF[s], oV[s], oSF[s]), (iF[s], oSF[s], iS[s]), (iS[s], oSF[s], oSB[s]),
                (iS[s], oSB[s], iB), (iB, oSB[s], mB), (oSB[s], oC[s], mB), (mB, oC[s], oB)):
        zc = sum(col.v[k].z for k in tri) / 3
        col.face(tri, cuv_in, ref=(0, -0.5, zc))

rib = Part("Ribbon", C["Accessories"])
K = Vector(torso_surf(0, 115.2, 1.1))
k0 = rib.add(K)
for s in (1, -1):
    a = rib.add(K + Vector((s * 3.4, 0.5, 1.6))); b = rib.add(K + Vector((s * 3.0, 0.3, -1.5)))
    rib.face((k0, a, b), uv_const("red"), ref=(0, -0.5, 115))
    c = rib.add(K + Vector((s * 1.9, 0.6, -5.8))); e = rib.add(K + Vector((s * 0.5, 0.3, -5.0)))
    rib.face((k0, c, e), uv_const("red_dk"), ref=(0, -0.5, 113))

# ------------------------------------------------------------------------------------------------
# SKIRT: 8-vert waistband -> 16-vert zig-zag hem (pleats in geometry + texture)
# ------------------------------------------------------------------------------------------------
sk = Part("Skirt", C["Clothing"])
W = [sk.add(p) for p in ring8(101.5, [(0, 6.3), (6.7, 5.6), (10.7, -0.4), (6.9, -5.9), (0, -6.5)])]
hem = []
for k in range(16):
    a = 2 * math.pi * k / 16
    r = 1.0 if k % 2 == 0 else 0.9
    hem.append(sk.add((math.sin(a) * 18.5 * r, -0.6 + math.cos(a) * 13.5 * r, 73.5 + (0.6 if k % 2 else 0))))
uv_sk = uv_cyl(256, 256, 256, 128, 102, 72, cf=-0.5)
# waist ring has 8 verts ordered front, +x..., hem 16 ordered by angle from front toward +x
for i in range(8):
    j = (i + 1) % 8
    h0, h1, h2 = hem[2 * i], hem[2 * i + 1], hem[(2 * i + 2) % 16]
    sk.face((W[i], h0, h1), uv_sk, ref=(0, -0.5, 88))
    sk.face((W[i], h1, W[j]), uv_sk, ref=(0, -0.5, 88))
    sk.face((W[j], h1, h2), uv_sk, ref=(0, -0.5, 88))

# ------------------------------------------------------------------------------------------------
# ARMS (6-vert rings along the bone) + HANDS
# ------------------------------------------------------------------------------------------------
def frame(a):
    a = Vector(a).normalized()
    u = a.cross(Vector((0, 1, 0)))
    if u.length < 1e-6:
        u = a.cross(Vector((1, 0, 0)))
    u.normalize()
    v = a.cross(u).normalized()
    return u, v

def ring_around(part, c, axis, r, n=6, squash=(1.0, 1.0), rot=0.0):
    u, v = frame(axis)
    return [part.add(tuple(Vector(c) + (u * math.cos(2 * math.pi * k / n + rot) * squash[0]
                                        + v * math.sin(2 * math.pi * k / n + rot) * squash[1]) * r)) for k in range(n)]

def tube(part, rings, centres, uvf):
    for a, b, ca, cb in zip(rings, rings[1:], centres, centres[1:]):
        n = len(a)
        for i in range(n):
            j = (i + 1) % n
            part.face((a[i], a[j], b[j], b[i]), uvf, ref=tuple((Vector(ca) + Vector(cb)) / 2))

uv_arm = uv_cyl(128, 384, 128, 128, 126, 70)
for s, nm in ((1, "Arm_L"), (-1, "Arm_R")):
    arm = Part(nm, C["Body"])
    Sh, El, Wr = (s * 14.8, -0.6, 120.8), (s * 17.4, -1.2, 101.5), (s * 19.4, 0.2, 83.0)
    pole = arm.add((s * 13.4, -0.6, 124.4))
    a1 = ring_around(arm, Sh, Vector(El) - Vector(Sh), 3.9)
    a2 = ring_around(arm, El, Vector(Wr) - Vector(El), 3.2)
    a3 = ring_around(arm, Wr, Vector(Wr) - Vector(El), 4.3)            # bell cuff (open)
    for i in range(6):
        arm.face((pole, a1[i], a1[(i + 1) % 6]), uv_arm, ref=Sh)
    tube(arm, [a1, a2, a3], [Sh, El, Wr], uv_arm)
    # hand: wrist ring (inside cuff) -> flattened palm ring -> fingertip pole; plus a thumb blade
    H0, H1, H2 = (s * 19.7, 0.2, 84.5), (s * 20.3, 0.6, 77.0), (s * 20.5, 1.0, 71.0)
    h0 = ring_around(arm, H0, Vector(H1) - Vector(H0), 1.5, n=5)
    h1 = ring_around(arm, H1, Vector(H2) - Vector(H1), 1.0, n=5, squash=(0.8, 2.1))
    tube(arm, [h0, h1], [H0, H1], uv_arm)
    tipi = arm.add(H2)
    for i in range(5):
        arm.face((h1[i], h1[(i + 1) % 5], tipi), uv_arm, ref=H1)
    # thumb: small tetrahedron on the front of the palm (3 visible tris)
    t0 = arm.add((s * 19.6, 1.6, 80.4)); t1 = arm.add((s * 21.0, 1.6, 79.8)); t2 = arm.add((s * 20.2, 1.0, 77.6))
    t3 = arm.add((s * 20.1, 3.3, 75.8))
    tc = (s * 20.2, 1.9, 78.4)
    for tri in ((t0, t1, t3), (t1, t2, t3), (t2, t0, t3)):
        arm.face(tri, uv_arm, ref=tc)

# ------------------------------------------------------------------------------------------------
# LEGS (6-vert rings) + SHOES
# ------------------------------------------------------------------------------------------------
uv_leg = uv_strip(0, 384, 128, 128, 87, 0)
def shoe_uv(pts, n, c):
    return [swatch("shoe", dy=(3 if p.z > 4 else 29)) for p in pts]
for s, nm in ((1, "L"), (-1, "R")):
    leg = Part("Leg_" + nm, C["Body"])
    P = [(s * 6.0, -0.4, 86.0), (s * 5.2, 0.6, 46.0), (s * 5.0, -0.8, 30.0), (s * 4.8, -0.4, 10.0)]
    R = [6.6, 4.2, 4.5, 2.6]
    rings = []
    for k, (c, r) in enumerate(zip(P, R)):
        ax = Vector(P[min(k + 1, 3)]) - Vector(P[max(k - 1, 0)])
        rings.append(ring_around(leg, c, ax, r, rot=math.pi / 6))
    tube(leg, rings, P, uv_leg)
    shoe = Part("Shoe_" + nm, C["Clothing"])
    cx = s * 4.8
    top = [shoe.add(p) for p in [(cx, 3.4, 9.6), (cx + s * 2.9, 1.4, 10.6), (cx + s * 2.8, -1.6, 11.2),
                                 (cx, -3.4, 11.6), (cx - s * 2.8, -1.6, 11.2), (cx - s * 2.9, 1.4, 10.6)]]
    sole = [shoe.add(p) for p in [(cx + s * 0.2, 11.2, 0.6), (cx + s * 3.3, 5.0, 0.3), (cx + s * 3.0, -2.4, 0.3),
                                  (cx, -4.4, 0.3), (cx - s * 3.0, -2.4, 0.3), (cx - s * 3.0, 5.0, 0.3)]]
    for i in range(6):
        j = (i + 1) % 6
        shoe.face((top[i], top[j], sole[j], sole[i]), shoe_uv, ref=(cx, 2.0, 4.0))
    shoe.face(tuple(sole), shoe_uv, ref=(cx, 2.0, 5.0))

# ------------------------------------------------------------------------------------------------
# HAIR CLIP (accessory)
# ------------------------------------------------------------------------------------------------
clip = Part("Hair_Clip", C["Accessories"])
cc = Vector(surf(-30, 15.6, 2.5))
cn = Vector(radial(-30, 0.2)).normalized()
up = Vector((0, 0, 1)); sd = up.cross(cn).normalized()
pts = [clip.add(hb(tuple(cc + up * 1.1))), clip.add(hb(tuple(cc + sd * 0.7))),
       clip.add(hb(tuple(cc - up * 1.1))), clip.add(hb(tuple(cc - sd * 0.7)))]
apex = clip.add(hb(tuple(cc + cn * 0.5)))
for i in range(4):
    clip.face((pts[i], pts[(i + 1) % 4], apex), uv_const("gold"), ref=hb(tuple(cc - cn * 1.0)))

# ------------------------------------------------------------------------------------------------
# build objects
# ------------------------------------------------------------------------------------------------
objs = [p.build(mat) for p in ALL_PARTS]

# stats
tot_t = tot_v = tot_f = 0
rows = []
for ob in sorted(objs, key=lambda o: o.name):
    me = ob.data
    me.calc_loop_triangles()
    t, v, f = len(me.loop_triangles), len(me.vertices), len(me.polygons)
    tot_t += t; tot_v += v; tot_f += f
    rows.append((ob.users_collection[0].name, ob.name, t, v, f))
for r in rows:
    print("PART", *r)
print("TOTAL_TRIS", tot_t, "VERTS", tot_v, "FACES", tot_f)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SAVED", OUT)
