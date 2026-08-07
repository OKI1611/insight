# -*- coding: utf-8 -*-
"""정본역(正本譯) 킹제임스 성경 : 헤리티지 에디션 — PDF 직접 생성(ReportLab)

  ① 큰글자판  A4 · 1단 14pt (어르신용 · 자간 균일 CJK 조판)
  ② 한영대역  신국판 152×225 · 존더반 병렬 표준형
     - 좌 한글 / 우 영어, 절 단위 정렬(verse-for-verse)
     - 러닝헤드(바깥 책·장, 중앙 쪽번호) + 단 구분선 + 큰 장번호
     - 미국 판매 1위 Zondervan NIV/KJV Parallel Bible 구조 기준 (2026-08-03 사용자 확정)

  서체: Noto Serif KR 정적 인스턴스(SIL OFL) · 서브셋 임베딩
  실행: python tools/build_pdfs.py [big|par|both]
"""
import json, io, os, re, sys, time
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph,
                                Spacer, PageBreak, Table, TableStyle)

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_appendix as APX                       # 앞·뒤 부록(2026-08-05 확정 구성)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FDIR = os.path.join(ROOT, "tools", "fonts")
pdfmetrics.registerFont(TTFont("NSK",  os.path.join(FDIR, "NotoSerifKR-Regular.ttf")))
pdfmetrics.registerFont(TTFont("NSKB", os.path.join(FDIR, "NotoSerifKR-Bold.ttf")))
pdfmetrics.registerFontFamily("NSK", normal="NSK", bold="NSKB")

GREEN = HexColor("#00593c"); GRAY = HexColor("#8a8a8a"); INK = HexColor("#232d28")
RULE  = HexColor("#c9c2b4")
books = json.load(io.open(os.path.join(ROOT, "bible", "books.json"), encoding="utf-8"))

# 자체 집필 소제목(2026-08-03): bible/headings/ko.json — {책: {장: [[절, 제목], ...]}}
# 개역 계열 소제목은 성서공회 저작물이라 쓰지 않고 전량 새로 지었다. 시편은 관례상 없음.
try:
    HEADINGS = json.load(io.open(os.path.join(ROOT, "bible", "headings", "ko.json"), encoding="utf-8"))
except Exception:
    HEADINGS = {}

def headings_for(book, ch):
    """해당 장의 소제목을 {절번호: 제목} 으로 반환"""
    return {v: t for v, t in HEADINGS.get(book, {}).get(str(ch), [])}

def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))

# 한글 본문 문장기호 정리(2026-08-03 사용자 확정):
#   따옴표·작은따옴표·낫표류는 모두 삭제 — 기존 한글 성경(개역 계열)의 관례대로 최소화.
#   마침표·쉼표·물음표·느낌표 등 문장부호는 유지. 영어(KJV) 본문은 원문 그대로 둔다
#   (KJV의 아포스트로피 mother's 등은 소유격이라 제거하면 안 됨).
_KO_QUOTES = re.compile(u'[“”‘’"\'「」『』《》〈〉]')

def clean_ko(s):
    s = _KO_QUOTES.sub("", str(s))
    return re.sub(r"\s{2,}", " ", s).strip()

def kr(b, c):
    return json.loads(io.open(os.path.join(ROOT, "bible", "kr", f"{b}-{c}.json"), encoding="utf-8-sig").read())

def en(b, c):
    p = os.path.join(ROOT, "bible", "en", f"{b}-{c}.json")
    return json.loads(io.open(p, encoding="utf-8").read()) if os.path.exists(p) else None

COPY = [
 ("도서명  정본역(正本譯) 킹제임스 성경 : 헤리티지 에디션", True),
 ("‘정본역(正本譯)’은 공인본문(Textus Receptus)과 맛소라 본문을 저본으로 삼았음을 뜻하는 말이며, "
  "다른 번역본의 가치를 부정하는 표현이 아닙니다.", False),
 ("이 책의 한국어 본문은 킹제임스 성경(KJV, 1611)의 영어 본문과 그 저본인 공인본문(Textus Receptus)·맛소라 본문을 "
  "히브리어·아람어·헬라어 원문과 대조하여 바이블 인사이트가 직접 번역한 것입니다. 기존 한국어 역본을 저본으로 삼지 않은 "
  "독자적인 번역이며, 번역 원칙 전문은 biblynote.com/translation 에 공개되어 있습니다.", False),
 ("영어 본문(King James Version, 1611)은 대한민국 저작권법상 보호 기간이 만료된 퍼블릭 도메인 저작물입니다.", False),
 ("본문 서체는 SIL Open Font License로 배포되는 Noto Serif KR을 사용하였습니다.", False),
 ("한국어 번역 저작권 ⓒ 오광일 · 바이블 인사이트, 2026. 이 책의 한국어 본문을 출판사의 서면 허락 없이 복제·전재·배포할 수 "
  "없습니다. 다만 개인 묵상·설교·강의·논문에서의 통상적인 인용은 출처(정본역(正本譯) 킹제임스 성경 : 헤리티지 에디션)를 밝히는 조건으로 허용합니다.", False),
 ("펴낸곳  바이블 인사이트 출판사", False),
 ("옮긴이  오광일", False),
 ("문의  contact@biblynote.com · biblynote.com", False),
]

def front_matter(sub, page, big=False):
    """표지 + 판권 — 판형에 비례해 여백 계산"""
    ph = page[1]
    # 역본명이 27자로 길어 한 줄이면 판형 폭을 넘는다 → 2줄 배치 + 크기 하향
    s_t  = ParagraphStyle("t",  fontName="NSKB", fontSize=25 if big else 19, leading=34 if big else 27, alignment=TA_CENTER, textColor=INK)
    s_s  = ParagraphStyle("s",  fontName="NSKB", fontSize=21 if big else 17, leading=30, alignment=TA_CENTER, textColor=GREEN)
    s_e  = ParagraphStyle("e",  fontName="NSK",  fontSize=11, leading=17, alignment=TA_CENTER, textColor=GRAY)
    s_p  = ParagraphStyle("pb", fontName="NSK",  fontSize=11, leading=17, alignment=TA_CENTER, textColor=INK)
    s_h  = ParagraphStyle("h",  fontName="NSKB", fontSize=13, leading=20, textColor=GREEN, spaceAfter=9)
    s_b  = ParagraphStyle("b",  fontName="NSK",  fontSize=9,  leading=14.2, alignment=TA_JUSTIFY, textColor=INK, spaceAfter=5, wordWrap="CJK")
    s_bb = ParagraphStyle("bb", parent=s_b, fontName="NSKB")
    out = [Spacer(1, ph*0.21),
           Paragraph("정본역(正本譯) 킹제임스 성경<br/>헤리티지 에디션", s_t), Spacer(1, ph*0.018),
           Paragraph(sub, s_s), Spacer(1, ph*0.012),
           Paragraph("THE HERITAGE KJV · AUTHENTIC VERSION · 1611", s_e),
           Spacer(1, ph*0.26), Paragraph("바이블 인사이트 출판사", s_p), PageBreak(),
           Spacer(1, ph*0.05), Paragraph("일러두기 · 판권", s_h)]
    for txt, bold in COPY:
        out.append(Paragraph(esc(txt), s_bb if bold else s_b))
    out.append(PageBreak())
    return out

# ───────────────────────── ① 큰글자판 (A4 · 2단 · 자간 균일) ─────────────────────────
def build_bigprint():
    out = os.path.join(ROOT, "책원고", "정본역킹제임스성경_큰글자판.pdf")
    doc = HeadedDoc(out, A4, 1.9*cm, 1.9*cm, 2.2*cm, 1.8*cm, ncols=2, gutter=9*mm, head_size=9,
                    title="정본역(正本譯) 킹제임스 성경 : 헤리티지 에디션 (큰글자판)", author="오광일", subject="한글 전용 큰글자 성경")

    # 자이언트 프린트형(미국 Giant Print 계열 · 2026-08-03 사용자 확정)
    #   큰 숫자 장 표기 + 영문 책명 병기 + 초록 소제목 — 한영대역판과 디자인 통일
    s_bk  = ParagraphStyle("bk",  fontName="NSKB", fontSize=25, leading=34, alignment=TA_CENTER, textColor=INK,
                           spaceBefore=10, spaceAfter=2)
    s_bke = ParagraphStyle("bke", fontName="NSK",  fontSize=11, leading=16, alignment=TA_CENTER, textColor=GRAY, spaceAfter=12)
    s_ch  = ParagraphStyle("ch",  fontName="NSKB", fontSize=30, leading=33, textColor=GREEN, spaceBefore=10, spaceAfter=5)
    s_v   = ParagraphStyle("v",   fontName="NSK",  fontSize=14, leading=24.5, alignment=TA_JUSTIFY, textColor=INK,
                           spaceAfter=4.5, wordWrap="CJK")        # ★자간 균일(CJK 균등 분배)
    s_sub = ParagraphStyle("sub", fontName="NSKB", fontSize=13.5, leading=19.5, textColor=GREEN,
                           spaceBefore=11, spaceAfter=4)          # 소제목
    story = front_matter("큰글자판", A4, big=True)
    # 앞부록(펴내며·번역 원칙·저본·일러두기·약자표) — front_matter가 이미 PageBreak로 끝나므로 선두 것은 제거
    story += APX.pdf_flowables(APX.resolve_verses(APX.front_sections()), doc._colw, big=True)[1:]
    story.append(PageBreak())
    t0 = time.time()
    for bi, bk in enumerate(books):
        bt = Paragraph(esc(bk["ko"]), s_bk)
        bt._bibly_head = (bk["ko"], bk["en"])
        story += [bt, Paragraph(esc(bk["en"]).upper(), s_bke)]
        for c in range(1, bk["ch"]+1):
            vs = kr(bk["file"], c)
            hd = headings_for(bk["file"], c)
            chp = Paragraph('%d <font size="11" color="#8a8a8a">%s</font>' % (c, esc(bk["ko"])), s_ch)
            chp._bibly_head = ("%s %d장" % (bk["ko"], c), bk["en"] + " %d" % c)
            story.append(chp)
            for n, v in enumerate(vs):
                if not isinstance(v, str):
                    continue
                if (n+1) in hd:
                    story.append(Paragraph(esc(hd[n+1]), s_sub))
                story.append(Paragraph('<font size="9.5" color="#00593c"><b>%d</b></font> %s' % (n+1, esc(clean_ko(v))), s_v))
        story.append(PageBreak())
        if (bi+1) % 10 == 0:
            print("  큰글자 %d/66 %.0fs" % (bi+1, time.time()-t0), flush=True)
    # 뒤부록(교리 용어·원어 도표·구원의 길·환산표·암송 30선·QR) — 본문이 PageBreak로 끝나므로 선두 것은 제거
    story += APX.pdf_flowables(APX.resolve_verses(APX.back_sections("bigprint")), doc._colw, big=True)[1:]
    doc.build(story)
    print("큰글자판 PDF:", round(os.path.getsize(out)/1e6, 1), "MB ·", doc.page, "쪽 · %.0fs" % (time.time()-t0))
    return out

# ───────────────────────── 공용: 러닝헤드 달린 문서 (1단/다단) ─────────────────────────
class HeadedDoc(BaseDocTemplate):
    """러닝헤드(바깥 책·장, 중앙 쪽번호) + 다단이면 단 구분선.
       afterFlowable 로 _bibly_head 마커를 추적해 페이지 끝에 그린다."""
    def __init__(self, path, page, ml, mr, mt, mb, ncols=1, gutter=8*mm, head_size=8, **kw):
        BaseDocTemplate.__init__(self, path, pagesize=page,
                                 leftMargin=ml, rightMargin=mr,
                                 topMargin=mt, bottomMargin=mb, **kw)
        self._page = page; self._ml, self._mr, self._mt, self._mb = ml, mr, mt, mb
        self._gutter = gutter; self._ncols = ncols; self._hs = head_size
        self._head = ("", "")
        self._head_skip = 2                     # 표지·판권 쪽수(러닝헤드 제외) — 샘플은 0으로
        W = page[0] - ml - mr
        cw = (W - gutter*(ncols-1)) / ncols
        frames = [Frame(ml + i*(cw+gutter), mb, cw, page[1]-mt-mb, id="c%d" % i,
                        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
                  for i in range(ncols)]
        self._colw = cw
        self.addPageTemplates([PageTemplate(id="p", frames=frames, onPageEnd=self._draw_head)])

    def afterFlowable(self, fl):
        h = getattr(fl, "_bibly_head", None)
        if h:
            self._head = h

    def _draw_head(self, cv, doc):
        if doc.page <= self._head_skip:         # 표지·판권 제외
            return
        w, h = self._page
        cv.setFont("NSKB", self._hs); cv.setFillColor(INK)
        cv.drawString(self._ml, h - 11*mm, self._head[0])
        cv.setFont("NSK", self._hs)
        cv.drawRightString(w - self._mr, h - 11*mm, self._head[1])
        cv.setFillColor(GRAY)
        cv.drawCentredString(w/2, h - 11*mm, str(doc.page))
        cv.setStrokeColor(RULE); cv.setLineWidth(0.5)
        cv.line(self._ml, h - 13*mm, w - self._mr, h - 13*mm)
        if self._ncols > 1:                     # 단 구분선
            cv.setLineWidth(0.4)
            for i in range(1, self._ncols):
                x = self._ml + i*self._colw + (i - 0.5)*self._gutter
                cv.line(x, self._mb, x, h - self._mt)

# ───────────────────────── ② 한영대역 (신국판 · 존더반 병렬 표준) ─────────────────────────
P_PAGE = (152*mm, 225*mm)                      # 신국판
P_ML = P_MR = 12*mm; P_MT = 18*mm; P_MB = 13*mm

def build_parallel():
    out = os.path.join(ROOT, "책원고", "정본역킹제임스성경_한영대역.pdf")
    doc = HeadedDoc(out, P_PAGE, P_ML, P_MR, P_MT, P_MB, ncols=1,
                    title="정본역(正本譯) 킹제임스 성경 : 헤리티지 에디션 (한영대역)", author="오광일",
                    subject="KJV 한영대역 성경 · 존더반 병렬 표준형")

    s_bk  = ParagraphStyle("bk",  fontName="NSKB", fontSize=19, leading=26, alignment=TA_CENTER, textColor=INK, spaceBefore=10, spaceAfter=2)
    s_bke = ParagraphStyle("bke", fontName="NSK",  fontSize=9.5, leading=14, alignment=TA_CENTER, textColor=GRAY, spaceAfter=9)
    s_ch  = ParagraphStyle("ch",  fontName="NSKB", fontSize=20, leading=23, textColor=GREEN, spaceBefore=8, spaceAfter=4)
    s_ko  = ParagraphStyle("ko",  fontName="NSK",  fontSize=8.8, leading=13.4, alignment=TA_JUSTIFY, textColor=INK, wordWrap="CJK")  # ★자간 균일
    s_en  = ParagraphStyle("en",  fontName="NSK",  fontSize=8.2, leading=12.1, alignment=TA_JUSTIFY, textColor=INK)                  # 라틴 워드랩 유지
    s_sub = ParagraphStyle("sub", fontName="NSKB", fontSize=9.6, leading=13.5, textColor=HexColor("#4a5a52"),
                           spaceBefore=7, spaceAfter=3.5)         # 소제목(양단 공통, 전체 폭)

    W = P_PAGE[0] - P_ML - P_MR
    half = W/2 - 3.2*mm
    tstyle = TableStyle([("VALIGN", (0,0), (-1,-1), "TOP"),
                         ("LINEAFTER", (0,0), (0,-1), 0.4, RULE),                 # 단 구분선
                         ("LEFTPADDING",  (0,0), (0,-1), 0), ("RIGHTPADDING", (0,0), (0,-1), 8),
                         ("LEFTPADDING",  (1,0), (1,-1), 8), ("RIGHTPADDING", (1,0), (1,-1), 0),
                         ("TOPPADDING",   (0,0), (-1,-1), 0), ("BOTTOMPADDING", (0,0), (-1,-1), 3.6)])

    def vno(n):
        return '<font size="6.2" color="#00593c"><b>%d</b></font> ' % n

    story = front_matter("한영대역", P_PAGE)
    story += APX.pdf_flowables(APX.resolve_verses(APX.front_sections()), W, big=False)[1:]
    story.append(PageBreak())
    t0 = time.time()
    for bi, bk in enumerate(books):
        bt = Paragraph(esc(bk["ko"]), s_bk)
        bt._bibly_head = (bk["ko"], bk["en"])
        story += [bt, Paragraph(esc(bk["en"]).upper(), s_bke)]
        for c in range(1, bk["ch"]+1):
            vs = en(bk["file"], c)
            if vs is None:
                continue
            chp = Paragraph('%d <font size="8" color="#8a8a8a">%s · %s %d</font>'
                            % (c, esc(bk["ko"]), esc(bk["en"]), c), s_ch)
            chp._bibly_head = ("%s %d장" % (bk["ko"], c), "%s %d" % (bk["en"], c))
            story.append(chp)
            # 소제목 절에서 표를 끊고, 소제목을 전체 폭으로 얹은 뒤 다음 구간 표를 이어 붙인다
            hd = headings_for(bk["file"], c)
            rows = []
            def flush():
                if rows:
                    story.append(Table(list(rows), colWidths=[half, half], style=tstyle, repeatRows=0))
                    rows.clear()
            for n, v in enumerate(vs):
                if (n+1) in hd:
                    flush()
                    story.append(Paragraph(esc(hd[n+1]), s_sub))
                rows.append([Paragraph(vno(n+1) + esc(clean_ko(v.get("ko", "") or "")), s_ko),
                             Paragraph(vno(n+1) + esc(v.get("en", "") or ""), s_en)])
            flush()
        story.append(PageBreak())
        if (bi+1) % 10 == 0:
            print("  대역 %d/66 %.0fs" % (bi+1, time.time()-t0), flush=True)
    story += APX.pdf_flowables(APX.resolve_verses(APX.back_sections("parallel")), W, big=False)[1:]
    doc.build(story)
    print("한영대역 PDF:", round(os.path.getsize(out)/1e6, 1), "MB ·", doc.page, "쪽 · %.0fs" % (time.time()-t0))
    return out

if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "both"
    if which in ("big", "both"):
        build_bigprint()
    if which in ("par", "both"):
        build_parallel()
