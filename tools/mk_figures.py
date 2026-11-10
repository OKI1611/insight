# -*- coding: utf-8 -*-
"""mk_figures.py — 영문판 인포그래픽 렌더러 (JSON 스펙 → PNG, Kindle 리플로우용)

  스펙: 책원고/영문판_천년왕국/figures/specs/<id>.json
  출력: 책원고/영문판_천년왕국/figures/<id>.png  (폭 1600px, 높이 자동, 흰 바탕 — e-ink 에서도 선명)

  스펙 형식(공통): {"id": "fig-01-1", "type": "cards"|"flow"|"columns", "title": "...", "subtitle": "...",
                   "footer": "...", "items": [...], "columns": 1|2, "note": "..."}
    cards   : items = [{"n": "1", "head": "...", "lines": ["...", "..."], "ref": "Zechariah 14:4", "tag": "optional"}]
              "groups": [{"label": "...", "items": [...]}]  (그룹 띠를 두고 싶을 때, items 대신)
    flow    : items = [{"head": "...", "sub": "...", "lines": [...], "ref": "..."}] 가로 흐름(5개 초과면 두 줄로 꺾음)
              "below": [{"label": "...", "lines": [...]}]  (각 단계 아래 주석, items 와 같은 개수)
    columns : "cols": [{"head": "...", "sub": "...", "rows": [{"label": "...", "text": "..."}]}]  2~3열 비교
    stack   : "blocks": [{"type": "columns", "label": "...", ...}, {"type": "flow", ...}]  블록을 위아래로 쌓음(비교표+흐름도 등)
  실행: python tools/mk_figures.py [fig-01-1 ...]   (인수 없으면 specs/ 전체)
"""
import io, os, sys, json, glob, textwrap
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(ROOT, "책원고", "영문판_천년왕국", "figures")
SPECS = os.path.join(BASE, "specs")
FDIR = os.path.join(ROOT, "tools", "fonts")

NAVY = (16, 27, 58); NAVY2 = (26, 42, 82); GOLD = (201, 162, 75); GOLDD = (150, 112, 40)
INK = (30, 34, 40); GRAY = (108, 116, 130); LGRAY = (225, 221, 210); CREAM = (250, 247, 239)
WHITE = (255, 255, 255); SAND = (240, 230, 205)

W = 1600; M = 56          # 폭·바깥 여백

_fc = {}
def F(kind, size):
    k = (kind, size)
    if k not in _fc:
        p = {"r": "Pretendard-Regular.ttf", "b": "Pretendard-Bold.ttf", "x": "Pretendard-Black.ttf",
             "s": "NotoSerif-Regular.ttf", "sb": "NotoSerifKR-Bold.ttf"}[kind]
        _fc[k] = ImageFont.truetype(os.path.join(FDIR, p), size)
    return _fc[k]

class Canvas:
    """높이를 모르는 채로 그리기 위해 넉넉한 캔버스에 그린 뒤 잘라 낸다."""
    def __init__(self, h=6000):
        self.im = Image.new("RGB", (W, h), WHITE); self.d = ImageDraw.Draw(self.im); self.y = 0
    def crop(self, bottom_pad=36):
        return self.im.crop((0, 0, W, int(self.y + bottom_pad)))

def wrap(d, text, font, width):
    """픽셀 폭 기준 줄바꿈"""
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font) <= width: cur = t
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines or [""]

def draw_text(d, x, y, text, font, fill, width, leading=1.3, align="left"):
    """줄바꿈 텍스트를 그리고 끝 y 를 돌려준다"""
    lh = int(font.size * leading)
    for ln in wrap(d, text, font, width):
        tx = x
        if align == "center": tx = x + (width - d.textlength(ln, font=font)) / 2
        elif align == "right": tx = x + width - d.textlength(ln, font=font)
        d.text((tx, y), ln, font=font, fill=fill); y += lh
    return y

def text_height(d, text, font, width, leading=1.3):
    return len(wrap(d, text, font, width)) * int(font.size * leading)

def header(c, spec):
    d = c.d
    d.rectangle([0, 0, W, 10], fill=GOLD)
    y = 34
    y = draw_text(d, M, y, spec["title"].upper(), F("x", 46), NAVY, W - 2 * M, 1.15)
    if spec.get("subtitle"):
        y += 6
        y = draw_text(d, M, y, spec["subtitle"], F("s", 27), GRAY, W - 2 * M, 1.3)
    y += 18
    d.rectangle([M, y, M + 90, y + 5], fill=GOLD)
    c.y = y + 30

def footer(c, spec):
    if not spec.get("footer"): return
    d = c.d; y = c.y + 10
    h = text_height(d, spec["footer"], F("b", 27), W - 2 * M - 60, 1.35) + 34
    d.rounded_rectangle([M, y, W - M, y + h], radius=14, fill=NAVY)
    draw_text(d, M + 30, y + 17, spec["footer"], F("b", 27), WHITE, W - 2 * M - 60, 1.35)
    c.y = y + h
    if spec.get("note"):
        c.y = draw_text(d, M, c.y + 14, spec["note"], F("r", 21), GRAY, W - 2 * M, 1.3)

def numbered_circle(d, x, y, n, r=26):
    d.ellipse([x, y, x + 2 * r, y + 2 * r], fill=GOLD)
    f = F("x", 30 if len(str(n)) < 2 else 24)
    tw = d.textlength(str(n), font=f)
    d.text((x + r - tw / 2, y + r - f.size * 0.62), str(n), font=f, fill=NAVY)

def card_block(d, x, y, w, it, head_font=F("b", 30), body_font=F("r", 24), ref_font=F("s", 21), min_h=0):
    """한 장의 카드. 끝 y 반환. min_h: 같은 행 카드와 바닥을 맞출 때 바탕색까지 채우기 위한 최소 높이."""
    pad = 22
    inner = w - 2 * pad
    hx = x + pad; tx = hx
    if it.get("n") not in (None, ""):
        tx = hx + 72
    hy = y + pad
    # 높이 계산
    th = text_height(d, it.get("head", ""), head_font, inner - (tx - hx), 1.2)
    for ln in it.get("lines", []):
        th += text_height(d, "• " + ln, body_font, inner - (tx - hx), 1.3) + 4
    if it.get("ref"): th += text_height(d, it["ref"], ref_font, inner - (tx - hx), 1.3) + 6
    h = max(th + 2 * pad + 4, min_h)
    d.rounded_rectangle([x, y, x + w, y + h], radius=16, fill=CREAM, outline=LGRAY, width=2)
    if it.get("n") not in (None, ""): numbered_circle(d, hx, hy - 2, it["n"])
    yy = draw_text(d, tx, hy, it.get("head", ""), head_font, NAVY, inner - (tx - hx), 1.2)
    for ln in it.get("lines", []):
        yy = draw_text(d, tx, yy + 4, "• " + ln, body_font, INK, inner - (tx - hx), 1.3)
    if it.get("ref"):
        yy = draw_text(d, tx, yy + 6, it["ref"], ref_font, GOLDD, inner - (tx - hx), 1.3)
    if it.get("tag"):
        tf = F("b", 19); tw = d.textlength(it["tag"], font=tf) + 22
        d.rounded_rectangle([x + w - pad - tw, y + 12, x + w - pad, y + 12 + 32], radius=16, fill=SAND)
        d.text((x + w - pad - tw + 11, y + 17), it["tag"], font=tf, fill=GOLDD)
    return y + h

def render_cards(c, spec):
    d = c.d
    cols = int(spec.get("columns", 1)); gap = 24
    cw = (W - 2 * M - gap * (cols - 1)) / cols
    groups = spec.get("groups") or [{"label": None, "items": spec.get("items", [])}]
    for g in groups:
        if g.get("label"):
            y = c.y + 8
            d.rounded_rectangle([M, y, W - M, y + 50], radius=10, fill=NAVY2)
            d.text((M + 20, y + 11), g["label"], font=F("b", 25), fill=WHITE)
            c.y = y + 64
        items = g["items"]
        for i in range(0, len(items), cols):
            row = items[i:i + cols]
            # 같은 행은 높이를 맞춘다: 먼저 임시 캔버스로 높이 측정
            hs = []
            for j, it in enumerate(row):
                tmp = Image.new("RGB", (W, 3000), WHITE); td = ImageDraw.Draw(tmp)
                hs.append(card_block(td, 0, 0, cw, it))
            h = max(hs)
            for j, it in enumerate(row):
                x = M + j * (cw + gap)
                card_block(d, x, c.y, cw, it, min_h=h)   # 같은 행 카드 바닥 맞춤(바탕색까지 채움)
            c.y += h + gap

def arrow_right(d, x, y, length=40, color=GOLD):
    d.line([x, y, x + length, y], fill=color, width=6)
    d.polygon([(x + length, y), (x + length - 14, y - 10), (x + length - 14, y + 10)], fill=color)

def arrow_down(d, x, y, length=36, color=GOLD):
    d.line([x, y, x, y + length], fill=color, width=6)
    d.polygon([(x, y + length), (x - 10, y + length - 14), (x + 10, y + length - 14)], fill=color)

def render_flow(c, spec):
    d = c.d
    items = spec["items"]; n = len(items)
    per_row = n if n <= 5 else (n + 1) // 2
    gap = 46
    bw = (W - 2 * M - gap * (per_row - 1)) / per_row
    below = spec.get("below")
    idx = 0
    while idx < n:
        row = items[idx: idx + per_row]
        # 높이 측정: 실제 그리기 함수를 임시 캔버스에 돌려 정확히 잰다
        def box(d, x, y, it, k, draw=True):
            yy = draw_text(d, x + 62, y + 14, it.get("head", ""), F("b", 27), WHITE, bw - 76, 1.2)
            if it.get("sub"): yy = draw_text(d, x + 14, yy + 6, it["sub"], F("r", 20), (205, 215, 238), bw - 28, 1.25)
            for ln in it.get("lines", []): yy = draw_text(d, x + 14, yy + 3, "• " + ln, F("r", 21), WHITE, bw - 28, 1.3)
            if it.get("ref"): yy = draw_text(d, x + 14, yy + 6, it["ref"], F("s", 19), (228, 192, 122), bw - 28, 1.3)
            return yy + 16 - y
        tmp = ImageDraw.Draw(Image.new("RGB", (W, 3000), WHITE))
        hs = [max(box(tmp, 0, 0, it, 0), 90) for it in row]
        H = max(hs)
        for j, it in enumerate(row):
            x = M + j * (bw + gap); y = c.y
            d.rounded_rectangle([x, y, x + bw, y + H], radius=14, fill=NAVY if j % 2 == 0 else NAVY2)
            k = idx + j + 1
            numbered_circle(d, x + 12, y + 12, k, r=20)
            box(d, x, y, it, k)
            if j < len(row) - 1: arrow_right(d, x + bw + 3, y + H / 2)
        c.y += H
        if below:
            bh = 0
            for j in range(len(row)):
                b = below[idx + j] if idx + j < len(below) else None
                if not b: continue
                h = 10
                if b.get("label"): h += text_height(d, b["label"], F("b", 21), bw - 10, 1.2) + 4
                for ln in b.get("lines", []): h += text_height(d, ln, F("r", 20), bw - 10, 1.3) + 2
                bh = max(bh, h)
            for j in range(len(row)):
                b = below[idx + j] if idx + j < len(below) else None
                if not b: continue
                x = M + j * (bw + gap); y = c.y + 8
                d.line([x + bw / 2, c.y, x + bw / 2, y + 6], fill=LGRAY, width=3)
                yy = y + 10
                if b.get("label"): yy = draw_text(d, x + 4, yy, b["label"], F("b", 21), NAVY, bw - 10, 1.2) + 4
                for ln in b.get("lines", []): yy = draw_text(d, x + 4, yy, ln, F("r", 20), INK, bw - 10, 1.3) + 2
            c.y += bh + 14
        idx += per_row
        if idx < n:
            arrow_down(d, W - M - 24, c.y + 6); c.y += 56
    c.y += 10

def render_columns(c, spec):
    d = c.d
    cols = spec["cols"]; n = len(cols); gap = 28
    cw = (W - 2 * M - gap * (n - 1)) / n
    # 헤더
    hh = 0
    for col in cols:
        h = text_height(d, col.get("head", ""), F("b", 29), cw - 30, 1.2) + 24
        if col.get("sub"): h += text_height(d, col["sub"], F("r", 20), cw - 30, 1.25) + 4
        hh = max(hh, h)
    for j, col in enumerate(cols):
        x = M + j * (cw + gap)
        d.rounded_rectangle([x, c.y, x + cw, c.y + hh], radius=12, fill=NAVY if j % 2 == 0 else GOLDD)
        yy = draw_text(d, x + 15, c.y + 12, col.get("head", ""), F("b", 29), WHITE, cw - 30, 1.2, "center")
        if col.get("sub"): draw_text(d, x + 15, yy + 4, col["sub"], F("r", 20), (235, 235, 235), cw - 30, 1.25, "center")
    c.y += hh + 10
    rows = max(len(col.get("rows", [])) for col in cols)
    for r in range(rows):
        rh = 0
        cells = []
        for col in cols:
            cell = col["rows"][r] if r < len(col["rows"]) else {"label": "", "text": ""}
            cells.append(cell)
            h = 16
            if cell.get("label"): h += text_height(d, cell["label"], F("b", 21), cw - 30, 1.2) + 2
            h += text_height(d, cell.get("text", ""), F("r", 23), cw - 30, 1.3)
            rh = max(rh, h + 10)
        for j, cell in enumerate(cells):
            x = M + j * (cw + gap)
            d.rounded_rectangle([x, c.y, x + cw, c.y + rh], radius=10, fill=CREAM if r % 2 == 0 else WHITE, outline=LGRAY, width=2)
            yy = c.y + 10
            if cell.get("label"): yy = draw_text(d, x + 15, yy, cell["label"], F("b", 21), GOLDD, cw - 30, 1.2) + 2
            draw_text(d, x + 15, yy, cell.get("text", ""), F("r", 23), INK, cw - 30, 1.3)
        c.y += rh + 8
    c.y += 8

def render_stack(c, spec):
    """여러 블록을 위아래로 쌓는다: "blocks": [{"type": "columns"|"flow"|"cards", "label": "...", ...}]"""
    d = c.d
    for b in spec["blocks"]:
        if b.get("label"):
            y = c.y + 6
            d.rounded_rectangle([M, y, W - M, y + 48], radius=10, fill=GOLDD)
            d.text((M + 18, y + 10), b["label"], font=F("b", 24), fill=WHITE)
            c.y = y + 62
        RENDER[b["type"]](c, b)
        c.y += 10

RENDER = {"cards": render_cards, "flow": render_flow, "columns": render_columns}
RENDER["stack"] = render_stack

def build(spec):
    c = Canvas()
    header(c, spec)
    RENDER[spec["type"]](c, spec)
    footer(c, spec)
    im = c.crop()
    out = os.path.join(BASE, spec["id"] + ".png")
    im.save(out, optimize=True)
    return out, im.size

def main():
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass
    ids = sys.argv[1:]
    paths = [os.path.join(SPECS, i + ".json") for i in ids] if ids else sorted(glob.glob(os.path.join(SPECS, "*.json")))
    for p in paths:
        spec = json.load(io.open(p, encoding="utf-8"))
        out, size = build(spec)
        print("%-12s %s  %dx%d" % (spec["id"], spec["type"], size[0], size[1]))

if __name__ == "__main__":
    main()
