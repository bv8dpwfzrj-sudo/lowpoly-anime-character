"""make_turnaround.py <qc_dir> <out.png> - LOWPOLY_CHARACTER_TURNAROUND.png from the inspection renders."""
import sys, os
from PIL import Image, ImageDraw, ImageFont
q, out = sys.argv[1], sys.argv[2]
top = [("Front", "full_tex_front"), ("Side", "full_tex_side"), ("Rear", "full_tex_rear"), ("Three-quarter", "full_tex_q34")]
bot = [("Head front", "head_tex_front"), ("Head side", "head_tex_side"), ("Head 3/4", "head_tex_q34"),
       ("Head 3/4 below", "head_tex_below"), ("Geometry only (no hair, clay)", "head_nohair_clay_side"),
       ("Side silhouette (no hair)", "head_nohair_sil_side")]
try:
    F = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 22)
    f2 = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 17)
except OSError:
    F = f2 = ImageFont.load_default()
FW, FH = 390, 645          # full-body tiles (from 520x860)
HW = HH = 260              # head tiles (from 600x600)
PAD, CAP = 14, 30
W = PAD + 6 * (HW + PAD)
H = 60 + CAP + FH + PAD + CAP + HH + PAD
img = Image.new("RGB", (W, H), (236, 238, 241))
d = ImageDraw.Draw(img)
d.text((PAD, 14), "LOW-POLY ANIME CHARACTER - turnaround (Blender 5.3, Eevee, flat shading)", fill=(30, 32, 40), font=F)
x0 = (W - (4 * FW + 3 * PAD)) // 2
for i, (cap, fn) in enumerate(top):
    x = x0 + i * (FW + PAD); y = 60
    d.text((x + 4, y), cap, fill=(30, 32, 40), font=f2)
    img.paste(Image.open(os.path.join(q, fn + ".png")).convert("RGB").resize((FW, FH), Image.LANCZOS), (x, y + CAP))
y = 60 + CAP + FH + PAD
for i, (cap, fn) in enumerate(bot):
    x = PAD + i * (HW + PAD)
    d.text((x + 4, y), cap, fill=(30, 32, 40), font=f2)
    img.paste(Image.open(os.path.join(q, fn + ".png")).convert("RGB").resize((HW, HH), Image.LANCZOS), (x, y + CAP))
img.save(out)
print(img.size)
