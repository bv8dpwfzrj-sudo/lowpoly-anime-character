"""make_gif.py <frames_dir> <out.gif> <tri_count> - full-body + head close-up turntables side by side."""
import sys, os, glob
from PIL import Image, ImageDraw, ImageFont
root, out, tris = sys.argv[1], sys.argv[2], sys.argv[3]
full = sorted(glob.glob(os.path.join(root, "full", "f_*.png")))
head = sorted(glob.glob(os.path.join(root, "head", "f_*.png")))
n = min(len(full), len(head))
FW, FH = Image.open(full[0]).size
HW, HH = Image.open(head[0]).size
PAD = 12
W, H = PAD * 3 + FW + HW, PAD * 2 + FH
try:
    F = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 22)
    f2 = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 17)
except OSError:
    F = f2 = ImageFont.load_default()
bg = Image.new("RGB", (W, H), (236, 238, 241))
d = ImageDraw.Draw(bg)
tx, ty = PAD * 2 + FW, PAD * 2 + HH + 18
lines = [("Low-poly anime character", F), ("original design", f2), ("", f2),
         (f"{tris} triangles total (budget 512-1024)", f2), ("flat shading, 512 px hand-painted atlas", f2),
         ("hair: cap + 24 shaped clumps", f2), ("head: 12-vertex ring loops,", f2),
         ("jaw border loop = chin/jaw edge", f2), ("", f2), ("Full 360-degree turntable", f2)]
for t, f in lines:
    d.text((tx, ty), t, fill=(35, 38, 48), font=f)
    ty += 30 if f is F else 24
d.text((PAD * 2 + FW + 4, PAD - 2 + HH + 2), "head close-up", fill=(90, 94, 104), font=f2)
frames = []
for i in range(n):
    c = bg.copy()
    c.paste(Image.open(full[i]).convert("RGB"), (PAD, PAD))
    c.paste(Image.open(head[i]).convert("RGB"), (PAD * 2 + FW, PAD))
    frames.append(c)
picks = list(range(0, n, max(1, n // 8)))[:8]
sample = Image.new("RGB", (W, H * len(picks)))
for k, j in enumerate(picks):
    sample.paste(frames[j], (0, k * H))
pal = sample.quantize(colors=256, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE)
q = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
q[0].save(out, save_all=True, append_images=q[1:], duration=50, loop=0, optimize=False, disposal=1)
print("wrote", out, n, "frames", (W, H), round(os.path.getsize(out) / 1e6, 2), "MB")
