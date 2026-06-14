# -*- coding: utf-8 -*-
"""BIBLY favicon — navy rounded square + gold serif B (legible at 16-48px)."""
from PIL import Image, ImageDraw, ImageFont
import os

NAVY_T = (24, 37, 66)
NAVY_B = (14, 24, 46)
IVORY  = (244, 241, 234)
SER    = "C:/Windows/Fonts/georgiab.ttf"

def make(S):
    ss = S * 4  # supersample for crisp downscale
    img = Image.new("RGBA", (ss, ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # rounded navy bg gradient (vertical)
    rad = int(ss * 0.22)
    bg = Image.new("RGB", (ss, ss), NAVY_T)
    px = bg.load()
    for y in range(ss):
        t = y / (ss - 1)
        r = int(NAVY_T[0] + (NAVY_B[0]-NAVY_T[0])*t)
        g = int(NAVY_T[1] + (NAVY_B[1]-NAVY_T[1])*t)
        b = int(NAVY_T[2] + (NAVY_B[2]-NAVY_T[2])*t)
        for x in range(ss):
            px[x, y] = (r, g, b)
    mask = Image.new("L", (ss, ss), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, ss-1, ss-1], radius=rad, fill=255)
    img.paste(bg, (0, 0), mask)
    d = ImageDraw.Draw(img)
    # gold serif B, centered, large
    f = ImageFont.truetype(SER, int(ss*0.74))
    bb = d.textbbox((0, 0), "B", font=f)
    bw, bh = bb[2]-bb[0], bb[3]-bb[1]
    d.text((ss/2 - bw/2 - bb[0], ss/2 - bh/2 - bb[1]), "B", font=f, fill=IVORY)
    return img.resize((S, S), Image.LANCZOS)

os.makedirs("images", exist_ok=True)
out = []
for S in (16, 32, 48):
    im = make(S); p = f"images/favicon-{S}.png"; im.save(p, "PNG"); out.append((p, os.path.getsize(p)))
# multi-size .ico at root
make(48).save("favicon.ico", sizes=[(16,16),(32,32),(48,48)])
out.append(("favicon.ico", os.path.getsize("favicon.ico")))
with open("_fav_status.txt", "w", encoding="utf-8") as fp:
    for p, s in out: fp.write("%s  %d\n" % (p, s))
