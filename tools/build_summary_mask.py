# -*- coding: utf-8 -*-
"""『가면의 시대』 무료 핵심요약 PDF 생성기

  · A4(210×297) · Noto Serif KR(SIL OFL, fsType=0) 서브셋 임베딩
  · 웹 무료 배포용 — 부크크 폰트·로고·판권 정보 일절 미사용
  · tools/build_summary_pdf.py(전작 요약본)의 구조를 따름

  실행: python tools/build_summary_mask.py [원고.txt]
  출력: files/가면의시대-핵심메시지요약.pdf
"""
import os, sys, io
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph,
                                Spacer, PageBreak, PageBreakIfNotEmpty, NextPageTemplate,
                                KeepTogether, Table, TableStyle, Flowable)

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FDIR = os.path.join(ROOT, "tools", "fonts")
pdfmetrics.registerFont(TTFont("NSK",  os.path.join(FDIR, "NotoSerifKR-Regular.ttf")))
pdfmetrics.registerFont(TTFont("NSKB", os.path.join(FDIR, "NotoSerifKR-Bold.ttf")))
pdfmetrics.registerFontFamily("NSK", normal="NSK", bold="NSKB")

# 팔레트 — 책 표지(페리윙클 블루) 계열로 통일
DEEPBG = HexColor("#3E4B94")     # 표지 바탕
CREAM  = HexColor("#F7F6F2")
GOLD   = HexColor("#A9B4E2")     # 표지 위 포인트(라이트 블루)
BLUE   = HexColor("#2E3F87")     # 제목·강조
PERI   = HexColor("#5B6EC0")     # 보조 포인트
INK    = HexColor("#24282F")
GRAY   = HexColor("#8A8A8A")
RULE   = HexColor("#C8CDE0")
BOXBG  = HexColor("#F2F4FA")
BOXLN  = HexColor("#D3D9EC")
KEYBG  = HexColor("#EDF0F9")

PAGE = (210*mm, 297*mm)          # A4 세로
ML = MR = 24*mm
MT = 24*mm
MB = 22*mm
CW = PAGE[0] - ML - MR           # 본문 폭

TITLE    = "가면의 시대"
SUBTITLE = "핵심 메시지 요약본"
AUTHOR   = "오광일"
RUNHEAD  = "가면의 시대 · 핵심 요약"

def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

# ───────────────────────── 스타일 ─────────────────────────
S = {}
S["body"] = ParagraphStyle("body", fontName="NSK", fontSize=10.4, leading=19,
                           alignment=TA_JUSTIFY, textColor=INK, spaceAfter=7,
                           wordWrap="CJK")                      # ★자간 균일
S["h1"]   = ParagraphStyle("h1", fontName="NSKB", fontSize=18, leading=27,
                           textColor=BLUE, spaceBefore=0, spaceAfter=3, wordWrap="CJK")
S["h2"]   = ParagraphStyle("h2", fontName="NSKB", fontSize=12.4, leading=19,
                           textColor=BLUE, spaceBefore=14, spaceAfter=5, wordWrap="CJK")
S["quote"]= ParagraphStyle("quote", fontName="NSK", fontSize=10.6, leading=18.5,
                           textColor=HexColor("#43496A"), leftIndent=9*mm, rightIndent=3*mm,
                           spaceBefore=6, spaceAfter=8, wordWrap="CJK")
S["key"]  = ParagraphStyle("key", fontName="NSKB", fontSize=11.2, leading=18.5,
                           textColor=BLUE, alignment=TA_CENTER, wordWrap="CJK")
S["bullet"]= ParagraphStyle("bul", fontName="NSK", fontSize=10, leading=17,
                           textColor=INK, leftIndent=6*mm, firstLineIndent=-4*mm,
                           spaceAfter=3, alignment=TA_LEFT, wordWrap="CJK")
S["boxt"] = ParagraphStyle("boxt", fontName="NSKB", fontSize=10.4, leading=16,
                           textColor=HexColor("#2E3F87"), spaceAfter=4, wordWrap="CJK")
S["boxb"] = ParagraphStyle("boxb", fontName="NSK", fontSize=9.8, leading=16.4,
                           textColor=INK, alignment=TA_JUSTIFY, spaceAfter=3, wordWrap="CJK")
S["chk"]  = ParagraphStyle("chk", fontName="NSKB", fontSize=10.8, leading=17,
                           textColor=BLUE, spaceBefore=10, spaceAfter=3, wordWrap="CJK")
S["note"] = ParagraphStyle("note", fontName="NSK", fontSize=9.6, leading=16,
                           textColor=GRAY, alignment=TA_CENTER, spaceBefore=9, wordWrap="CJK")

class Rule(Flowable):
    """가로 구분선"""
    def __init__(self, w, color=RULE, thick=0.6, gap=3):
        Flowable.__init__(self); self.w=w; self.color=color; self.thick=thick; self.gap=gap
    def wrap(self, aw, ah): return (self.w, self.thick + self.gap*2)
    def draw(self):
        self.canv.setStrokeColor(self.color); self.canv.setLineWidth(self.thick)
        self.canv.line(0, self.gap, self.w, self.gap)

class KeyLine(Flowable):
    """핵심 한 줄 — 연블루 배경 강조 블록"""
    def __init__(self, text, w):
        Flowable.__init__(self); self.p = Paragraph(esc(text), S["key"]); self.w = w
    def wrap(self, aw, ah):
        pw, ph = self.p.wrap(self.w - 14*mm, ah)
        self.h = ph + 12*mm
        return (self.w, self.h)
    def draw(self):
        c = self.canv
        c.setFillColor(KEYBG); c.setStrokeColor(HexColor("#C2CBE8")); c.setLineWidth(0.7)
        c.roundRect(0, 3*mm, self.w, self.h - 5*mm, 2.4*mm, stroke=1, fill=1)
        c.setFillColor(PERI)
        c.rect(0, 3*mm, 1.8*mm, self.h - 5*mm, stroke=0, fill=1)
        self.p.drawOn(c, 7*mm, self.h - 4.6*mm - self.p.height)

def quote_block(text):
    """인용 — 좌측 블루 라인"""
    p = Paragraph(esc(text), S["quote"])
    t = Table([[p]], colWidths=[CW])
    t.setStyle(TableStyle([
        ("LINEBEFORE", (0,0), (0,0), 1.8, PERI),
        ("LEFTPADDING", (0,0), (-1,-1), 0), ("RIGHTPADDING", (0,0), (-1,-1), 0),
        ("TOPPADDING", (0,0), (-1,-1), 3), ("BOTTOMPADDING", (0,0), (-1,-1), 3),
    ]))
    return t

def box_block(title, lines):
    """음영 박스"""
    inner = []
    if title:
        inner.append(Paragraph(esc(title), S["boxt"]))
    for ln in lines:
        inner.append(Paragraph(esc(ln), S["boxb"]))
    t = Table([[inner]], colWidths=[CW])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), BOXBG),
        ("BOX", (0,0), (-1,-1), 0.7, BOXLN),
        ("LEFTPADDING", (0,0), (-1,-1), 6*mm), ("RIGHTPADDING", (0,0), (-1,-1), 6*mm),
        ("TOPPADDING", (0,0), (-1,-1), 4.5*mm), ("BOTTOMPADDING", (0,0), (-1,-1), 4*mm),
    ]))
    return t

# ───────────────────────── 표지 ─────────────────────────
def draw_star(c, cx, cy, r, color, glow):
    """광야의 별 — 책 도비라와 같은 모티프"""
    c.saveState()
    c.setFillColor(glow)
    for rr, a in [(r*3.2, 0.10), (r*2.0, 0.18)]:
        c.setFillColor(glow); c.setFillAlpha(a)
        c.circle(cx, cy, rr, stroke=0, fill=1)
    c.setFillAlpha(1)
    c.setFillColor(color); c.circle(cx, cy, r*0.42, stroke=0, fill=1)
    c.setStrokeColor(color); c.setLineWidth(0.9)
    c.setStrokeAlpha(0.55)
    c.line(cx - r*2.4, cy, cx + r*2.4, cy)
    c.line(cx, cy - r*2.4, cx, cy + r*2.4)
    c.restoreState()

def tracked(c, cx, y, text, font, size, tracking, color):
    """자간(letter-spacing) 적용 가운데 정렬 — textobject 사용"""
    w = c.stringWidth(text, font, size) + tracking * max(0, len(text) - 1)
    t = c.beginText(cx - w/2, y)
    t.setFont(font, size); t.setFillColor(color); t.setCharSpace(tracking)
    t.textOut(text)
    c.drawText(t)
    # Tc(자간)는 텍스트 상태로 남아 이후 drawString까지 오염시킨다 → 즉시 0으로 되돌림
    r = c.beginText(0, 0); r.setCharSpace(0); r.textOut("")
    c.drawText(r)

def draw_cover(c, doc):
    w, h = PAGE
    c.setFillColor(DEEPBG); c.rect(0, 0, w, h, stroke=0, fill=1)
    cx = w/2
    # 상단 포인트 라인
    c.setFillColor(GOLD); c.rect(cx-11*mm, h-36*mm, 22*mm, 0.8, stroke=0, fill=1)
    # 영문 캡션(자간)
    tracked(c, cx, h-44*mm, "THE AGE OF MASKS", "NSK", 9, 3.4, GOLD)
    # 부제
    c.setFillColor(HexColor("#CFD6EE")); c.setFont("NSK", 11)
    c.drawCentredString(cx, h-56*mm, "정의가 지는 세상에서 끝내 나를 지키는 법")
    # 제목
    c.setFillColor(CREAM); c.setFont("NSKB", 34)
    c.drawCentredString(cx, h-78*mm, "가면의 시대")
    # 요약본 배지
    tracked(c, cx, h-95*mm, "핵심 메시지 요약본", "NSKB", 12, 3.0, GOLD)
    c.setStrokeColor(GOLD); c.setLineWidth(0.6)
    c.line(cx-28*mm, h-100*mm, cx+28*mm, h-100*mm)
    # 별 심볼
    draw_star(c, cx, h-134*mm, 4.2*mm, CREAM, HexColor("#AEB9E8"))
    # 하단
    c.setFillColor(CREAM); c.setFont("NSKB", 15)
    c.drawCentredString(cx, 62*mm, "당신은 틀리지 않았다")
    c.setFillColor(HexColor("#CFD6EE")); c.setFont("NSK", 10)
    c.drawCentredString(cx, 46*mm, "오광일 지음")
    c.setFillColor(HexColor("#9AA6D4")); c.setFont("NSK", 8.4)
    c.drawCentredString(cx, 30*mm, "바이블 인사이트 · biblynote.com")

def draw_body(c, doc):
    w, h = PAGE
    if doc.page <= 1:
        return
    c.setStrokeColor(RULE); c.setLineWidth(0.4)
    c.line(ML, MB - 7*mm, w - MR, MB - 7*mm)
    c.setFont("NSK", 8); c.setFillColor(GRAY)
    c.drawString(ML, MB - 12*mm, RUNHEAD)
    c.drawRightString(w - MR, MB - 12*mm, str(doc.page - 1))

# ───────────────────────── 원고 파서 ─────────────────────────
def parse(path):
    story = []
    box = None; boxlines = []
    first_h1 = True
    for raw in io.open(path, encoding="utf-8").read().split("\n"):
        s = raw.strip()
        if not s:
            continue
        if s.startswith(("#T ", "#ST ", "#SS ", "#AU ")):
            continue                                   # 표지는 캔버스로 직접 그림
        if s.startswith("#B "):
            box = s[3:].strip(); boxlines = []; continue
        if s.startswith("#EB"):
            story.append(Spacer(1, 3))
            story.append(box_block(box, boxlines))
            story.append(Spacer(1, 5)); box = None; continue
        if box is not None:
            boxlines.append(s); continue

        if s.startswith("#H1 "):
            if not first_h1:
                # 페이지 끝에 남은 Spacer가 다음 장으로 넘어가면 그 페이지가
                # '비어 있지 않음'으로 판정되어 빈 페이지가 생긴다 → 먼저 제거
                while story and isinstance(story[-1], Spacer):
                    story.pop()
                story.append(PageBreakIfNotEmpty())
            first_h1 = False
            story.append(Paragraph(esc(s[4:]), S["h1"]))
            story.append(Rule(CW, PERI, 1.4, 4))
            story.append(Spacer(1, 7))
        elif s.startswith("#H2 "):
            story.append(KeepTogether([Paragraph(esc(s[4:]), S["h2"]), Spacer(1, 1)]))
        elif s.startswith("#K "):
            story.append(Spacer(1, 4)); story.append(KeyLine(s[3:], CW)); story.append(Spacer(1, 6))
        elif s.startswith("#Q "):
            story.append(quote_block(s[3:]))
            story.append(Spacer(1, 7))
        elif s.startswith("#L "):
            story.append(Paragraph("·&nbsp;&nbsp;" + esc(s[3:]), S["bullet"]))
        elif s.startswith("#C "):
            story.append(Paragraph(esc(s[3:]), S["chk"]))
        elif s.startswith("#N "):
            story.append(Paragraph(esc(s[3:]), S["note"]))
        else:
            story.append(Paragraph(esc(s), S["body"]))
    return story

def build(src, out):
    doc = BaseDocTemplate(out, pagesize=PAGE,
                          leftMargin=ML, rightMargin=MR, topMargin=MT, bottomMargin=MB,
                          title="%s — %s" % (TITLE, SUBTITLE),
                          author=AUTHOR,
                          subject="바이블 인사이트(biblynote.com) 무료 배포 자료",
                          creator="바이블 인사이트 · biblynote.com")
    fr_cover = Frame(0, 0, PAGE[0], PAGE[1], id="c",
                     leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    fr_body  = Frame(ML, MB, CW, PAGE[1]-MT-MB, id="b",
                     leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates([
        PageTemplate(id="cover", frames=[fr_cover], onPage=draw_cover),
        PageTemplate(id="body",  frames=[fr_body],  onPage=draw_body),
    ])
    story = [NextPageTemplate("body"), PageBreak()] + parse(src)
    doc.build(story)
    print("생성:", out)
    print("  %d쪽 · %.0f KB" % (doc.page, os.path.getsize(out)/1024))
    return out

if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "tools", "summary_src_mask.txt")
    out = os.path.join(ROOT, "files", "가면의시대-핵심메시지요약.pdf")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    build(src, out)
