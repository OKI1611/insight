# -*- coding: utf-8 -*-
"""Refined OG share card for BIBLY (1200x630)."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math, os

W, H = 1200, 630
CX = W // 2

# ---- palette ----
TOP    = (16, 27, 52)     # deep navy top
BOT    = (8, 16, 32)      # darker bottom
GLOW   = (44, 62, 104)    # warm center glow
GOLD   = (216, 194, 138)  # refined muted gold
GOLD_BR= (233, 214, 166)  # brighter gold accent
IVORY  = (244, 241, 234)  # near-white warm
MUTED  = (150, 168, 198)  # cool blue-grey
FRAME  = (198, 170, 110)  # frame gold

# ---- 1) vertical gradient base ----
base = Image.new("RGB", (W, H), TOP)
px = base.load()
for y in range(H):
    t = y / (H - 1)
    # ease towards bottom
    te = t * t * (3 - 2 * t)
    r = int(TOP[0] + (BOT[0] - TOP[0]) * te)
    g = int(TOP[1] + (BOT[1] - TOP[1]) * te)
    b = int(TOP[2] + (BOT[2] - TOP[2]) * te)
    for x in range(W):
        px[x, y] = (r, g, b)

# ---- 2) soft radial glow (center, slightly upper) ----
glow_mask = Image.new("L", (W, H), 0)
gd = ImageDraw.Draw(glow_mask)
gd.ellipse([CX - 430, 150 - 250, CX + 430, 150 + 470], fill=255)
glow_mask = glow_mask.filter(ImageFilter.GaussianBlur(130))
glow_layer = Image.new("RGB", (W, H), GLOW)
base = Image.composite(glow_layer, base, glow_mask.point(lambda v: int(v * 0.55)))

# ---- 3) vignette (darken edges) ----
vig = Image.new("L", (W, H), 0)
vd = ImageDraw.Draw(vig)
vd.ellipse([-150, -120, W + 150, H + 120], fill=255)
vig = vig.filter(ImageFilter.GaussianBlur(160))
dark = Image.new("RGB", (W, H), (4, 9, 20))
base = Image.composite(base, dark, vig)

img = base.convert("RGB")
d = ImageDraw.Draw(img)

# ---- fonts ----
def F(path, size):
    return ImageFont.truetype(path, size)
SER = "C:/Windows/Fonts/georgiab.ttf"   # serif for wordmark
KB  = "C:/Windows/Fonts/malgunbd.ttf"   # korean bold
KR  = "C:/Windows/Fonts/malgun.ttf"     # korean regular

f_bibly = F(SER, 138)
f_sub   = F(KB, 40)
f_eye   = F(KR, 26)
f_tag   = F(KB, 60)
f_foot  = F(KR, 29)

def text_center(draw, cy, s, font, fill, ls=0):
    """draw horizontally-centered text with optional letter spacing; return (top,bottom)."""
    if ls == 0:
        bb = draw.textbbox((0, 0), s, font=font)
        w = bb[2] - bb[0]
        draw.text((CX - w / 2 - bb[0], cy), s, font=font, fill=fill)
        return cy + bb[1], cy + bb[3]
    # letter spaced
    widths = []
    for ch in s:
        bb = draw.textbbox((0, 0), ch, font=font)
        widths.append(bb[2] - bb[0])
    total = sum(widths) + ls * (len(s) - 1)
    x = CX - total / 2
    top = 99999; bot = -99999
    for ch, w in zip(s, widths):
        bb = draw.textbbox((0, 0), ch, font=font)
        draw.text((x - bb[0], cy), ch, font=font, fill=fill)
        top = min(top, cy + bb[1]); bot = max(bot, cy + bb[3])
        x += w + ls
    return top, bot

# ---- 4) elegant inset frame ----
m = 34
d.rectangle([m, m, W - m, H - m], outline=FRAME, width=2)
# inner hairline
d.rectangle([m + 7, m + 7, W - m - 7, H - m - 7], outline=(FRAME[0], FRAME[1], FRAME[2]), width=1)
# corner accents (small gold ticks)
for (ax, ay) in [(m, m), (W - m, m), (m, H - m), (W - m, H - m)]:
    pass

# ---- 5) open-book emblem (monoline gold) centered near top ----
ebx, eby = CX, 132          # emblem center
hw = 60                      # half width
# spine
d.line([(ebx, eby - 16), (ebx, eby + 14)], fill=GOLD, width=3)
# left page outline
d.line([(ebx, eby + 14), (ebx - hw, eby + 2)], fill=GOLD, width=3)     # bottom edge
d.line([(ebx - hw, eby + 2), (ebx - hw + 4, eby - 18)], fill=GOLD, width=3)  # outer edge
d.line([(ebx - hw + 4, eby - 18), (ebx, eby - 16)], fill=GOLD, width=3)      # top edge
# right page outline (mirror)
d.line([(ebx, eby + 14), (ebx + hw, eby + 2)], fill=GOLD, width=3)
d.line([(ebx + hw, eby + 2), (ebx + hw - 4, eby - 18)], fill=GOLD, width=3)
d.line([(ebx + hw - 4, eby - 18), (ebx, eby - 16)], fill=GOLD, width=3)
# subtle page lines
for i, dy in enumerate((-6, 2)):
    d.line([(ebx - hw + 16, eby + dy), (ebx - 10, eby + dy - 2)], fill=(GOLD[0], GOLD[1], GOLD[2]), width=1)
    d.line([(ebx + 10, eby + dy - 2), (ebx + hw - 16, eby + dy)], fill=(GOLD[0], GOLD[1], GOLD[2]), width=1)

# ---- 6) eyebrow ----
text_center(d, 174, "유튜브 「오광일의 인사이트 브리핑」 공식 강의 플랫폼", f_eye, MUTED, ls=2)

# ---- 7) BIBLY wordmark (serif, wide tracking) ----
text_center(d, 222, "BIBLY", f_bibly, IVORY, ls=14)

# ---- 8) subtitle with side dots ----
sub = "바이블 인사이트"
bb = d.textbbox((0, 0), sub, font=f_sub)
sw = bb[2] - bb[0]
sy = 382
text_center(d, sy, sub, f_sub, GOLD)
# side dots / rules
gap = sw / 2 + 26
d.line([(CX - gap - 46, sy + 24), (CX - gap, sy + 24)], fill=(FRAME[0], FRAME[1], FRAME[2]), width=2)
d.line([(CX + gap, sy + 24), (CX + gap + 46, sy + 24)], fill=(FRAME[0], FRAME[1], FRAME[2]), width=2)
d.ellipse([CX - gap - 60, sy + 19, CX - gap - 50, sy + 29], fill=GOLD)
d.ellipse([CX + gap + 50, sy + 19, CX + gap + 60, sy + 29], fill=GOLD)

# ---- 9) main tagline ----
text_center(d, 440, "말씀으로 시대를 읽다", f_tag, IVORY, ls=1)

# ---- 10) footer keywords ----
text_center(d, 540, "천년왕국 · 종말론 · 성경적 세계관   |   기초부터 100% 무료", f_foot, MUTED, ls=1)

out = "images/og-cover.png"
img.save(out, "PNG")
with open("_og_status.txt", "w", encoding="utf-8") as fp:
    fp.write("saved %s  size=%dx%d  bytes=%d\n" % (out, img.size[0], img.size[1], os.path.getsize(out)))
