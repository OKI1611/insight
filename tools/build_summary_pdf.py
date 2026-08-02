# -*- coding: utf-8 -*-
"""『교회를 떠나고서야, 예수를 만났다』 무료 핵심요약 PDF 생성기

  · A5(148×210) · Noto Serif KR(SIL OFL) 서브셋 임베딩
  · 웹 무료 배포용 — 부크크 폰트·로고·판권 정보 일절 미사용
  실행: python tools/build_summary_pdf.py [원고.txt]
  출력: files/교회를떠나고서야-핵심요약.pdf
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

# 팔레트 — 책 표지(딥그린) + 사이트(그린) 통일
DEEPBG = HexColor("#21342A")
CREAM  = HexColor("#F5F0E4")
GOLD   = HexColor("#C6A86C")
GREEN  = HexColor("#00593C")
INK    = HexColor("#232D28")
GRAY   = HexColor("#8A8A8A")
RULE   = HexColor("#C9C2B4")
BOXBG  = HexColor("#F4F2EA")
BOXLN  = HexColor("#D8D2BE")
KEYBG  = HexColor("#EDF2EE")

PAGE = (148*mm, 210*mm)
ML = MR = 17*mm
MT = 18*mm
MB = 16*mm
CW = PAGE[0] - ML - MR          # 본문 폭

TITLE    = "교회를 떠나고서야, 예수를 만났다"
SUBTITLE = "핵심 메시지 요약본"
AUTHOR   = "오광일"

def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

# ───────────────────────── 스타일 ─────────────────────────
S = {}
S["body"] = ParagraphStyle("body", fontName="NSK", fontSize=10, leading=17.6,
                           alignment=TA_JUSTIFY, textColor=INK, spaceAfter=6.5,
                           wordWrap="CJK")                      # ★자간 균일
S["h1"]   = ParagraphStyle("h1", fontName="NSKB", fontSize=17, leading=25,
                           textColor=GREEN, spaceBefore=0, spaceAfter=3, wordWrap="CJK")
S["h2"]   = ParagraphStyle("h2", fontName="NSKB", fontSize=11.8, leading=18,
                           textColor=GREEN, spaceBefore=13, spaceAfter=5, wordWrap="CJK")
S["quote"]= ParagraphStyle("quote", fontName="NSK", fontSize=10.2, leading=17.5,
                           textColor=HexColor("#4A5A50"), leftIndent=8*mm, rightIndent=3*mm,
                           spaceBefore=6, spaceAfter=8, wordWrap="CJK")
S["key"]  = ParagraphStyle("key", fontName="NSKB", fontSize=10.8, leading=17.5,
                           textColor=GREEN, alignment=TA_CENTER, wordWrap="CJK")
S["bullet"]= ParagraphStyle("bul", fontName="NSK", fontSize=9.7, leading=15.6,
                           textColor=INK, leftIndent=5.4*mm, firstLineIndent=-3.6*mm,
                           spaceAfter=2.6, alignment=TA_LEFT, wordWrap="CJK")
S["boxt"] = ParagraphStyle("boxt", fontName="NSKB", fontSize=10, leading=15,
                           textColor=HexColor("#5A4A2A"), spaceAfter=3.5, wordWrap="CJK")
S["boxb"] = ParagraphStyle("boxb", fontName="NSK", fontSize=9.3, leading=15.2,
                           textColor=INK, alignment=TA_JUSTIFY, spaceAfter=3, wordWrap="CJK")
S["chk"]  = ParagraphStyle("chk", fontName="NSKB", fontSize=10.2, leading=16,
                           textColor=GREEN, spaceBefore=9, spaceAfter=3, wordWrap="CJK")
S["note"] = ParagraphStyle("note", fontName="NSK", fontSize=9.2, leading=15,
                           textColor=GRAY, alignment=TA_CENTER, spaceBefore=8, wordWrap="CJK")

class Rule(Flowable):
    """가로 구분선"""
    def __init__(self, w, color=RULE, thick=0.6, gap=3):
        Flowable.__init__(self); self.w=w; self.color=color; self.thick=thick; self.gap=gap
    def wrap(self, aw, ah): return (self.w, self.thick + self.gap*2)
    def draw(self):
        self.canv.setStrokeColor(self.color); self.canv.setLineWidth(self.thick)
        self.canv.line(0, self.gap, self.w, self.gap)

class KeyLine(Flowable):
    """핵심 한 줄 — 연녹색 배경 강조 블록"""
    def __init__(self, text, w):
        Flowable.__init__(self); self.p = Paragraph(esc(text), S["key"]); self.w = w
    def wrap(self, aw, ah):
        pw, ph = self.p.wrap(self.w - 12*mm, ah)
        self.h = ph + 11*mm
        return (self.w, self.h)
    def draw(self):
        c = self.canv
        c.setFillColor(KEYBG); c.setStrokeColor(HexColor("#BFD3C6")); c.setLineWidth(0.7)
        c.roundRect(0, 3*mm, self.w, self.h - 5*mm, 2.2*mm, stroke=1, fill=1)
        c.setFillColor(GOLD)
        c.rect(0, 3*mm, 1.6*mm, self.h - 5*mm, stroke=0, fill=1)
        self.p.drawOn(c, 6*mm, self.h - 4.2*mm - self.p.height)

def quote_block(text):
    """인용 — 좌측 골드 라인"""
    p = Paragraph(esc(text), S["quote"])
    t = Table([[p]], colWidths=[CW])
    t.setStyle(TableStyle([
        ("LINEBEFORE", (0,0), (0,0), 1.6, GOLD),
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
        ("LEFTPADDING", (0,0), (-1,-1), 5*mm), ("RIGHTPADDING", (0,0), (-1,-1), 5*mm),
        ("TOPPADDING", (0,0), (-1,-1), 4*mm), ("BOTTOMPADDING", (0,0), (-1,-1), 3.4*mm),
    ]))
    return t

# ───────────────────────── 표지 ─────────────────────────
def draw_door(c, cx, top, w, h, color, light, lw):
    x0, y0 = cx - w/2, top          # y0 = 상단(위에서 아래로 그리는 좌표계 보정 완료값 전달)
    x1, y1 = cx + w/2, top - h
    c.setStrokeColor(color); c.setLineWidth(lw)
    c.arc(x0, y0 - w, x1, y0, 0, 180)                   # 아치
    c.line(x0, y0 - w/2, x0, y1); c.line(x1, y0 - w/2, x1, y1)
    c.line(x0 - w/6, y1, x1 + w/6, y1)                  # 바닥
    c.setStrokeColor(light); c.setLineWidth(max(0.8, lw*0.55))
    for i, dx in enumerate([0.44, 0.56, 0.68]):
        lx = x0 + w*dx
        c.line(lx, y0 - w/2 - h*0.20 - i*(h*0.045), lx, y1 + h*0.08)

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
    # 상단 골드 라인
    c.setFillColor(GOLD); c.rect(cx-9*mm, h-27*mm, 18*mm, 0.7, stroke=0, fill=1)
    # 영문 캡션(자간)
    tracked(c, cx, h-33*mm, "LEAVING THE CHURCH,  MEETING JESUS", "NSK", 7, 1.7, GOLD)
    # 부제
    c.setFillColor(HexColor("#CBD3C9")); c.setFont("NSK", 9)
    c.drawCentredString(cx, h-42*mm, "환멸의 시대를 건너, 다시 찾은 진짜 교회")
    # 제목
    c.setFillColor(CREAM); c.setFont("NSKB", 21)
    c.drawCentredString(cx, h-58*mm, "교회를 떠나고서야,")
    c.drawCentredString(cx, h-73*mm, "예수를 만났다")
    # 요약본 배지
    tracked(c, cx, h-87*mm, "핵심 메시지 요약본", "NSKB", 10.5, 2.4, GOLD)
    c.setStrokeColor(GOLD); c.setLineWidth(0.6)
    c.line(cx-21*mm, h-91.5*mm, cx+21*mm, h-91.5*mm)
    # 문 심볼
    draw_door(c, cx, h-104*mm, 26*mm, 40*mm, GOLD, CREAM, 1.5)
    # 하단
    tracked(c, cx, 40*mm, "The door is still open", "NSK", 8.5, 0.9, GOLD)
    c.setFillColor(HexColor("#CBD3C9")); c.setFont("NSK", 9.5)
    c.drawCentredString(cx, 28*mm, "오광일 지음")
    c.setFillColor(HexColor("#8FA396")); c.setFont("NSK", 7.6)
    c.drawCentredString(cx, 18*mm, "바이블 인사이트 · biblynote.com")

def draw_body(c, doc):
    w, h = PAGE
    if doc.page <= 1:
        return
    c.setStrokeColor(RULE); c.setLineWidth(0.4)
    c.line(ML, MB - 6*mm, w - MR, MB - 6*mm)
    c.setFont("NSK", 7.4); c.setFillColor(GRAY)
    c.drawString(ML, MB - 10.4*mm, "교회를 떠나고서야, 예수를 만났다 · 핵심 요약")
    c.drawRightString(w - MR, MB - 10.4*mm, str(doc.page - 1))

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
            story.append(Rule(CW, GOLD, 1.2, 4))
            story.append(Spacer(1, 6))
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
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "tools", "summary_src.txt")
    out = os.path.join(ROOT, "files", "교회를떠나고서야-핵심요약.pdf")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    build(src, out)
