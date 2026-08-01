# -*- coding: utf-8 -*-
"""네이버 블로그 브랜드 이미지 세트 — 홈페이지(BIBLY 바이블 인사이트) 톤 그대로.
   ① PC 타이틀 배너 ② 모바일 커버 ③ 글 상단 헤더 ④ 글 하단 CTA
   팔레트: navy #182c54 / ink #213a6b / green #00704a / sand #eaf0f8 / white
"""
import os, io, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

sys.stdout.reconfigure(encoding="utf-8")
HOME = r"C:\Users\오광일\OneDrive\바탕 화면\홈페이지 제작"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT  = os.path.join(HOME, "images", "blog")
os.makedirs(OUT, exist_ok=True)

FB = os.path.join(HERE, "fonts", "NotoSerifKR-Bold.ttf")
FR = os.path.join(HERE, "fonts", "NotoSerifKR-Regular.ttf")
MG = r"C:\Windows\Fonts\malgun.ttf"
MB = r"C:\Windows\Fonts\malgunbd.ttf"
def f(path, sz): return ImageFont.truetype(path, sz)

NAVY  = (24, 44, 84)
INK   = (33, 58, 107)
GREEN = (0, 112, 74)
SAND  = (234, 240, 248)
WHITE = (255, 255, 255)
SOFT  = (231, 214, 172)

# ── 로고에서 책 심볼만 잘라내기(글자 부분 제외) ──────────────
_logo = Image.open(os.path.join(HOME, "images", "logo-bible-insight.png")).convert("RGB")
_sym  = _logo.crop((8, 4, 184, 140))            # 펼친 책 부분

def symbol(size, on_white_card=True, pad=0.20):
    """책 심볼을 흰 카드 위에 올려 반환(네이비 배경에서도 원색 유지)."""
    s = _sym.copy()
    s.thumbnail((int(size * (1 - pad * 2)), int(size * (1 - pad * 2))), Image.LANCZOS)
    if not on_white_card:
        return s
    card = Image.new("RGB", (size, size), WHITE)
    card.paste(s, ((size - s.width) // 2, (size - s.height) // 2))
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size - 1, size - 1], radius=int(size * 0.22), fill=255)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(card, (0, 0), mask)
    return out

def vgrad(w, h, top, bot):
    g = Image.new("RGB", (1, h))
    px = g.load()
    for y in range(h):
        t = y / max(1, h - 1)
        px[0, y] = tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3))
    return g.resize((w, h), Image.BICUBIC)

def center(d, txt, font, y, w, fill):
    bb = d.textbbox((0, 0), txt, font=font)
    d.text(((w - (bb[2] - bb[0])) / 2 - bb[0], y), txt, font=font, fill=fill)
    return bb[3] - bb[1]

def save(im, name):
    p = os.path.join(OUT, name)
    im.convert("RGB").save(p, "PNG", optimize=True)
    print("  %-34s %s  %.0fKB" % (name, im.size, os.path.getsize(p) / 1024))
    return p

# ───────────────────────── ① PC 타이틀 배너 966×260 ─────────────────────────
def title_banner():
    W, H = 966, 260
    im = vgrad(W, H, (30, 54, 100), (18, 33, 62))
    # 오른쪽 위에서 번지는 은은한 광원 — 격자보다 훨씬 깔끔하다
    glow = Image.new("L", (W, H), 0)
    ImageDraw.Draw(glow).ellipse([W - 560, -300, W + 160, 300], fill=64)
    glow = glow.filter(ImageFilter.GaussianBlur(140))
    im = Image.composite(Image.new("RGB", (W, H), (56, 86, 142)), im, glow)
    d = ImageDraw.Draw(im)

    sym = symbol(96)
    im.paste(sym, (78, 62), sym)

    x = 78 + 96 + 32
    d.text((x, 68), "바이블 인사이트", font=f(FB, 46), fill=WHITE)
    d.text((x + 3, 130), "BIBLE INSIGHT", font=f(FR, 16), fill=(146, 168, 208))
    d.line([(x + 3, 174), (x + 58, 174)], fill=GREEN, width=3)
    d.text((x + 3, 190), "말씀으로 시대를 읽습니다", font=f(MG, 19), fill=(204, 217, 238))

    # 오른쪽 정보 블록
    rx = W - 78
    for i, (t, fo, col) in enumerate([
        ("오광일의 인사이트 브리핑", f(MB, 17), WHITE),
        ("유튜브 구독 8,300+", f(MG, 15), (168, 188, 222)),
        ("biblynote.com", f(MG, 15), SOFT)]):
        bb = d.textbbox((0, 0), t, font=fo)
        d.text((rx - (bb[2] - bb[0]), 96 + i * 30), t, font=fo, fill=col)
    d.line([(0, H - 4), (W, H - 4)], fill=GREEN, width=4)
    return save(im, "01_PC타이틀_966x260.png")

# ───────────────────────── ② 모바일 커버 1300×1000 ─────────────────────────
def mobile_cover():
    W, H = 1300, 1000
    im = vgrad(W, H, (32, 58, 106), (16, 30, 58))
    d = ImageDraw.Draw(im)
    sym = symbol(230)
    im.paste(sym, ((W - 230) // 2, 250), sym)
    d = ImageDraw.Draw(im)
    center(d, "바이블 인사이트", f(FB, 88), 530, W, WHITE)
    center(d, "BIBLE INSIGHT", f(FR, 30), 646, W, (150, 172, 210))
    d.line([(W // 2 - 60, 706), (W // 2 + 60, 706)], fill=GREEN, width=5)
    center(d, "말씀으로 시대를 읽습니다", f(MG, 36), 740, W, (208, 220, 240))
    center(d, "천년왕국 · 요한계시록 · 종말 예언", f(MG, 27), 800, W, (150, 172, 210))
    center(d, "biblynote.com", f(MG, 26), 866, W, SOFT)
    return save(im, "02_모바일커버_1300x1000.png")

# ───────────────────────── ③ 글 상단 헤더 800×150 ─────────────────────────
def post_header():
    W, H = 800, 150
    im = Image.new("RGB", (W, H), WHITE)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, H], fill=(250, 251, 253))
    d.line([(0, 0), (W, 0)], fill=GREEN, width=5)
    sym = symbol(76, on_white_card=False)
    im.paste(sym, (46, (H - sym.height) // 2 + 2))
    d = ImageDraw.Draw(im)
    d.text((136, 40), "바이블 인사이트", font=f(FB, 27), fill=INK)
    d.text((138, 82), "말씀으로 시대를 읽습니다  ·  오광일", font=f(MG, 15), fill=(120, 136, 166))
    t = "biblynote.com"
    bb = d.textbbox((0, 0), t, font=f(MB, 16))
    d.text((W - 44 - (bb[2] - bb[0]), 66), t, font=f(MB, 16), fill=GREEN)
    d.line([(0, H - 1), (W, H - 1)], fill=(226, 232, 242), width=1)
    return save(im, "03_글상단헤더_800x150.png")

# ───────────────────────── ④ 글 하단 CTA 800×330 ─────────────────────────
def post_footer():
    W, H = 800, 330
    im = vgrad(W, H, (30, 54, 100), (18, 33, 62))
    d = ImageDraw.Draw(im)
    d.line([(0, 0), (W, 0)], fill=GREEN, width=5)
    sym = symbol(76)
    im.paste(sym, (44, 40), sym)
    d = ImageDraw.Draw(im)
    d.text((146, 48), "더 깊이 공부하고 싶으시다면", font=f(FB, 27), fill=WHITE)
    d.text((148, 92), "강의 321편 · 성경사전 5,453항목 · 성경 읽기 · 매일 묵상 — 모두 무료", font=f(MG, 15), fill=(174, 192, 224))

    items = [("온라인 성경 아카데미", "biblynote.com"),
             ("유튜브 인사이트 브리핑", "구독 8,300+"),
             ("저자의 책", "biblynote.com/books")]
    bw, gap, x0, y0 = 226, 22, 44, 160
    for i, (t, s) in enumerate(items):
        x = x0 + i * (bw + gap)
        acc = i == 0
        d.rounded_rectangle([x, y0, x + bw, y0 + 96], radius=12,
                            fill=GREEN if acc else None,
                            outline=None if acc else (104, 128, 172), width=0 if acc else 2)
        d.text((x + 20, y0 + 26), t, font=f(MB, 16), fill=WHITE)
        d.text((x + 20, y0 + 56), s, font=f(MG, 14),
               fill=(214, 236, 226) if acc else (160, 180, 214))
    d.text((44, H - 46), "바이블 인사이트 · 오광일   |   말씀으로 시대를 읽습니다",
           font=f(MG, 14), fill=(140, 160, 196))
    return save(im, "04_글하단CTA_800x330.png")

if __name__ == "__main__":
    print("블로그 브랜드 이미지 생성 →", OUT)
    title_banner(); mobile_cover(); post_header(); post_footer()
