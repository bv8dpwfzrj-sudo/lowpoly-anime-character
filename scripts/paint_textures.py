"""paint_textures.py - hand-painted, pixel-style 512x512 texture atlas for the low-poly character.
   python paint_textures.py <out.png>
Region layout (pixels, origin top-left) - MUST match build_character.py:
  FACE  (0,0)-(256,256)     front projection of the head: x in [-8,8] cm, z in [-7,9]+offset (see FACE_* below)
  HAIR  (256,0)-(512,256)   u = azimuth, v = height
  TOP   (0,256)-(256,384)   torso cylinder: u = azimuth, v = z 127 -> 82
  SKIRT (256,256)-(512,384) skirt cylinder: u = azimuth, v = z 102 -> 72
  LEGS  (0,384)-(128,512)   v = z 87 -> 0 (skin, knee socks)
  ARMS  (128,384)-(256,512) v = z 126 -> 70 (sleeve, cuff, hand)
  MISC  (256,384)-(512,512) 32x32 swatches (see SWATCH)
All drawing is aliased on purpose (nearest-neighbour texture look)."""
import sys, math, random
from PIL import Image, ImageDraw

OUT = sys.argv[1]
random.seed(7)
A = Image.new("RGB", (512, 512), (255, 0, 255))
d = ImageDraw.Draw(A)

# ---------------- palette (original design: navy hair, cream/teal sailor top, red ribbon) -------
SKIN = (246, 220, 204); SKIN_SH = (228, 192, 178); SKIN_SH2 = (214, 172, 160)
HAIR = (52, 58, 96); HAIR_DK = (30, 33, 60); HAIR_HI = (78, 88, 138); HAIR_HI2 = (112, 126, 180)
CREAM = (242, 236, 220); CREAM_SH = (219, 211, 193); CREAM_DK = (196, 186, 168)
TEAL = (44, 98, 104); TEAL_DK = (28, 66, 72); TEAL_HI = (70, 132, 136)
RED = (196, 62, 74); RED_DK = (140, 38, 52)
SOCK = (34, 34, 44); SOCK_HI = (60, 60, 76)
BROWN = (96, 58, 42); BROWN_DK = (60, 36, 28); SOLE = (40, 30, 26)
WHITE = (250, 250, 246); LINE = (40, 30, 40)
IRIS = (40, 150, 140); IRIS_DK = (20, 80, 86); IRIS_HI = (130, 220, 200)
BLUSH = (242, 168, 164); BLUSH_LN = (226, 128, 128); LIP = (150, 70, 74)
GOLD = (236, 190, 70); GOLD_DK = (190, 130, 40)

# ---------------- FACE --------------------------------------------------------------------
FX0, FX1 = -8.0, 8.0      # head-frame x range across the 256 px
FZ0, FZ1 = -7.0, 15.0     # head-frame z range (bottom, top); 22 cm over 256 px -> ~11.6 px/cm
def fp(x, z):
    return (int(round((x - FX0) / (FX1 - FX0) * 255)), int(round((FZ1 - z) / (FZ1 - FZ0) * 255)))
def fbox(x0, z0, x1, z1):
    (a, b), (c, e) = fp(x0, z1), fp(x1, z0)
    return [a, b, c, e]

d.rectangle([0, 0, 255, 255], fill=SKIN)
# hair shadow under the bangs and soft shade on the neck below the jaw (anime cel shading)
d.rectangle(fbox(-8, 12.3, 8, 15), fill=SKIN_SH)
for x0 in range(-8, 8):
    zz = 12.3 - (0.5 if x0 % 2 else 0.0)
    d.polygon([fp(x0, 12.3), fp(x0 + 0.5, zz - 0.6), fp(x0 + 1, 12.3)], fill=SKIN_SH)
d.rectangle(fbox(-8, -7, 8, -1.6), fill=SKIN_SH)
d.polygon([fp(-3.6, -1.6), fp(0, -3.0), fp(3.6, -1.6)], fill=SKIN_SH)

def eye(s):
    """s = +1 character-left side of image? we draw in head-frame x; s mirrors."""
    X = lambda x: s * x
    # sclera (almond-ish, taller than wide - anime)
    d.polygon([fp(X(1.7), 9.3), fp(X(2.2), 10.7), fp(X(3.4), 11.3), fp(X(4.6), 11.0), fp(X(5.1), 9.9),
               fp(X(4.7), 8.3), fp(X(3.4), 7.9), fp(X(2.2), 8.3)], fill=WHITE)
    # iris + pupil + highlights
    a0, a1 = sorted([fp(X(2.45), 0)[0], fp(X(4.35), 0)[0]])
    d.ellipse([a0, fp(0, 11.0)[1], a1, fp(0, 8.0)[1]], fill=IRIS)
    # darker upper iris band
    d.chord([a0, fp(0, 11.0)[1], a1, fp(0, 8.0)[1]], 180, 360, fill=IRIS_DK)
    d.chord([a0 + 3, fp(0, 10.2)[1], a1 - 3, fp(0, 8.1)[1]], 20, 160, fill=IRIS_HI)
    p0, p1 = sorted([fp(X(3.0), 0)[0], fp(X(3.8), 0)[0]])
    d.ellipse([p0, fp(0, 10.1)[1], p1, fp(0, 8.9)[1]], fill=IRIS_DK)
    h0, h1 = sorted([fp(X(2.75), 0)[0], fp(X(3.35), 0)[0]])
    d.ellipse([h0, fp(0, 10.65)[1], h1, fp(0, 10.05)[1]], fill=WHITE)
    g0, g1 = sorted([fp(X(3.85), 0)[0], fp(X(4.15), 0)[0]])
    d.ellipse([g0, fp(0, 8.85)[1], g1, fp(0, 8.55)[1]], fill=WHITE)
    # thick upper lash line with outer flick
    d.polygon([fp(X(1.5), 9.5), fp(X(2.1), 10.9), fp(X(3.4), 11.55), fp(X(4.7), 11.25), fp(X(5.6), 10.6),
               fp(X(5.3), 10.1), fp(X(4.6), 10.75), fp(X(3.4), 11.05), fp(X(2.3), 10.55), fp(X(1.8), 9.4)], fill=LINE)
    d.polygon([fp(X(5.0), 10.4), fp(X(5.9), 10.0), fp(X(5.2), 10.0)], fill=LINE)
    # lower lash: short broken line
    d.line([fp(X(2.4), 8.05), fp(X(3.4), 7.8), fp(X(4.4), 8.0)], fill=LINE, width=2)
    d.line([fp(X(4.6), 8.25), fp(X(4.9), 8.6)], fill=LINE, width=1)
    # brow (thin, slightly raised at the outer end)
    d.line([fp(X(1.9), 12.25), fp(X(3.2), 12.6), fp(X(4.7), 12.45)], fill=HAIR_DK, width=3)
    # blush with hatch lines
    b0, b1 = sorted([fp(X(3.0), 0)[0], fp(X(5.3), 0)[0]])
    d.ellipse([b0, fp(0, 6.9)[1], b1, fp(0, 5.9)[1]], fill=BLUSH)
    for k in range(3):
        xx = 3.5 + k * 0.55
        d.line([fp(X(xx), 6.1), fp(X(xx + 0.35), 6.7)], fill=BLUSH_LN, width=2)
eye(+1); eye(-1)
# nose: tiny shade notch on the camera-left side of the tip + nostril dot
d.polygon([fp(-0.1, 6.6), fp(-0.55, 5.8), fp(-0.05, 5.6)], fill=SKIN_SH2)
d.point(fp(0.35, 5.45), fill=SKIN_SH2)
# mouth: small cat-like smile, lower-lip hint
d.line([fp(-0.95, 4.05), fp(-0.35, 3.8), fp(0, 3.95), fp(0.35, 3.8), fp(0.95, 4.05)], fill=LIP, width=2)
d.line([fp(-0.3, 3.35), fp(0.3, 3.35)], fill=SKIN_SH2, width=2)
# chin: no painted shadow on the chin itself (geometry must carry it); tiny highlight only
d.line([fp(-0.5, 1.6), fp(0.5, 1.6)], fill=(252, 232, 220), width=2)

# ---------------- HAIR (256..512, 0..256) ---------------------------------------------------
HX, HY = 256, 0
for y in range(256):
    t = y / 255.0
    c = tuple(int(HAIR[i] * (1 - t * 0.55) + HAIR_DK[i] * t * 0.55) for i in range(3))
    d.line([HX, HY + y, HX + 255, HY + y], fill=c)
# angular "angel ring" highlights: broken, irregular shards (not a solid band)
xs = 0
while xs < 256:
    w = random.choice((10, 14, 18, 22))
    if random.random() < 0.72:
        x0 = HX + xs; y0 = 40 + random.randrange(-4, 5)
        d.polygon([(x0, y0 + 6), (x0 + w // 2, y0 - 4), (x0 + w, y0 + 6), (x0 + w // 2 + 2, y0 + 20)], fill=HAIR_HI)
        d.polygon([(x0 + w // 2 - 2, y0 + 4), (x0 + w // 2, y0), (x0 + w // 2 + 2, y0 + 4), (x0 + w // 2, y0 + 10)], fill=HAIR_HI2)
    xs += w + random.choice((2, 4, 6))
# strand lines
for k in range(60):
    x = HX + random.randrange(0, 256)
    y0 = random.randrange(70, 200)
    d.line([(x, y0), (x + random.choice((-2, 0, 2)), y0 + random.randrange(20, 50))], fill=HAIR_DK, width=1)
# darker tips band
d.rectangle([HX, 228, HX + 255, 255], fill=HAIR_DK)

# ---------------- TOP / blouse (0..256, 256..384): v = z 127 -> 82 --------------------------
def tz(z):
    return int(256 + (127 - z) / (127 - 82) * 127)
d.rectangle([0, 256, 255, 383], fill=CREAM)
# side/back shading by azimuth (u: 0=back, 0.5=front, 1=back)
# under-bust / side shading as angular wedges (light comes from the front)
for u0 in (0.30, 0.70):
    x = int(u0 * 255)
    d.polygon([(x - 10, tz(112)), (x + 10, tz(112)), (x + 4, tz(98)), (x - 4, tz(98))], fill=CREAM_SH)
d.polygon([(100, tz(108.5)), (156, tz(108.5)), (148, tz(106.5)), (108, tz(106.5))], fill=CREAM_SH)
# fold shapes (angular)
for (u, z0, z1, w) in [(0.42, 112, 99, 6), (0.58, 110, 98, 6), (0.27, 116, 100, 5), (0.73, 116, 100, 5), (0.5, 104, 97, 4)]:
    x = int(u * 255)
    d.polygon([(x - w, tz(z0)), (x + 1, tz(z1)), (x + w // 2, tz(z0 + 3))], fill=CREAM_DK)
# hem: teal band + under-shorts below
d.rectangle([0, tz(97.6), 255, tz(96.0)], fill=TEAL)
d.rectangle([0, tz(96.0), 255, 383], fill=SOCK)
# front placket line
d.line([128, tz(110), 128, tz(97.6)], fill=CREAM_DK, width=2)

# ---------------- SKIRT (256..512, 256..384): v = z 102 -> 72 ------------------------------
def sz(z):
    return int(256 + (102 - z) / 30.0 * 127)
d.rectangle([256, 256, 511, 383], fill=TEAL)
for k in range(16):
    x0 = 256 + k * 16
    d.polygon([(x0, sz(101)), (x0 + 3, sz(101)), (x0 + 6, 383), (x0, 383)], fill=TEAL_DK)
    d.polygon([(x0 + 10, sz(99)), (x0 + 12, sz(99)), (x0 + 14, 383), (x0 + 11, 383)], fill=TEAL_HI)
d.rectangle([256, sz(101.8), 511, sz(100.4)], fill=TEAL_DK)               # waistband
d.rectangle([256, sz(75.4), 511, sz(74.6)], fill=WHITE)                  # sailor hem stripe

# ---------------- LEGS (0..128, 384..512): v = z 87 -> 0 ------------------------------------
def lz(z):
    return int(384 + (87 - z) / 87.0 * 127)
d.rectangle([0, 384, 127, 511], fill=SKIN)
d.rectangle([0, lz(87), 127, lz(72)], fill=SKIN_SH)                     # shadow under the skirt
d.rectangle([0, lz(40), 127, 511], fill=SOCK)
d.rectangle([0, lz(40), 127, lz(38.6)], fill=SOCK_HI)
for k in range(8):                                                      # knee shading on the front
    d.point((60 + k, lz(46)), fill=SKIN_SH)

# ---------------- ARMS (128..256, 384..512): v = z 126 -> 70 -------------------------------
def az(z):
    return int(384 + (126 - z) / 56.0 * 127)
d.rectangle([128, 384, 255, 511], fill=CREAM)
d.rectangle([128, az(126), 255, az(118)], fill=CREAM_SH)                # under-collar shade
d.rectangle([128, az(84.5), 255, az(80.0)], fill=TEAL)                  # cuff
d.rectangle([128, az(83.2), 255, az(82.4)], fill=WHITE)                 # cuff stripe
d.rectangle([128, az(80.0), 255, 511], fill=SKIN)                       # hand
d.rectangle([128, az(73.5), 255, 511], fill=SKIN_SH)                    # fingers a touch darker
for k in range(4):
    x = 150 + k * 22
    d.line([x, az(73.5), x, 511], fill=SKIN_SH2, width=1)               # finger separations

# ---------------- MISC swatches (256..512, 384..512), 32x32 each ----------------------------
SW = {"skin": SKIN, "skin_sh": SKIN_SH, "teal": TEAL, "red": RED, "brown": BROWN, "sole": SOLE,
      "gold": GOLD, "hair_dk": HAIR_DK, "cream": CREAM, "red_dk": RED_DK, "brown_dk": BROWN_DK, "white": WHITE}
for i, (k, c) in enumerate(SW.items()):
    x0, y0 = 256 + (i % 8) * 32, 384 + (i // 8) * 32
    d.rectangle([x0, y0, x0 + 31, y0 + 31], fill=c)
# collar swatch with white stripe (teal + stripe) at slot 12
x0, y0 = 256 + (12 % 8) * 32, 384 + (12 // 8) * 32
d.rectangle([x0, y0, x0 + 31, y0 + 31], fill=TEAL)
d.rectangle([x0, y0 + 24, x0 + 31, y0 + 27], fill=WHITE)
# shoe swatch: brown upper with darker sole band (slot 13)
x0, y0 = 256 + (13 % 8) * 32, 384 + (13 // 8) * 32
d.rectangle([x0, y0, x0 + 31, y0 + 31], fill=BROWN)
d.rectangle([x0, y0 + 24, x0 + 31, y0 + 31], fill=SOLE)
d.rectangle([x0, y0 + 4, x0 + 31, y0 + 6], fill=BROWN_DK)
A.save(OUT)
print("atlas", OUT)
