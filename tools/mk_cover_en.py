# -*- coding: utf-8 -*-
"""
『The Millennial Kingdom Explained』 영문판 킨들 전자책 앞표지 생성기 — 2026-11-10
  사용: python -X utf8 tools/mk_cover_en.py   (저장소 어디서 실행해도 됨, 재실행 시 같은 결과)
산출물
  책원고/영문판_천년왕국/build/cover_1600x2560.jpg   (1600×2560, RGB, JPEG q95)
  책원고/영문판_천년왕국/build/cover_thumb_120.png   (120px 폭 썸네일, 가독성 점검용)
디자인
  한국어판(천년왕국을 아십니까)의 남색 바탕 + 금색 제목 톤을 잇는다. 벡터 요소만 사용:
  별·지평선(지구 곡면)·한 점의 빛·가는 금색 선·열린 책 엠블럼(tools/make_logo_a.py 와 같은 경로).
  글꼴은 tools/fonts/ 만 쓴다(NotoSerifKR-Bold = 제목, NotoSerif-Regular = 부제, Pretendard = 캡션).
"""
import os, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FDIR = os.path.join(ROOT, "tools", "fonts")
OUT_DIR = os.path.join(ROOT, "책원고", "영문판_천년왕국", "build")
OUT_JPG = os.path.join(OUT_DIR, "cover_1600x2560.jpg")
OUT_THUMB = os.path.join(OUT_DIR, "cover_thumb_120.png")

W, H = 1600, 2560          # 킨들 권장 규격
S = 2                      # 2배 슈퍼샘플링 후 LANCZOS 축소(선·원이 매끈해진다)
SW, SH = W * S, H * S

# ── 팔레트(미니북_만들기.py 와 동일 계열) ──
NAVY = (16, 27, 58)        # #101b3a
NAVY_D = (8, 14, 34)       # 상단 깊은 하늘
NAVY_L = (26, 42, 82)      # #1a2a52 지평선 부근
EARTH = (7, 11, 26)        # 지평선 아래 지구 그림자
GOLD = (201, 162, 75)      # #c9a24b
GOLD_T = (214, 176, 92)    # 제목용(살짝 밝힌 금색)
GOLD_L = (228, 192, 122)   # #e4c07a
CREAM = (243, 238, 225)    # #f3eee1
CREAM_D = (200, 204, 220)  # 부제·캡션용 푸른 크림

def F(name, size):
    p = {"serifb": "NotoSerifKR-Bold.ttf", "serif": "NotoSerif-Regular.ttf",
         "sansx": "Pretendard-Black.ttf", "sansb": "Pretendard-Bold.ttf", "sans": "Pretendard-Regular.ttf"}[name]
    return ImageFont.truetype(os.path.join(FDIR, p), int(size * S))

# ───────────────────────── 배경 ─────────────────────────
def background():
    """세로 그라데이션(위 깊은 남색 → 지평선 쪽 밝은 남색) 을 numpy 로 만든다."""
    y = np.linspace(0.0, 1.0, SH)[:, None]
    horizon = 0.735                                   # 지평선 위치(비율)
    t = np.clip(y / horizon, 0, 1) ** 1.6            # 아래로 갈수록 밝게
    top, mid = np.array(NAVY_D, float), np.array(NAVY_L, float)
    rgb = (top[None, None, :] + (mid - top)[None, None, :] * t[:, :, None])   # (SH,1,3)
    x = np.linspace(-1, 1, SW)[None, :, None]        # 좌우 가장자리 비네팅 (1,SW,1)
    rgb = rgb * (1 - 0.18 * (x ** 2))                # → (SH,SW,3)
    return Image.fromarray(rgb.clip(0, 255).astype(np.uint8), "RGB")

def stars(im, n=260, seed=7):
    rnd = random.Random(seed)
    d = ImageDraw.Draw(im, "RGBA")
    for _ in range(n):
        x, y = rnd.uniform(0, SW), rnd.uniform(0, SH * 0.70)
        r = rnd.choice([0.9, 1.1, 1.4, 1.8, 2.4]) * S
        a = int(rnd.uniform(70, 210) * (1 - y / (SH * 0.9)))
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 250, 235, max(a, 20)))
    for _ in range(9):                                # 조금 큰 별 몇 개에 십자 반짝임(글자 띠 위쪽 하늘에만)
        x, y = rnd.uniform(SW * 0.08, SW * 0.92), rnd.uniform(SH * 0.03, SH * 0.125)
        L = rnd.uniform(8, 16) * S
        d.line([x - L, y, x + L, y], fill=(255, 245, 220, 110), width=S)
        d.line([x, y - L, x, y + L], fill=(255, 245, 220, 110), width=S)
        d.ellipse([x - 2 * S, y - 2 * S, x + 2 * S, y + 2 * S], fill=(255, 250, 235, 230))

def glow_layer(size, color, radius_px, cx, cy, strength=1.0, power=1.0):
    """중심 (cx,cy) 에서 radius_px 까지 퍼지는 원형 빛 레이어(RGBA)."""
    # (PIL 의 radial_gradient 는 변 가운데서 128 에 그쳐 사각 경계가 드러난다 → 직접 만든다)
    n = radius_px * 2
    yy, xx = np.ogrid[:n, :n]
    dist = np.sqrt((xx - radius_px + 0.5) ** 2 + (yy - radius_px + 0.5) ** 2) / radius_px
    arr = (1.0 - np.clip(dist, 0, 1)) ** power * 255 * strength
    mask = Image.fromarray(arr.clip(0, 255).astype(np.uint8), "L")
    layer = Image.new("RGBA", size, color + (0,))
    solid = Image.new("RGBA", mask.size, color + (255,))
    solid.putalpha(mask)
    layer.alpha_composite(solid, (int(cx - radius_px), int(cy - radius_px)))
    return layer

def mul_alpha(layer, mask_arr):
    """RGBA 레이어의 알파에 0~1 배열을 곱한다."""
    a = np.asarray(layer.getchannel("A"), dtype=np.float32) * mask_arr
    layer.putalpha(Image.fromarray(a.clip(0, 255).astype(np.uint8), "L"))
    return layer

def horizon(im):
    """지구 곡면: 큰 원의 윗부분이 지평선. 그 테두리에 금빛 림라이트, 가운데 한 점의 빛."""
    HY = int(SH * 0.735)                     # 지평선(원 꼭대기) y
    R = int(SW * 1.55)                       # 지구 반지름(완만한 곡률)
    CX, CY = SW // 2, HY + R
    base = im.convert("RGBA")

    # 1) 지평선 바깥 하늘 글로우(크고 은은한 남청색) + 2) 금빛 새벽 글로우
    base.alpha_composite(glow_layer(base.size, (74, 102, 170), int(SW * 0.95), CX, HY, 0.55, 1.8))
    base.alpha_composite(glow_layer(base.size, (220, 180, 110), int(SW * 0.52), CX, HY, 0.75, 2.2))

    # 3) 지구 본체(지평선 아래는 어둡게) + 안쪽 위 가장자리의 옅은 남색(대기 산란)
    circle = Image.new("L", base.size, 0)
    ImageDraw.Draw(circle).ellipse([CX - R, CY - R, CX + R, CY + R], fill=255)
    circle_arr = np.asarray(circle, dtype=np.float32) / 255.0
    earth = Image.new("RGBA", base.size, EARTH + (255,))
    earth.putalpha(circle)
    inner = mul_alpha(glow_layer(base.size, (28, 48, 96), int(SW * 0.9), CX, HY, 0.9, 1.4), circle_arr)
    earth.alpha_composite(inner)
    base.alpha_composite(earth)

    # 4) 림라이트(지평선 가장자리의 금빛 가는 호) — 좌우로 갈수록 사라지고, 블러로 부드럽게
    rim = Image.new("RGBA", base.size, (0, 0, 0, 0))
    rd = ImageDraw.Draw(rim)
    for w, a in ((22 * S, 60), (10 * S, 120), (4 * S, 230)):
        rd.ellipse([CX - R, CY - R, CX + R, CY + R], outline=GOLD_L + (a,), width=w)
    xs = np.linspace(-1, 1, SW)
    fade = np.clip(1 - np.abs(xs) ** 1.6, 0, 1)
    rim = mul_alpha(rim, np.repeat(fade[None, :], SH, axis=0))
    rim = rim.filter(ImageFilter.GaussianBlur(3 * S))
    base.alpha_composite(rim)

    # 5) 한 점의 빛(지평선 한가운데)
    base.alpha_composite(glow_layer(base.size, (255, 236, 190), int(SW * 0.22), CX, HY, 0.9, 3.5))
    base.alpha_composite(glow_layer(base.size, (255, 250, 235), int(18 * S), CX, HY, 1.0, 1.2))
    d = ImageDraw.Draw(base)
    r = 5 * S
    d.ellipse([CX - r, HY - r, CX + r, HY + r], fill=(255, 255, 250, 255))
    # 지평선 아래, 아주 가는 금빛 점 몇 개(벡터) — 한국어판의 땅 위 불빛을 암시
    rnd = random.Random(11)
    for _ in range(70):
        ang = rnd.uniform(-0.18, 0.18)
        rr = R - rnd.uniform(40, 520) * S
        x, y = CX + rr * math.sin(ang), CY - rr * math.cos(ang)
        rad = rnd.choice([0.8, 1.0, 1.4]) * S
        d.ellipse([x - rad, y - rad, x + rad, y + rad], fill=(240, 200, 130, rnd.randint(60, 170)))
    return base.convert("RGB"), HY

# ───────────────────────── 글자 ─────────────────────────
def spaced_width(d, text, font, tracking):
    return sum(d.textlength(ch, font=font) for ch in text) + tracking * S * (len(text) - 1)

def draw_spaced(d, text, font, cx, y, fill, tracking=0.0):
    """글자 간격(tracking, 1배 px 단위) 을 두고 가운데 정렬로 쓴다. y 는 대문자 윗선."""
    tw = spaced_width(d, text, font, tracking)
    x = cx - tw / 2
    asc = font.getbbox("H")[1]
    for ch in text:
        d.text((x, y - asc), ch, font=font, fill=fill)
        x += d.textlength(ch, font=font) + tracking * S
    return tw

def text_glow(base, draw_fn, blur, color_alpha):
    """draw_fn(d, fill) 로 같은 글자를 레이어에 그려 블러 → 뒤에 깔아 은은한 광륜을 만든다."""
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(layer), color_alpha)
    layer = layer.filter(ImageFilter.GaussianBlur(blur * S))
    base.alpha_composite(layer)

TITLE_LINES = ["MILLENNIAL", "KINGDOM", "EXPLAINED"]
TITLE_MAX_W = W - 2 * 100      # 제목 최대 폭(1배 px)
TITLE_TOP = 600                # 큰 글자 첫 줄 윗선(1배 px)
TITLE_TRACK = 3

def fit_size(d, lines, tracking, max_w, lo=80, hi=230):
    """max_w 안에 들어가는 가장 큰 글자 크기를 찾는다(1배 px)."""
    while hi - lo > 1:
        mid = (lo + hi) // 2
        f = F("serifb", mid)
        if max(spaced_width(d, t, f, tracking) for t in lines) <= max_w * S:
            lo = mid
        else:
            hi = mid
    return lo

def title_block(base):
    """제목: 작은 'THE' 리드 + 큰 금색 3단어(MILLENNIAL / KINGDOM / EXPLAINED)."""
    d = ImageDraw.Draw(base)
    size = fit_size(d, TITLE_LINES, TITLE_TRACK, TITLE_MAX_W)
    font = F("serifb", size)
    top = TITLE_TOP * S
    leading = int(size * 1.12 * S)
    # 리드 'THE' — 작은 세리프, 넓은 자간, 양옆 짧은 금선
    fl = F("serifb", 54)
    the_y = top - 112 * S
    tw = draw_spaced(d, "THE", fl, SW / 2, the_y, GOLD_L, tracking=14)
    cy = the_y + fl.getbbox("H")[3] * 0.5 - fl.getbbox("H")[1] * 0.5 + 0  # 대문자 중간 높이
    for sgn in (-1, 1):
        x0 = SW / 2 + sgn * (tw / 2 + 36 * S)
        d.line([x0, cy, x0 + sgn * 120 * S, cy], fill=GOLD + (200,), width=S)
    def paint(dd, fill):
        for i, t in enumerate(TITLE_LINES):
            draw_spaced(dd, t, font, SW / 2, top + i * leading, fill, tracking=TITLE_TRACK)
    text_glow(base, paint, 14, (255, 215, 140, 120))
    paint(ImageDraw.Draw(base), GOLD_T)
    print("title size %dpx" % size)
    return top + (len(TITLE_LINES) - 1) * leading + int(size * 0.74 * S)   # 마지막 줄 밑선

def italic_text(text, font, fill, shear=0.18):
    """NotoSerif 에 이탤릭이 없어 레이어를 기울여 이탤릭 느낌을 낸다."""
    tmp = ImageDraw.Draw(Image.new("L", (1, 1)))
    bbox = tmp.textbbox((0, 0), text, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad = int(h * shear) + 8
    layer = Image.new("RGBA", (w + 2 * pad, h + 8), (0, 0, 0, 0))
    ImageDraw.Draw(layer).text((pad - bbox[0], 4 - bbox[1]), text, font=font, fill=fill)
    # 출력 (x,y) ← 입력 (x + shear*(y - h*0.75), y): 윗부분이 오른쪽으로 기운다
    layer = layer.transform(layer.size, Image.AFFINE, (1, shear, -shear * layer.size[1] * 0.75, 0, 1, 0), Image.BICUBIC)
    return layer

def rule(d, cx, y, half, color=GOLD, w=2):
    """가운데 작은 마름모가 있는 가는 금색 선."""
    d.line([cx - half * S, y, cx - 22 * S, y], fill=color, width=w * S)
    d.line([cx + 22 * S, y, cx + half * S, y], fill=color, width=w * S)
    r = 7 * S
    d.polygon([(cx, y - r), (cx + r, y), (cx, y + r), (cx - r, y)], fill=color)

# ───────────────────────── 엠블럼(열린 책 · 한 점의 빛) ─────────────────────────
def bezier(p0, p1, p2, p3, n=40):
    pts = []
    for i in range(n + 1):
        t = i / n; u = 1 - t
        x = u**3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t**3 * p3[0]
        y = u**3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t**3 * p3[1]
        pts.append((x, y))
    return pts

def emblem(d, cx, cy, size, color):
    """tools/make_logo_a.py 의 mark() 와 같은 경로(viewBox 0 0 100 100, stroke 6.5, round cap)."""
    k = size * S / 100.0
    T = lambda p: (cx + (p[0] - 50) * k, cy + (p[1] - 50) * k)
    sw = max(int(round(6.5 * k)), 2)
    def stroke(pts):
        pts = [T(p) for p in pts]
        d.line(pts, fill=color, width=sw, joint="curve")
        for p in (pts[0], pts[-1]):
            r = sw / 2
            d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=color)
    left = bezier((50, 40), (42, 31), (30, 29), (18, 31)) + [(18, 72)] + bezier((18, 72), (30, 70), (42, 72), (50, 80))
    right = [(100 - x, y) for x, y in left]
    stroke(left); stroke(right); stroke([(50, 40), (50, 80)])
    c = T((50, 19)); r = 5.5 * k
    d.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], fill=color)

# ───────────────────────── 조립 ─────────────────────────
def build():
    im = background()
    stars(im)
    im, HY = horizon(im)
    base = im.convert("RGBA")
    d = ImageDraw.Draw(base)
    cx = SW / 2

    # 얇은 안쪽 테두리(한국어 미니북 표지의 금색 틀을 아주 옅게)
    m = 58 * S
    d.rectangle([m, m, SW - m, SH - m], outline=GOLD + (70,), width=S)

    # 1) 키커(세미나 조회수) — 작은 대문자, 넓은 자간
    kicker = "FROM THE BIBLE-PROPHECY SEMINAR VIEWED 1.49 MILLION TIMES"
    draw_spaced(d, kicker, F("sansb", 30), cx, 395 * S, CREAM_D, tracking=4.2)
    rule(d, cx, 455 * S, 150, GOLD + (190,), 1)

    # 2) 제목
    bottom = title_block(base)
    d = ImageDraw.Draw(base)

    # 3) 가는 금색 선
    rule(d, cx, bottom + 88 * S, 230)

    # 4) 부제(크림, 세리프 이탤릭 느낌) 2줄
    fs = F("serif", 60)
    sub1 = italic_text("The Real Thousand-Year Kingdom", fs, CREAM)
    sub2 = italic_text("the Bible Promised", fs, CREAM)
    y = bottom + 150 * S
    base.alpha_composite(sub1, (int(cx - sub1.size[0] / 2), int(y)))
    base.alpha_composite(sub2, (int(cx - sub2.size[0] / 2), int(y + 84 * S)))

    # 5) 저자(자간 넓게) — 지평선 위, 빛의 자리 바로 위
    d = ImageDraw.Draw(base)
    draw_spaced(d, "KWANG-IL OH", F("sansb", 50), cx, HY - 230 * S, CREAM, tracking=12)

    # 6) 엠블럼 + 출판사 표기(지평선 아래 어두운 영역)
    emblem(d, cx, HY + 300 * S, 150, GOLD)
    draw_spaced(d, "BIBLY INSIGHT", F("sansb", 30), cx, HY + 425 * S, GOLD_L, tracking=8)

    return base.convert("RGB").resize((W, H), Image.LANCZOS)

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    cover = build()
    assert cover.size == (W, H) and cover.mode == "RGB"
    cover.save(OUT_JPG, "JPEG", quality=95, optimize=True, subsampling=0)
    th = cover.resize((120, round(120 * H / W)), Image.LANCZOS)
    th.save(OUT_THUMB, "PNG")
    print(OUT_JPG, cover.size, "%.2f MB" % (os.path.getsize(OUT_JPG) / 1048576))
    print(OUT_THUMB, th.size)

if __name__ == "__main__":
    main()
