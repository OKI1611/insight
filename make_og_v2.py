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
GOLD   = (116, 198, 157)  # 스타벅스 그린 계열(밝은 초록 · 네이비 위 강조)
GOLD_BR= (150, 215, 180)  # brighter green accent
IVORY  = (244, 241, 234)  # near-white warm
MUTED  = (150, 168, 198)  # cool blue-grey
FRAME  = (70, 150, 110)   # frame green

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

# ---- 5) 실제 로고(펼친 책)를 흰 라운드 뱃지 위에 ----
bcx, bcy, bs = CX, 118, 78
d.rounded_rectangle([bcx - bs, bcy - bs, bcx + bs, bcy + bs], radius=26, fill=(255, 255, 255))
try:
    _bk = Image.open("_book_t.png").convert("RGBA")
    _th = int(bs * 1.5); _bw, _bh = _bk.size; _sc = _th / _bh
    _bk = _bk.resize((max(1, int(_bw * _sc)), _th), Image.LANCZOS)
    img.paste(_bk, (int(bcx - _bk.width / 2), int(bcy - _bk.height / 2)), _bk)
except Exception:
    pass

# ---- 6) eyebrow ----
text_center(d, 212, "유튜브 「오광일의 인사이트 브리핑」 공식 강의 플랫폼", f_eye, MUTED, ls=2)

# ---- 7) 바이블 인사이트 워드마크 (한글 볼드) ----
f_wm = F(KB, 92)
text_center(d, 250, "바이블 인사이트", f_wm, IVORY, ls=2)

# ---- 8) 초록 구분선 (가운데 점) ----
dy = 384
d.line([(CX - 132, dy), (CX - 34, dy)], fill=(FRAME[0], FRAME[1], FRAME[2]), width=2)
d.line([(CX + 34, dy), (CX + 132, dy)], fill=(FRAME[0], FRAME[1], FRAME[2]), width=2)
d.ellipse([CX - 6, dy - 6, CX + 6, dy + 6], fill=GOLD)

# ---- 9) main tagline ----
text_center(d, 406, "말씀으로 시대를 읽다", f_tag, IVORY, ls=1)

# ---- 10) footer keywords ----
text_center(d, 528, "천년왕국 · 종말론 · 성경적 세계관   |   기초부터 100% 무료", f_foot, MUTED, ls=1)

out = "images/og-cover.png"
img.save(out, "PNG")
with open("_og_status.txt", "w", encoding="utf-8") as fp:
    fp.write("saved %s  size=%dx%d  bytes=%d\n" % (out, img.size[0], img.size[1], os.path.getsize(out)))
