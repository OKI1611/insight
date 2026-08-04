# -*- coding: utf-8 -*-
"""웹용 로고 자산 생성 — BIBLE INSIGHT DB 모노그램 (역할 분리안, 2026-08-05 확정)

  역할 분리: 헤더·푸터·인쇄물·공유카드 = 새 DB 모노그램
             파비콘·앱아이콘·엠블럼 = 기존 책 심볼 유지(소형 가독성)

  산출(images/):
    logo-heritage-wide.png    가로형 록업, 흰 배경용 네이비 반전, 투명 배경 (헤더·푸터·본문)
    logo-heritage-square.png  정사각 512px, 네이비 배경 원본 축소 (JSON-LD·프로필)
    og-cover.png              1200×630 공유 카드 재생성 (?v=7)

  실행: python tools/make_logo_web.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC  = os.path.join(ROOT, "images", "brand")
IMG  = os.path.join(ROOT, "images")

from build_blog_brand import (SQ, HZ, content_box, cutout, to_light, monogram,
                              fit, glow_bg, NAVY, CREAM, GOLD)

MG = r"C:\Windows\Fonts\malgun.ttf"


def save(im, path, **kw):
    im.save(path, "PNG", optimize=True, **kw)
    print("  %-28s %-12s %.0fKB" % (os.path.basename(path), "%dx%d" % im.size,
                                    os.path.getsize(path) / 1024))


# ── ① 가로형 록업 — 직접 조판(2026-08-05 사용자 피드백 반영) ──
#    원본 wide 로고의 영문이 가늘어 헤더에서 약해 보임 →
#    DB 마크 + 굵은 세리프 "BIBLE INSIGHT" + 아랫줄 한글 "바이블 인사이트" 소자.
FB_TTF = os.path.join(ROOT, "tools", "fonts", "NotoSerifKR-Bold.ttf")
FR_TTF = os.path.join(ROOT, "tools", "fonts", "NotoSerifKR-Regular.ttf")

def _tracked(draw, xy, txt, font, fill, tracking):
    """자간(tracking px)을 주며 한 글자씩 그리기 — 반환: 전체 폭"""
    x, y = xy
    for ch in txt:
        draw.text((x, y), ch, font=font, fill=fill)
        x += draw.textlength(ch, font=font) + tracking
    return x - tracking - xy[0]

def compose_lockup(dark_bg=False, h=200):
    """마크 + BIBLE INSIGHT(굵게) + 바이블 인사이트(소자) 2줄 록업.
       dark_bg=False → 흰 배경용(네이비/muted), True → 네이비 배경용(크림)."""
    mark = (cutout if dark_bg else to_light)(monogram(SQ))
    mark = fit(mark, h=h)
    c_main = CREAM if dark_bg else NAVY
    c_sub  = (196, 205, 224) if dark_bg else (98, 112, 140)
    f_en = ImageFont.truetype(FB_TTF, int(h * 0.40))       # 굵은 세리프 영문
    f_ko = ImageFont.truetype(FR_TTF, int(h * 0.155))      # 한글 소자
    tr_en = int(h * 0.055); tr_ko = int(h * 0.09)

    tmp = Image.new("RGBA", (10, 10)); dt = ImageDraw.Draw(tmp)
    w_en = sum(dt.textlength(c, font=f_en) + tr_en for c in "BIBLE INSIGHT") - tr_en
    w_ko = sum(dt.textlength(c, font=f_ko) + tr_ko for c in "바이블 인사이트") - tr_ko
    gap = int(h * 0.22)
    W = mark.width + gap + int(max(w_en, w_ko)) + 4
    im = Image.new("RGBA", (W, h), (0, 0, 0, 0))
    im.paste(mark, (0, 0), mark)
    d = ImageDraw.Draw(im)
    tx = mark.width + gap
    y_en = int(h * 0.16)
    _tracked(d, (tx, y_en), "BIBLE INSIGHT", f_en, c_main, tr_en)
    y_ko = y_en + int(h * 0.40 * 1.38)
    _tracked(d, (tx + int(h * 0.02), y_ko), "바이블 인사이트", f_ko, c_sub, tr_ko)
    return im

def wide_light():
    save(compose_lockup(dark_bg=False, h=200), os.path.join(IMG, "logo-heritage-wide.png"))


# ── ② 정사각 512 (JSON-LD Organization.logo 용) ─────────────
def square():
    im = SQ.resize((512, 512), Image.LANCZOS)
    save(im, os.path.join(IMG, "logo-heritage-square.png"))


# ── ③ og-cover 1200×630 ─────────────────────────────────────
def og_cover():
    W, H = 1200, 630
    im = glow_bg(W, H)
    lock = compose_lockup(dark_bg=True, h=200)
    lock = fit(lock, w=640)
    im.paste(lock, ((W - lock.width) // 2, 150), lock)
    d = ImageDraw.Draw(im)
    y = 150 + lock.height + 42
    d.line([(W//2 - 40, y), (W//2 + 40, y)], fill=GOLD, width=2)
    f1 = ImageFont.truetype(MG, 30)
    t1 = "말씀으로 시대를 읽습니다"
    d.text(((W - d.textlength(t1, font=f1)) / 2, y + 22), t1, font=f1, fill=(214, 223, 238))
    f2 = ImageFont.truetype(MG, 22)
    t2 = "성경 읽기 · 강의 320편 · 성경사전 5,453항목  |  biblynote.com"
    d.text(((W - d.textlength(t2, font=f2)) / 2, y + 74), t2, font=f2, fill=(136, 158, 196))
    save(im.convert("RGB"), os.path.join(IMG, "og-cover.png"))


if __name__ == "__main__":
    print("웹 로고 자산 생성 →", IMG)
    wide_light(); square(); og_cover()
