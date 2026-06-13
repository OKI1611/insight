# -*- coding: utf-8 -*-
"""BIBLY app icons + maskable + apple-touch + install screenshots."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

NAVY_T = (22, 34, 62)
NAVY_B = (12, 22, 44)
GLOW   = (46, 66, 112)
GOLD   = (216, 194, 138)
GOLD_BR= (233, 214, 166)
IVORY  = (244, 241, 234)
MUTED  = (150, 168, 198)
SER    = "C:/Windows/Fonts/georgiab.ttf"
KB     = "C:/Windows/Fonts/malgunbd.ttf"
KR     = "C:/Windows/Fonts/malgun.ttf"

def grad_bg(S, glow=True):
    img = Image.new("RGB", (S, S), NAVY_T)
    px = img.load()
    for y in range(S):
        t = y / (S - 1); te = t * t * (3 - 2 * t)
        r = int(NAVY_T[0] + (NAVY_B[0]-NAVY_T[0])*te)
        g = int(NAVY_T[1] + (NAVY_B[1]-NAVY_T[1])*te)
        b = int(NAVY_T[2] + (NAVY_B[2]-NAVY_T[2])*te)
        for x in range(S): px[x, y] = (r, g, b)
    if glow:
        m = Image.new("L", (S, S), 0)
        d = ImageDraw.Draw(m)
        d.ellipse([S*0.12, S*0.02, S*0.88, S*0.78], fill=255)
        m = m.filter(ImageFilter.GaussianBlur(S*0.16))
        gl = Image.new("RGB", (S, S), GLOW)
        img = Image.composite(gl, img, m.point(lambda v: int(v*0.5)))
    return img

def draw_book(d, cx, cy, hw, w=0):
    """open-book monoline emblem centered at (cx,cy)."""
    th = max(2, int(hw*0.10)) if w == 0 else w
    top = hw*0.34; bot = hw*0.24; out = hw*0.40
    d.line([(cx, cy-top), (cx, cy+bot)], fill=GOLD, width=th)
    for s in (-1, 1):
        d.line([(cx, cy+bot), (cx+s*hw, cy+bot*0.4)], fill=GOLD, width=th)
        d.line([(cx+s*hw, cy+bot*0.4), (cx+s*(hw-th*1.2), cy-out)], fill=GOLD, width=th)
        d.line([(cx+s*(hw-th*1.2), cy-out), (cx, cy-top)], fill=GOLD, width=th)

def icon(S, glyph=0.56, book=True, border=True):
    img = grad_bg(S)
    d = ImageDraw.Draw(img, "RGBA")
    if border:
        m = int(S*0.066); rw = max(3, int(S*0.012)); rad = int(S*0.12)
        d.rounded_rectangle([m, m, S-m, S-m], radius=rad,
                            outline=(FRAMEc[0], FRAMEc[1], FRAMEc[2], 150), width=rw)
    # serif B
    f = ImageFont.truetype(SER, int(S*glyph))
    bb = d.textbbox((0, 0), "B", font=f)
    bw, bh = bb[2]-bb[0], bb[3]-bb[1]
    by = S*0.50 if book else S*0.52
    d.text((S/2 - bw/2 - bb[0], by - bh/2 - bb[1] - (S*0.04 if book else 0)),
           "B", font=f, fill=IVORY)
    if book:
        draw_book(d, S/2, S*0.78, S*0.14)
    return img

FRAMEc = (198, 170, 110)

os.makedirs("images", exist_ok=True)
out = []

# any-purpose icons (full bleed, subtle border)
for S in (192, 512):
    im = icon(S, glyph=0.56, book=True, border=True)
    p = f"images/icon-{S}.png"; im.save(p, "PNG"); out.append((p, os.path.getsize(p)))

# maskable (generous safe zone: glyph smaller, no border near edge)
im = icon(512, glyph=0.42, book=False, border=False)
p = "images/icon-maskable-512.png"; im.save(p, "PNG"); out.append((p, os.path.getsize(p)))

# apple-touch (180, opaque, no border ring needed - iOS rounds)
im = icon(180, glyph=0.56, book=True, border=False)
p = "images/apple-touch-icon.png"; im.save(p, "PNG"); out.append((p, os.path.getsize(p)))

# ---- install screenshot (mobile narrow 1080x1920) ----
def screenshot():
    W, H = 1080, 1920
    img = Image.new("RGB", (W, H), NAVY_T)
    px = img.load()
    for y in range(H):
        t = y/(H-1); te = t*t*(3-2*t)
        r = int(NAVY_T[0]+(NAVY_B[0]-NAVY_T[0])*te)
        g = int(NAVY_T[1]+(NAVY_B[1]-NAVY_T[1])*te)
        b = int(NAVY_T[2]+(NAVY_B[2]-NAVY_T[2])*te)
        for x in range(W): px[x, y] = (r, g, b)
    m = Image.new("L", (W, H), 0); dd = ImageDraw.Draw(m)
    dd.ellipse([W*0.05, H*0.04, W*0.95, H*0.6], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(180))
    img = Image.composite(Image.new("RGB",(W,H),GLOW), img, m.point(lambda v:int(v*0.5)))
    d = ImageDraw.Draw(img, "RGBA")
    CX = W//2
    def ctr(cy, s, font, fill, ls=0):
        if ls == 0:
            bb = d.textbbox((0,0), s, font=font); w = bb[2]-bb[0]
            d.text((CX-w/2-bb[0], cy), s, font=font, fill=fill); return
        ws = [d.textbbox((0,0),c,font=font)[2]-d.textbbox((0,0),c,font=font)[0] for c in s]
        x = CX-(sum(ws)+ls*(len(s)-1))/2
        for c,w in zip(s,ws):
            bb=d.textbbox((0,0),c,font=font); d.text((x-bb[0],cy),c,font=font,fill=fill); x+=w+ls
    draw_book(d, CX, 360, 92)
    ctr(470, "유튜브 「오광일의 인사이트 브리핑」 공식", ImageFont.truetype(KR,34), MUTED, ls=2)
    ctr(540, "BIBLY", ImageFont.truetype(SER,210), IVORY, ls=18)
    sub="바이블 인사이트"; f=ImageFont.truetype(KB,62)
    ctr(820, sub, f, GOLD)
    ctr(930, "말씀으로 시대를 읽다", ImageFont.truetype(KB,84), IVORY, ls=1)
    d.rectangle([CX-60, 1070, CX+60, 1075], fill=GOLD_BR)
    feats = ["255편 무료 강의 · 평생 무제한 소장",
             "천년왕국 · 종말론 · 성경적 세계관",
             "요약노트 · 확인퀴즈 · 강사 질의응답",
             "가입 없이 시청 · 100% 무료"]
    fy = 1200; ff = ImageFont.truetype(KR,44)
    for s in feats:
        d.ellipse([CX-320, fy+14, CX-300, fy+34], fill=GOLD)
        bb=d.textbbox((0,0),s,font=ff); d.text((CX-275, fy), s, font=ff, fill=IVORY); fy+=110
    # pill
    pill="📱 홈 화면에 추가하면 앱처럼"; pf=ImageFont.truetype(KB,46)
    bb=d.textbbox((0,0),pill,font=pf); pw=bb[2]-bb[0]
    d.rounded_rectangle([CX-pw/2-40, 1700, CX+pw/2+40, 1790], radius=45,
                        fill=(GOLD[0],GOLD[1],GOLD[2],255))
    d.text((CX-pw/2-bb[0], 1718), pill, font=pf, fill=(16,27,52))
    return img

sc = screenshot(); p="images/screenshot-mobile.png"; sc.save(p,"PNG"); out.append((p, os.path.getsize(p)))

with open("_icon_status.txt","w",encoding="utf-8") as fp:
    for path, sz in out: fp.write("%s  %d bytes\n" % (path, sz))
