# -*- coding: utf-8 -*-
"""앱 테스터 모집 카드뉴스 5장 생성 (유튜브 커뮤니티·인스타 공용 1080×1080)

  브랜드: 딥네이비(#0a2540)·브랜드 그린(#00704a)·크림(#f7f4ed)·포인트 골드(#ffd76a)
  서체:  Malgun Gothic Bold/Regular (Windows 기본 — 한글 자간 안정)
  실행:  python tools/make_tester_cards.py  →  images/promo/tester/card1~5.png
"""
import os, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "images", "promo", "tester")
os.makedirs(OUT, exist_ok=True)

W = H = 1080
NAVY = (10, 37, 64); GREEN = (0, 112, 74); DEEP = (10, 61, 43)
CREAM = (247, 244, 237); GOLD = (255, 215, 106); WHITE = (255, 255, 255)
GRAY = (150, 162, 176); INK = (28, 36, 49)

FB = r"C:\Windows\Fonts\malgunbd.ttf"
FR = r"C:\Windows\Fonts\malgun.ttf"
def f(sz, bold=True): return ImageFont.truetype(FB if bold else FR, sz)

def tw(d, t, fnt): return d.textbbox((0, 0), t, font=fnt)[2]

def center(d, y, t, fnt, fill):
    d.text(((W - tw(d, t, fnt)) / 2, y), t, font=fnt, fill=fill)

def bg(top, bottom):
    """세로 그라데이션 배경"""
    im = Image.new("RGB", (W, H), top)
    dd = ImageDraw.Draw(im)
    for y in range(H):
        r = y / H
        dd.line([(0, y), (W, y)], fill=tuple(int(top[i] + (bottom[i] - top[i]) * r) for i in range(3)))
    return im

def pill(d, cx, y, text, fnt, fg, bgc, padx=26, pady=13, r=999):
    w = tw(d, text, fnt); h = fnt.size + pady * 2
    x0 = cx - (w + padx * 2) / 2
    d.rounded_rectangle([x0, y, x0 + w + padx * 2, y + h], radius=r, fill=bgc)
    d.text((x0 + padx, y + pady - 2), text, font=fnt, fill=fg)
    return y + h

def softbox(im, box, radius=26, alpha=26, outline=None, width=0):
    """RGB 캔버스에 반투명 흰 박스 — d.rounded_rectangle의 알파는 무시되므로 오버레이로 합성"""
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    od.rounded_rectangle(box, radius=radius, fill=(255, 255, 255, alpha),
                         outline=outline, width=width)
    im.alpha_composite(ov) if im.mode == "RGBA" else im.paste(
        Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB"), (0, 0))


def brand(d, y=980):
    fs = f(26, False)
    t = "BIBLY  바이블 인사이트  ·  biblynote.com"
    d.text(((W - tw(d, t, fs)) / 2, y), t, font=fs, fill=(160, 180, 172))

# ── 1) 표지 ─────────────────────────────────────────────
def card1():
    im = bg(NAVY, DEEP); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 12], fill=GOLD)
    pill(d, W/2, 120, "선착순 25명 모집", f(30), DEEP, GOLD)
    center(d, 235, "바이블 인사이트가", f(62), WHITE)
    center(d, 320, "‘앱’이 됩니다", f(78), GOLD)
    d.line([(W/2 - 90, 445), (W/2 + 90, 445)], fill=(120, 150, 140), width=3)
    center(d, 495, "정식 출시 전, 함께해 주실", f(38, False), (206, 220, 214))
    center(d, 552, "첫 테스터 25분을 찾습니다", f(44), WHITE)
    # 선물 강조 박스 (반투명 — softbox로 합성 후 텍스트를 다시 그린다)
    softbox(im, [150, 665, W - 150, 875], radius=30, alpha=26, outline=GOLD, width=3)
    d = ImageDraw.Draw(im)
    center(d, 700, "완주하신 모든 분께", f(34, False), GOLD)
    center(d, 762, "저자 도서 1권 무료 증정", f(46), WHITE)
    brand(d)
    im.save(os.path.join(OUT, "card1.png")); print("card1")

# ── 2) 왜 필요한가 ───────────────────────────────────────
def card2():
    im = bg(CREAM, (233, 240, 236)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 14, H], fill=GREEN)
    d.text((90, 110), "WHY", font=f(28), fill=GREEN)
    d.text((90, 165), "왜 테스터가", font=f(64), fill=INK)
    d.text((90, 248), "필요할까요?", font=f(64), fill=INK)
    lines = [
        ("구글의 새 출시 규정에 따라", False),
        ("신규 앱은 정식 출시 전", False),
        ("14일간의 비공개 테스트를", True),
        ("반드시 거쳐야 합니다.", True),
    ]
    y = 400
    for t, strong in lines:
        d.text((90, y), t, font=f(42, strong), fill=INK if strong else (90, 100, 112))
        y += 66
    d.rounded_rectangle([90, 720, W - 90, 880], radius=24, fill=WHITE, outline=(190, 214, 204), width=2)
    d.text((130, 754), "이 마지막 관문만 넘으면", font=f(34, False), fill=(90, 100, 112))
    d.text((130, 806), "누구나 다운로드할 수 있습니다", font=f(38), fill=GREEN)
    d.text((90, 985), "BIBLY  바이블 인사이트", font=f(26, False), fill=(150, 162, 176))
    im.save(os.path.join(OUT, "card2.png")); print("card2")

# ── 3) 참여 방법 3단계 ───────────────────────────────────
def card3():
    im = bg(NAVY, DEEP); d = ImageDraw.Draw(im)
    center(d, 95, "참여 방법", f(66), WHITE)
    center(d, 185, "3분이면 충분합니다", f(34, False), GOLD)
    steps = [
        ("1", "메일 한 통 보내기", "contact@biblynote.com 으로", "제목 「앱 테스터 신청」 + 내 Gmail 주소"),
        ("2", "링크에서 테스터 되기", "회신으로 참여 링크를 보내드려요", "링크 클릭 → 플레이 스토어에서 설치"),
        ("3", "14일 동안 함께하기", "지우지 말고 가끔 열어 보기", "말씀도 보고 강의도 듣고 — 그게 전부!"),
    ]
    y = 285
    for num, title, s1, s2 in steps:
        softbox(im, [70, y, W - 70, y + 200], radius=26, alpha=22)
        d = ImageDraw.Draw(im)
        d.ellipse([110, y + 60, 190, y + 140], fill=GOLD)
        nf = f(46); d.text((150 - tw(d, num, nf) / 2, y + 74), num, font=nf, fill=DEEP)
        d.text((222, y + 42), title, font=f(42), fill=WHITE)
        d.text((222, y + 100), s1, font=f(29, False), fill=(180, 200, 192))
        d.text((222, y + 142), s2, font=f(29, False), fill=(180, 200, 192))
        y += 225
    brand(d, 985)
    im.save(os.path.join(OUT, "card3.png")); print("card3")

# ── 4) 선물 (도서 3권 표지) ──────────────────────────────
def card4():
    im = bg(DEEP, (6, 42, 30)); d = ImageDraw.Draw(im)
    pill(d, W/2, 80, "완주 감사 선물", f(30), DEEP, GOLD)
    center(d, 175, "저자의 책 1권을", f(60), WHITE)
    center(d, 255, "무료로 보내드립니다", f(60), GOLD)
    center(d, 360, "세 권 중 원하시는 한 권을 고르세요", f(32, False), (170, 195, 185))
    covers = ["mask.jpg", "church.jpg", "mom.jpg"]
    names = ["가면의 시대", "교회를 떠나고서야,\n예수를 만났다", "엄마 향기"]
    bw = 250; gap = 45
    total = bw * 3 + gap * 2
    x = (W - total) / 2
    for i, (c, nm) in enumerate(zip(covers, names)):
        p = os.path.join(ROOT, "images", "books", c)
        if os.path.exists(p):
            cov = Image.open(p).convert("RGB")
            ratio = bw / cov.width
            cov = cov.resize((bw, int(cov.height * ratio)), Image.LANCZOS)
            # 그림자
            sh = Image.new("RGBA", (bw + 40, cov.height + 40), (0, 0, 0, 0))
            ImageDraw.Draw(sh).rounded_rectangle([20, 26, bw + 20, cov.height + 26], radius=6, fill=(0, 0, 0, 130))
            sh = sh.filter(ImageFilter.GaussianBlur(14))
            im.paste(sh, (int(x) - 20, 445), sh)
            im.paste(cov, (int(x), 445))
        yy = 445 + 360
        for j, ln in enumerate(nm.split("\n")):
            fn = f(28, False)
            d.text((x + (bw - tw(d, ln, fn)) / 2, yy + j * 38), ln, font=fn, fill=(210, 228, 220))
        x += bw + gap
    brand(d, 985)
    im.save(os.path.join(OUT, "card4.png")); print("card4")

# ── 5) 마감 CTA ─────────────────────────────────────────
def card5():
    im = bg(GREEN, DEEP); d = ImageDraw.Draw(im)
    center(d, 150, "지금 신청하세요", f(70), WHITE)
    center(d, 255, "선착순 25명 · 마감 시 조기 종료", f(34, False), GOLD)
    d.rounded_rectangle([110, 380, W - 110, 600], radius=30, fill=WHITE)
    center(d, 420, "신청은 메일 한 통", f(36, False), (110, 122, 134))
    center(d, 480, "contact@biblynote.com", f(46), GREEN)
    center(d, 545, "제목 「앱 테스터 신청」 + 내 Gmail 주소", f(28, False), (130, 142, 154))
    center(d, 665, "안드로이드 폰과 Gmail만 있으면", f(34, False), (205, 225, 216))
    center(d, 715, "누구나 참여하실 수 있어요", f(34, False), (205, 225, 216))
    center(d, 815, "말씀으로 시대를 읽다", f(40), GOLD)
    brand(d, 985)
    im.save(os.path.join(OUT, "card5.png")); print("card5")

if __name__ == "__main__":
    card1(); card2(); card3(); card4(); card5()
    print("저장 폴더:", OUT)
