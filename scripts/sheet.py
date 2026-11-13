"""sheet.py <out.png> <scale> <cols> <img1> <img2> ... - tile images with their view name as a caption."""
import sys, os
from PIL import Image, ImageDraw, ImageFont
out, scale, cols = sys.argv[1], float(sys.argv[2]), int(sys.argv[3])
ims = [Image.open(p).convert("RGB") for p in sys.argv[4:]]
w, h = ims[0].size
w2, h2 = int(w * scale), int(h * scale)
rows = (len(ims) + cols - 1) // cols
sh = Image.new("RGB", (w2 * cols, (h2 + 24) * rows), (255, 255, 255))
d = ImageDraw.Draw(sh)
try:
    f = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 16)
except OSError:
    f = ImageFont.load_default()
for i, (im, p) in enumerate(zip(ims, sys.argv[4:])):
    x, y = (i % cols) * w2, (i // cols) * (h2 + 24)
    sh.paste(im.resize((w2, h2), Image.LANCZOS), (x, y + 24))
    d.text((x + 6, y + 3), os.path.basename(p).rsplit(".", 1)[0], fill=(30, 30, 30), font=f)
sh.save(out)
print(sh.size)
