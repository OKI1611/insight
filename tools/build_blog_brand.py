# -*- coding: utf-8 -*-
"""네이버 블로그 브랜드 이미지 세트 — BIBLE INSIGHT 정본 로고(DB 모노그램) 기준.

  소스: images/brand/logo-di-square.png (1254x1254) · logo-di-wide.png (1774x887)
  팔레트: navy #061d3a · cream #f4efe4 · gold #d0a457 · green #00704a(액션)
  산출: images/blog/  (PC 타이틀 · 모바일 커버 · 글 상단 헤더 · 글 하단 CTA · 프로필)
  실행: python tools/build_blog_brand.py
"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC  = os.path.join(ROOT, "images", "brand")
OUT  = os.path.join(ROOT, "images", "blog")
os.makedirs(OUT, exist_ok=True)

FB = os.path.join(ROOT, "tools", "fonts", "NotoSerifKR-Bold.ttf")
FR = os.path.join(ROOT, "tools", "fonts", "NotoSerifKR-Regular.ttf")
MG = r"C:\Windows\Fonts\malgun.ttf"
MB = r"C:\Windows\Fonts\malgunbd.ttf"
def f(p, s): return ImageFont.truetype(p, s)

NAVY  = (6, 29, 58)
CREAM = (244, 239, 228)
GOLD  = (208, 164, 87)
GREEN = (0, 112, 74)

SQ = Image.open(os.path.join(SRC, "logo-di-square.png")).convert("RGB")
HZ = Image.open(os.path.join(SRC, "logo-di-wide.png")).convert("RGB")


def content_box(im, thr=150):
    """배경(네이비)을 뺀 로고 내용 영역."""
    a = np.array(im).mean(2)
    ys, xs = np.where(a > thr)
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def row_bands(im, thr=150):
    """세로로 끊기는 구간을 기준으로 [ (시작y, 끝y), ... ] 반환."""
    a = np.array(im).mean(2)
    x0, y0, x1, y1 = content_box(im, thr)
    rows = (a[:, x0:x1] > thr).sum(1) > 0
    bands, s = [], None
    for y in range(y0, y1 + 1):
        on = rows[y] if y < len(rows) else False
        if on and s is None:
            s = y
        elif not on and s is not None:
            bands.append((s, y)); s = None
    if s is not None:
        bands.append((s, y1))
    return bands


def monogram(im):
    """정사각 로고에서 DB 마크만 잘라낸다(아래 BIBLE / INSIGHT 글자는 제외).
       세로 밴드는 [골드 사각형, DB 마크, BIBLE, INSIGHT] 순 —
       가장 높은 밴드(DB 마크)까지를 모노그램으로 본다."""
    bands = row_bands(im)
    top = max(range(len(bands)), key=lambda i: bands[i][1] - bands[i][0])
    y0, y1 = bands[0][0], bands[top][1]
    a = np.array(im).mean(2)
    cols = (a[y0:y1, :] > 150).sum(0)
    nz = np.nonzero(cols)[0]
    return im.crop((int(nz.min()), y0, int(nz.max()) + 1, y1))


def cutout(im):
    """네이비 배경을 투명하게 — 크림 획만 남겨 어떤 배경에도 이음매 없이 얹는다."""
    a = np.array(im).astype(float)
    lum = a.mean(2)
    gold = (a[:, :, 0] - a[:, :, 2] > 40) & (lum > 70) & (lum < 215)
    alpha = np.clip((lum - 45) / (238 - 45) * 1.25, 0, 1)
    alpha[gold] = 1.0
    rgba = im.convert("RGBA")
    rgba.putalpha(Image.fromarray((alpha * 255).astype("uint8")))
    return rgba


def to_light(mark):
    """네이비 배경의 크림 마크 → 투명 배경의 네이비 마크(골드 포인트는 유지)."""
    a = np.array(mark).astype(int)
    lum = a.mean(2)
    gold = (a[:, :, 0] - a[:, :, 2] > 40) & (lum > 70) & (lum < 210)
    ink = lum > 150
    out = np.zeros((a.shape[0], a.shape[1], 3), dtype="uint8")
    out[:] = CREAM
    out[ink] = NAVY
    out[gold] = GOLD
    rgba = Image.fromarray(out).convert("RGBA")
    rgba.putalpha(Image.fromarray(((ink | gold) * 255).astype("uint8")))
    return rgba


def fit(im, w=None, h=None):
    if w:
        return im.resize((w, max(1, int(im.height * w / im.width))), Image.LANCZOS)
    return im.resize((max(1, int(im.width * h / im.height)), h), Image.LANCZOS)


def glow_bg(w, h):
    """평평한 네이비 + 오른쪽 위 은은한 광원(격자·패턴 없이 깔끔하게)."""
    im = Image.new("RGB", (w, h), NAVY)
    g = Image.new("L", (w, h), 0)
    ImageDraw.Draw(g).ellipse([w - int(w * .62), -int(h * 1.1), w + int(w * .18), int(h * .95)], fill=58)
    g = g.filter(ImageFilter.GaussianBlur(max(w, h) // 7))
    return Image.composite(Image.new("RGB", (w, h), (26, 56, 100)), im, g)


def ctr(d, txt, font, y, w, fill):
    bb = d.textbbox((0, 0), txt, font=font)
    d.text(((w - (bb[2] - bb[0])) / 2 - bb[0], y), txt, font=font, fill=fill)


def save(im, name):
    p = os.path.join(OUT, name)
    im.convert("RGB").save(p, "PNG", optimize=True)
    print("  %-32s %-12s %.0fKB" % (name, "%dx%d" % im.size, os.path.getsize(p) / 1024))


MARK_D = cutout(monogram(SQ))          # 어두운 배경용(크림 마크, 배경 투명)
MARK_L = to_light(monogram(SQ))        # 밝은 배경용(네이비 마크, 배경 투명)
LOCKUP = cutout(HZ.crop(content_box(HZ)))          # 가로형 로고
LOGO_SQ = cutout(SQ.crop(content_box(SQ)))         # 정사각 로고(글자 포함)


# ───────────────── ① PC 타이틀 966×280 ─────────────────
def pc_title():
    W, H = 966, 280
    im = glow_bg(W, H)
    lock = fit(LOCKUP, w=560)
    im.paste(lock, ((W - lock.width) // 2, 56), lock)
    d = ImageDraw.Draw(im)
    y = 56 + lock.height + 28
    d.line([(W // 2 - 34, y), (W // 2 + 34, y)], fill=GOLD, width=2)
    ctr(d, "말씀으로 시대를 읽습니다", f(MG, 21), y + 18, W, (214, 223, 238))
    ctr(d, "천년왕국 · 요한계시록 · 종말 예언      |      biblynote.com",
        f(MG, 15), y + 58, W, (136, 158, 196))
    save(im, "01_PC타이틀_966x280.png")


# ───────────────── ② 모바일 커버 1300×1000 ─────────────────
def mobile_cover():
    W, H = 1300, 1000
    im = glow_bg(W, H)
    logo = fit(LOGO_SQ, h=540)
    im.paste(logo, ((W - logo.width) // 2, 128), logo)
    d = ImageDraw.Draw(im)
    y = 128 + logo.height + 44
    d.line([(W // 2 - 46, y), (W // 2 + 46, y)], fill=GOLD, width=3)
    ctr(d, "말씀으로 시대를 읽습니다", f(MG, 40), y + 28, W, (218, 227, 242))
    ctr(d, "천년왕국 · 요한계시록 · 종말 예언", f(MG, 28), y + 94, W, (140, 162, 200))
    save(im, "02_모바일커버_1300x1000.png")


# ───────────────── ③ 글 상단 헤더 800×140 ─────────────────
def post_header():
    W, H = 800, 140
    im = Image.new("RGB", (W, H), (252, 251, 248))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 4], fill=NAVY)
    mark = fit(MARK_L, h=62)
    im.paste(mark, (48, (H - mark.height) // 2 + 2), mark)
    d = ImageDraw.Draw(im)
    x = 48 + mark.width + 26
    d.text((x, 40), "BIBLE INSIGHT", font=f(FB, 23), fill=NAVY)
    d.text((x + 2, 80), "바이블 인사이트 · 오광일", font=f(MG, 15), fill=(122, 138, 168))
    t = "biblynote.com"
    bb = d.textbbox((0, 0), t, font=f(MB, 16))
    d.text((W - 48 - (bb[2] - bb[0]), 60), t, font=f(MB, 16), fill=GREEN)
    d.line([(0, H - 1), (W, H - 1)], fill=(228, 224, 214), width=1)
    save(im, "03_글상단헤더_800x140.png")


# ───────────────── ④ 글 하단 CTA 800×340 ─────────────────
def post_footer():
    W, H = 800, 340
    im = glow_bg(W, H)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 4], fill=GOLD)
    mark = fit(MARK_D, h=76)
    im.paste(mark, (48, 42), mark)
    d = ImageDraw.Draw(im)
    x = 48 + mark.width + 28
    d.text((x, 46), "더 깊이 공부하고 싶으시다면", font=f(FB, 26), fill=CREAM)
    d.text((x + 2, 90), "강의 321편 · 성경사전 5,453항목 · 성경 읽기 · 매일 묵상 — 모두 무료",
           font=f(MG, 15), fill=(160, 180, 214))

    items = [("온라인 성경 아카데미", "biblynote.com", True),
             ("유튜브 인사이트 브리핑", "구독 8,300+", False),
             ("저자의 책", "biblynote.com/books", False)]
    bw, gap, x0, y0 = 226, 22, 48, 168
    for i, (t, s, acc) in enumerate(items):
        bx = x0 + i * (bw + gap)
        d.rounded_rectangle([bx, y0, bx + bw, y0 + 98], radius=12,
                            fill=GREEN if acc else None,
                            outline=None if acc else (92, 116, 158), width=0 if acc else 2)
        d.text((bx + 20, y0 + 27), t, font=f(MB, 16), fill=CREAM if acc else (238, 240, 246))
        d.text((bx + 20, y0 + 58), s, font=f(MG, 14),
               fill=(208, 234, 224) if acc else (146, 168, 204))
    d.text((48, H - 44), "바이블 인사이트 · 오광일   |   말씀으로 시대를 읽습니다",
           font=f(MG, 14), fill=(126, 148, 186))
    save(im, "04_글하단CTA_800x340.png")


# ───────────────── ⑤ 프로필 400×400 ─────────────────
def profile():
    S = 400
    im = glow_bg(S, S)
    logo = fit(LOGO_SQ, h=int(S * 0.62))
    im.paste(logo, ((S - logo.width) // 2, (S - logo.height) // 2), logo)
    save(im, "05_프로필_400x400.png")


if __name__ == "__main__":
    print("블로그 브랜드 이미지 →", OUT)
    pc_title(); mobile_cover(); post_header(); post_footer(); profile()
