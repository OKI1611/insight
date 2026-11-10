# -*- coding: utf-8 -*-
"""mk_extract.py — 『천년왕국을 아십니까』 내지 PDF → 장별 한국어 원문 Markdown (영문판 번역 원천)

  산출: 책원고/영문판_천년왕국/src_ko/NN_slug.md
  - 머리글(책 제목·장 제목 반복)·쪽번호·'시안확인용' 워터마크 제거
  - 줄바꿈으로 끊긴 문단을 다시 잇는다(행 끝 위치·들여쓰기로 문단 경계 판정)
  - 표는 PyMuPDF find_tables() 로 Markdown 표로 변환하고 `[표 @pNN]` 마커를 붙인다
  - 그림(래스터)이 있는 자리는 `[그림 @pNN]` 마커 (영문 인포그래픽으로 재작도 대상)
  - 각 문단 앞에 원서 쪽수를 `{p.NN}` 로 남겨 역추적할 수 있게 한다
  사용: python tools/mk_extract.py "<내지 PDF 경로>"
"""
import sys, os, re, io
import fitz

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "책원고", "영문판_천년왕국", "src_ko")

# (파일 슬러그, 시작쪽, 끝쪽) — 차례(p2~4) 기준. PDF 쪽번호 = 인쇄 쪽번호
SECTIONS = [
    ("00a_preface", 5, 6), ("00b_prologue", 7, 12), ("00c_at_a_glance", 13, 19),
    ("01", 20, 32), ("02", 33, 40), ("03", 41, 49), ("04", 50, 57),
    ("05", 58, 68), ("06", 69, 80), ("07", 81, 98), ("08", 99, 111), ("09", 112, 119),
    ("10", 120, 129), ("11", 130, 139), ("12", 140, 147), ("13", 148, 157), ("14", 158, 165),
    ("15", 166, 176), ("16", 177, 185), ("17", 186, 196),
    ("18", 197, 202), ("19", 203, 209), ("20", 210, 218), ("21", 219, 232), ("22", 233, 242),
    ("23", 243, 249), ("24", 250, 262),
    ("25", 263, 274), ("26", 275, 283), ("27", 284, 290), ("28", 291, 302),
    ("29_epilogue", 303, 308), ("30_appendix_A", 309, 310), ("31_appendix_B", 311, 314),
    ("32_appendix_C", 315, 317), ("33_appendix_D", 317, 318), ("34_appendix_E", 319, 326),
    ("35_author", 327, 327), ("36_colophon", 328, 328),
]

RUNHEAD = re.compile(r"^(천년왕국을 아십니까|제\d부 · \S+|부록|\d{1,3}|시안확인용|\d+장 · .+|프롤로그 · 천년왕국을 아십니까|한눈에 보는 천년왕국 · 핵심 개념 요약|에필로그 · .+)$")
WATERMARK = "시안확인용"

def page_lines(page):
    """[(y0, x0, x1, text, size)] 본문 순서대로"""
    d = page.get_text("dict")
    out = []
    for b in d["blocks"]:
        if b["type"] != 0: continue
        for l in b["lines"]:
            t = "".join(s["text"] for s in l["spans"]).strip()
            if not t: continue
            size = max(s["size"] for s in l["spans"])
            x0, y0, x1, y1 = l["bbox"]
            out.append((round(y0, 1), round(x0, 1), round(x1, 1), t, size))
    out.sort(key=lambda r: (r[0], r[1]))
    return out

def is_bold_heading(size):
    return size >= 11.5     # 본문 9~10pt, 소제목 11~13pt, 장 제목 16pt+

def extract_section(doc, start, end):
    md = []
    for pno in range(start, end + 1):
        page = doc[pno - 1]
        W, H = page.rect.width, page.rect.height
        tabs = []
        try:
            tf = page.find_tables()
            for t in tf.tables:
                if t.row_count >= 2 and t.col_count >= 2:
                    tabs.append((fitz.Rect(t.bbox), t))
        except Exception:
            pass
        imgs = [fitz.Rect(page.get_image_bbox(im)) for im in page.get_images(full=True)
                if page.get_image_bbox(im).height > 40]
        lines = page_lines(page)
        items = []          # (y, kind, payload)
        for r, t in tabs:
            try: md_tab = t.to_markdown()
            except Exception: md_tab = "\n".join(" | ".join(str(c or "") for c in row) for row in t.extract())
            md_tab = md_tab.replace("<br>", " ").replace("\n\n", "\n")
            items.append((r.y0, "table", "[표 @p%d]\n%s" % (pno, md_tab.strip())))
        for r in imgs:
            items.append((r.y0, "image", "[그림 @p%d]" % pno))
        # 본문 줄 → 문단
        paras, cur, cur_size = [], [], None
        body_right = max([x1 for (_, _, x1, _, _) in lines] or [W])
        first_page = (pno == start)
        for i, (y, x0, x1, t, size) in enumerate(lines):
            if any(fitz.Rect(x0, y, x1, y + 1).intersects(r) for r, _ in tabs): continue
            if t == WATERMARK or WATERMARK in t and len(t) <= 8: continue
            if y < 45 and RUNHEAD.match(t) and not (first_page and i < 3 and size > 11): continue   # 머리글
            if y > H - 40 and re.match(r"^\d{1,3}$", t): continue                                   # 쪽번호
            if re.match(r"^\d{1,3}$", t) and (y < 60 or y > H - 60): continue
            if is_bold_heading(size):
                if cur: paras.append((cur_y, "p", "".join(cur))); cur = []
                paras.append((y, "h", (t, size)))
                continue
            if not cur:
                cur, cur_y = [t], y
            else:
                cur.append(t)
            # 문단 끝 판정: 행 끝이 오른쪽 여백보다 많이 비었거나 다음 행이 들여쓰기
            short = (body_right - x1) > 12
            nxt = lines[i + 1] if i + 1 < len(lines) else None
            indent = nxt is not None and (nxt[1] - x0) > 6 and abs(nxt[0] - y) > 5
            gap = nxt is not None and (nxt[0] - y) > size * 2.2
            if short or indent or gap or nxt is None:
                paras.append((cur_y, "p", "".join(cur))); cur = []
        if cur: paras.append((cur_y, "p", "".join(cur)))
        for y, k, v in paras: items.append((y, k, v))
        items.sort(key=lambda r: r[0])
        md.append("\n{p.%d}\n" % pno)
        for y, k, v in items:
            if k == "h":
                t, size = v
                lvl = "#" if size >= 15 else ("##" if size >= 12.5 else "###")
                md.append("%s %s\n" % (lvl, t))
            else:
                md.append(v + "\n")
    text = "\n".join(md)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text

def main():
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass
    pdf = sys.argv[1]
    doc = fitz.open(pdf)
    os.makedirs(OUT, exist_ok=True)
    for slug, s, e in SECTIONS:
        txt = extract_section(doc, s, e)
        p = os.path.join(OUT, slug + ".md")
        io.open(p, "w", encoding="utf-8").write(txt)
        print("%-18s p%3d-%3d  %6d자  표 %2d  그림 %2d" % (slug, s, e, len(txt), txt.count("[표 @"), txt.count("[그림 @")))

if __name__ == "__main__":
    main()
