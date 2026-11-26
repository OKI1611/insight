# -*- coding: utf-8 -*-
"""build_mk_epub.py — 『The Millennial Kingdom Explained』 (영문판) Kindle 용 EPUB 3 빌더

  입력: 책원고/영문판_천년왕국/en/*.md  (장별 Markdown, 번역 산출)
        책원고/영문판_천년왕국/figures/fig-*.png (재작도 인포그래픽)
        책원고/영문판_천년왕국/build/cover_1600x2560.jpg (표지)
  출력: 책원고/영문판_천년왕국/build/The_Millennial_Kingdom_Explained.epub

  규격: EPUB 3.0 리플로우 · mimetype STORED 첫 항목 · nav.xhtml + toc.ncx 병행(KDP 권장)
  실행: python tools/build_mk_epub.py [--strict]   (--strict: 그림 누락·한글 잔존 시 중단)
"""
import io, os, re, sys, glob, zipfile, html, uuid, time, argparse
import markdown

try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(ROOT, "책원고", "영문판_천년왕국")
EN, FIG, BUILD = (os.path.join(BASE, d) for d in ("en", "figures", "build"))
OUT = os.path.join(BUILD, "The_Millennial_Kingdom_Explained.epub")
COVER = os.path.join(BUILD, "cover_1600x2560.jpg")

TITLE = "The Millennial Kingdom Explained"
SUBTITLE = "The Real Thousand-Year Kingdom the Bible Promised"
AUTHOR = "Kwang-il Oh"
PUBLISHER = "Bible Insight"
LANG = "en"
BOOK_ID = "urn:uuid:" + str(uuid.uuid5(uuid.NAMESPACE_URL, "https://biblynote.com/books/millennium-en"))

# 파일 → (표시 제목, 그룹) — 파트 머리 페이지는 START_PART 에 지정
PARTS = {
    "01": ("Part One", "Foundations", "What Is the Millennial Kingdom?"),
    "05": ("Part Two", "Arrival", "How Does the Kingdom Come?"),
    "10": ("Part Three", "Citizens", "Who Enters, and How Do They Live?"),
    "18": ("Part Four", "The Kingdom", "Its Land, Its Worship, and Its Government"),
    "25": ("Part Five", "Consummation", "The End of the Thousand Years and the Eternal State"),
}
APPENDIX_START = "30_appendix_A"
LABELS = {"chapter": "Chapter", "contents": "Contents", "toc": "Table of Contents", "cover": "Cover",
          "titlepage": "Title Page", "copyright": "Copyright", "rights": "Copyright © 2026 %s. All rights reserved."}

def use_profile(lang):
    """--lang es: 스페인어판(El Reino Milenial explicado) 경로·제목·라벨로 전환"""
    global LANG, BASE, EN, FIG, BUILD, OUT, COVER, TITLE, SUBTITLE, BOOK_ID, PARTS, LABELS
    if lang != "es": return
    LANG = "es"
    BASE = os.path.join(ROOT, "책원고", "스페인어판_천년왕국")
    EN, FIG, BUILD = (os.path.join(BASE, d) for d in ("es", "figures", "build"))
    OUT = os.path.join(BUILD, "El_Reino_Milenial_explicado.epub")
    COVER = os.path.join(BUILD, "cover_1600x2560.jpg")
    TITLE = "El Reino Milenial explicado"
    SUBTITLE = "El verdadero reino de mil años que la Biblia prometió"
    BOOK_ID = "urn:uuid:" + str(uuid.uuid5(uuid.NAMESPACE_URL, "https://biblynote.com/books/millennium-es"))
    PARTS = {
        "01": ("Primera parte", "Fundamentos", "¿Qué es el Reino Milenial?"),
        "05": ("Segunda parte", "Llegada", "¿Cómo viene el Reino?"),
        "10": ("Tercera parte", "Ciudadanos", "¿Quiénes entran y cómo viven?"),
        "18": ("Cuarta parte", "El Reino", "Su tierra, su culto y su gobierno"),
        "25": ("Quinta parte", "Consumación", "El fin de los mil años y el estado eterno"),
    }
    LABELS = {"chapter": "Capítulo", "contents": "Índice", "toc": "Índice", "cover": "Portada",
              "titlepage": "Portadilla", "copyright": "Derechos", "rights": "Copyright © 2026 %s. Todos los derechos reservados."}

CSS = """
@charset "utf-8";
body { font-family: Georgia, "Times New Roman", serif; line-height: 1.6; margin: 0 5%; color: #111; }
h1 { font-size: 1.7em; line-height: 1.25; margin: 1.6em 0 0.4em; text-align: left; font-weight: bold; }
h1 .num { display: block; font-size: 0.6em; letter-spacing: 0.12em; color: #8a6d2f; text-transform: uppercase; margin-bottom: 0.4em; }
h2 { font-size: 1.25em; margin: 1.6em 0 0.5em; line-height: 1.3; }
h3 { font-size: 1.05em; margin: 1.4em 0 0.4em; color: #1a2a52; border-left: 4px solid #c9a24b; padding-left: 0.5em; }
p { margin: 0 0 0.85em; text-align: left; }
p.tagline { color: #555; font-style: italic; margin: -0.2em 0 1em; }
blockquote { margin: 0.9em 1.2em 1em 1.2em; padding: 0.4em 0.9em; border-left: 3px solid #c9a24b; background: #faf7ef; font-style: normal; }
blockquote p { margin: 0 0 0.4em; }
table { border-collapse: collapse; width: 100%; margin: 1em 0 1.2em; font-size: 0.88em; }
th, td { border: 1px solid #bbb; padding: 0.35em 0.45em; vertical-align: top; text-align: left; }
th { background: #eee9dc; }
figure { margin: 1.2em 0; text-align: center; page-break-inside: avoid; }
figure img { max-width: 100%; height: auto; }
figcaption { font-size: 0.85em; color: #444; margin-top: 0.4em; text-align: left; }
.part { text-align: center; margin-top: 30%; }
.part .pn { font-size: 0.9em; letter-spacing: 0.25em; color: #8a6d2f; text-transform: uppercase; }
.part h1 { text-align: center; font-size: 2em; margin: 0.3em 0 0.2em; }
.part .ps { font-size: 1.1em; color: #333; font-style: italic; }
.titlepage { text-align: center; margin-top: 20%; }
.titlepage .t { font-size: 2em; font-weight: bold; line-height: 1.2; }
.titlepage .s { font-size: 1.1em; font-style: italic; margin: 0.8em 0 2em; color: #333; }
.titlepage .a { font-size: 1.2em; letter-spacing: 0.1em; }
.titlepage .p { margin-top: 4em; font-size: 0.9em; color: #666; }
.copyright { font-size: 0.85em; color: #333; }
.copyright p { margin: 0 0 0.6em; }
hr { border: 0; border-top: 1px solid #ccc; margin: 1.6em 25%; }
.toc p { margin: 0 0 0.3em; }
.toc .l2 { margin-left: 1.4em; }
ol, ul { margin: 0 0 0.9em 1.2em; }
li { margin-bottom: 0.3em; }
em { font-style: italic; }
/* ── 2026-11-24 내지 디자인 개편(사용자 승인): 종이책식 본문 + 장 첫머리 + 상자 ── */
body { font-family: serif; line-height: normal; margin: 0 4%; }
p { margin: 0; text-indent: 1.4em; text-align: justify; }
p.first, p.noindent, h1 + p, h2 + p, h3 + p, figure + p, blockquote + p, aside + p, table + p, hr + p, div + p { text-indent: 0; }
p.first:first-letter { float: left; font-size: 3.2em; line-height: 0.85; margin: 0.05em 0.08em 0 0; color: #1a2a52; font-weight: bold; }
p.first span.lead { font-variant: small-caps; letter-spacing: 0.03em; }
h1 { text-align: center; font-size: 1.6em; line-height: 1.2; margin: 2em 0 0.3em; font-weight: normal; }
h1 .num { display: block; font-size: 0.5em; letter-spacing: 0.3em; text-transform: uppercase; color: #8a6d2f; margin-bottom: 0.9em; }
h1 .sub { display: block; font-size: 0.62em; font-style: italic; color: #444; margin-top: 0.5em; }
p.tagline { text-align: center; text-indent: 0; font-style: normal; font-size: 0.9em; color: #666; margin: 0.6em 0 1.6em; }
div.epigraph { margin: 0 10% 2em; text-align: center; }
div.epigraph p { text-indent: 0; text-align: center; font-style: italic; font-size: 0.95em; }
p.ref { text-indent: 0; font-style: normal; font-variant: small-caps; letter-spacing: 0.05em; font-size: 0.85em; color: #555; margin-top: 0.3em; }
div.epigraph p.ref { text-align: center; font-style: normal; }
blockquote p.ref { text-align: right; }
hr.orn { border: 0; border-top: 1px solid #c9a24b; width: 18%; margin: 1.8em auto 1.2em; }
h2 { font-size: 1.15em; margin: 0 0 0.7em; text-align: left; font-weight: bold; color: #1a2a52; page-break-after: avoid; }
blockquote { margin: 0.9em 6% 1em; padding: 0; border: 0; background: none; }
blockquote p { text-indent: 0; font-size: 0.95em; }
aside.box { display: block; margin: 1.3em 0; padding: 0.7em 0.9em 0.6em; border: 1px solid #c9a24b; background: #fbf8f0; page-break-inside: avoid; }
aside.box h3 { margin: 0 0 0.5em; padding: 0; border: 0; font-size: 0.8em; letter-spacing: 0.1em; text-transform: uppercase; color: #8a6d2f; }
aside.box p { text-indent: 0; font-size: 0.92em; margin-bottom: 0.4em; text-align: left; }
aside.box ul, aside.box ol { font-size: 0.92em; margin-bottom: 0.2em; }
aside.takeaways { background: #f1f3f8; border-color: #1a2a52; }
aside.takeaways h3 { color: #1a2a52; }
aside.onesentence { border: 0; border-top: 2px solid #c9a24b; border-bottom: 2px solid #c9a24b; background: none; padding: 0.8em 0; }
aside.onesentence h3 { text-align: center; }
aside.onesentence p { text-align: center; font-style: italic; font-size: 1.02em; }
figcaption { text-align: center; font-size: 0.8em; color: #555; font-style: italic; }
table { font-size: 0.82em; }
"""

# 상자 종류: h3 제목 접두어 → class. 상자 범위는 기본 '첫 단락'까지이고, 원문 상자가 더 길면
# md 에 '{/box}' 한 줄을 넣어 끝을 표시한다(원서 PDF 상자 테두리로 확인, 2026-11-24).
BOX_KINDS = [("Window on the Original", "window"), ("A Page from History", "history"),
             ("Text or Inference?", "inference"), ("Frequently Asked Question", "faq"),
             ("Confusion", "confusion"), ("Key Takeaways", "takeaways"), ("In One Sentence", "onesentence"),
             ("Ventana al original", "window"), ("Una página de la historia", "history"), ("¿Texto o inferencia?", "inference"),
             ("Pregunta frecuente", "faq"), ("Confusión", "confusion"), ("Puntos clave", "takeaways"), ("En una frase", "onesentence")]

def design_xhtml(body):
    """승인된 내지 디자인을 본문 XHTML 에 입힌다: 장 제목/부제 분리, 제사, 성경 블록 인용, 드롭캡, 상자, 장식선."""
    # 1) 장 제목 "제목: 부제" → 제목 + 부제
    body = re.sub(r'<h1><span class="num">((?:Chapter|Capítulo) \d+)</span>(.*?):\s*(.*?)</h1>',
                  r'<h1><span class="num">\1</span>\2<span class="sub">\3</span></h1>', body, count=1)
    # 2) 태그라인 바로 다음의 성경 인용 단락 = 제사(epigraph)
    body, n_epi = re.subn(r'(<p class="tagline">[^<]*?</p>\s*)<p>“([^<]*?)”\s*\(([^()<]*?)\)\.?</p>',
                          r'\1<div class="epigraph"><p>\2</p><p class="ref">\3</p></div>', body, count=1, flags=re.S)
    # 3) 단독 성경 인용 단락 “…” (책 장:절) → 블록 인용 + 오른쪽 출처
    body = re.sub(r'<p>“([^<]{100,}?)”\s*\(([^()<]*\d+:\d+[^()<]*)\)\.?</p>',
                  r'<blockquote class="kjv"><p>“\1”</p><p class="ref">\2</p></blockquote>', body)
    # 4) 상자: h3 + (기본) 첫 단락 / {/box} 표시까지 / Key Takeaways 는 다음 제목 전까지
    parts = re.split(r'(<h[123][^>]*>.*?</h[123]>|<figure>.*?</figure>|<table>.*?</table>)', body, flags=re.S)
    out, i = [], 0
    while i < len(parts):
        p = parts[i]
        m = re.match(r'<h3>(.*?)</h3>', p, flags=re.S)
        kind = None
        if m:
            t = re.sub(r'<.*?>', '', m.group(1)).strip()
            kind = next((v for k, v in BOX_KINDS if t.startswith(k)), None)
        if kind and i + 1 < len(parts):
            nxt = parts[i + 1]
            if '{/box}' in nxt:
                inner, rest = nxt.split('{/box}', 1)
                inner = re.sub(r'<p>\s*$', '', inner); rest = re.sub(r'^\s*</p>', '', rest)
            elif kind == "takeaways":
                inner, rest = nxt, ""
            else:
                mm = re.match(r'(\s*<(p|ul|ol|blockquote)[ >].*?</\2>)(.*)', nxt, flags=re.S)
                inner, rest = (mm.group(1), mm.group(3)) if mm else (nxt, "")
            out.append('<aside class="box %s">%s%s</aside>%s' % (kind, p, inner, rest)); i += 2; continue
        out.append(p); i += 1
    body = "".join(out)
    body = body.replace("<p>{/box}</p>", "").replace("{/box}", "")
    # 5) h2 앞 장식선, 장 첫 단락 드롭캡(+ 첫 네 단어 작은 대문자)
    body = re.sub(r'(<h2[ >])', r'<hr class="orn"/>\1', body)
    def lead(mm):
        txt = mm.group(2)
        w = re.match(r'((?:\S+\s+){1,4})(.*)', txt, flags=re.S)
        if w and '<' not in w.group(1):
            txt = '<span class="lead">%s</span>%s' % (w.group(1), w.group(2))
        return mm.group(1) + '<p class="first">' + txt + '</p>'
    anchor = r'(</div>\s*)<p>(.*?)</p>' if n_epi else r'(<p class="tagline">.*?</p>\s*)<p>(.*?)</p>'
    body = re.sub(anchor, lead, body, count=1, flags=re.S)
    return body

XHTML = ('<?xml version="1.0" encoding="utf-8"?>\n<!DOCTYPE html>\n'
         '<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="en" lang="en">\n'
         '<head><meta charset="utf-8"/><title>%s</title><link rel="stylesheet" type="text/css" href="style.css"/></head>\n'
         '<body%s>\n%s\n</body>\n</html>\n')

def E(s): return html.escape(s, quote=True)

MD = markdown.Markdown(extensions=["tables", "smarty"], output_format="xhtml",
                       extension_configs={"smarty": {"substitutions": {
                           "left-single-quote": "‘", "right-single-quote": "’",
                           "left-double-quote": "“", "right-double-quote": "”",
                           "left-angle-quote": "«", "right-angle-quote": "»",
                           "ellipsis": "…", "ndash": "–", "mdash": "—"}}})

def md_to_xhtml(text, chapter_num=None):
    """Markdown → XHTML 본문 조각. 그림 마커·FIGURE SPEC 주석·태그라인 처리."""
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)           # FIGURE SPEC 주석 제거
    text = re.sub(r"\{p\.\d+\}", "", text)
    lines = text.split("\n")
    out, i = [], 0
    while i < len(lines):
        ln = lines[i]
        m = re.match(r"!\[(.*?)\]\((figures/[^)]+)\)", ln.strip())
        if m:
            cap, src = m.group(1), m.group(2)
            out.append('<figure><img src="%s" alt="%s"/><figcaption>%s</figcaption></figure>' % (E(os.path.basename(src)), E(cap), E(cap)))
            i += 1; continue
        out.append(ln); i += 1
    text = "\n".join(out)
    MD.reset()
    body = MD.convert(text)
    # 장 번호 꾸밈: <h1>Chapter 5. Title</h1> → <h1><span class="num">Chapter 5</span>Title</h1>
    body = re.sub(r"<h1>(Chapter|Capítulo) (\d+)\.\s*(.*?)</h1>", r'<h1><span class="num">\1 \2</span>\3</h1>', body, count=1)
    # 태그라인(— … —) 단락
    body = re.sub(r"<p>(—|&#8212;|&mdash;)\s*(.*?)\s*(—|&#8212;|&mdash;)</p>", r'<p class="tagline">\2</p>', body, count=1)
    # 그림 블록은 markdown 이 <p> 로 감쌀 수 있음
    body = re.sub(r"<p>(<figure>.*?</figure>)</p>", r"\1", body, flags=re.S)
    return body

def optimize_image(fn, path):
    """그림 PNG 를 256색 팔레트로 양자화해 용량을 줄인다(Kindle 전송비 $0.15/MB 절감). 표지 JPEG 는 그대로."""
    if not fn.lower().endswith(".png"):
        return open(path, "rb").read()
    from PIL import Image
    im = Image.open(path).convert("RGB")
    q = im.quantize(colors=160, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    buf = io.BytesIO(); q.save(buf, "PNG", optimize=True)
    return buf.getvalue()

def first_heading(md_text, fallback):
    m = re.search(r"^#\s+(.+)$", md_text, flags=re.M)
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else fallback

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--strict", action="store_true"); ap.add_argument("--lang", default="en"); a = ap.parse_args()
    use_profile(a.lang)
    os.makedirs(BUILD, exist_ok=True)
    files = sorted(glob.glob(os.path.join(EN, "*.md")))
    if not files: sys.exit("en/ 에 번역 파일이 없습니다")
    spine, manifest, nav, ncx = [], [], [], []
    docs = {}      # 파일명 → xhtml
    images = {}    # 파일명 → 경로
    missing_fig, hangul = [], []
    problems = []

    def add_doc(name, title, body, body_attr="", level=1):
        docs[name] = XHTML % (E(title), body_attr, body)
        spine.append(name); nav.append((level, title, name))

    # 1) 표지·속표지·판권
    has_cover = os.path.exists(COVER)
    if has_cover:
        images["cover.jpg"] = COVER
        add_doc("cover.xhtml", LABELS["cover"], '<div style="text-align:center;margin:0;padding:0"><img src="cover.jpg" alt="Cover" style="max-height:100%;max-width:100%"/></div>', ' style="margin:0;padding:0"')
    add_doc("title.xhtml", LABELS["titlepage"],
            '<div class="titlepage"><p class="t">%s</p><p class="s">%s</p><p class="a">%s</p><p class="p">%s<br/>biblynote.com</p></div>' % (E(TITLE), E(SUBTITLE), E(AUTHOR), E(PUBLISHER)))
    copyright_md = os.path.join(EN, "36_colophon.md")
    if os.path.exists(copyright_md):
        add_doc("copyright.xhtml", LABELS["copyright"], '<div class="copyright">%s</div>' % md_to_xhtml(io.open(copyright_md, encoding="utf-8").read()))

    # 2) 본문
    toc_entries = []
    for p in files:
        name = os.path.basename(p)[:-3]
        if name == "36_colophon": continue
        md_text = io.open(p, encoding="utf-8").read()
        if re.search(r"[가-힣]", re.sub(r"<!--.*?-->", "", md_text, flags=re.S)):
            hangul.append(name)
        num = name[:2]
        if num in PARTS:
            pn, pt, ps = PARTS[num]
            add_doc("part%s.xhtml" % num, "%s · %s" % (pn, pt),
                    '<div class="part"><p class="pn">%s</p><h1>%s</h1><p class="ps">%s</p></div>' % (E(pn), E(pt), E(ps)))
        title = first_heading(md_text, name)
        body = design_xhtml(md_to_xhtml(md_text))
        for fm in re.finditer(r'src="(fig-[^"]+)"', body):
            fp = os.path.join(FIG, fm.group(1))
            if os.path.exists(fp): images[fm.group(1)] = fp
            else: missing_fig.append((name, fm.group(1)))
        level = 2 if (num.isdigit() and name[:2] in [f"{i:02d}" for i in range(1, 29)]) or name.startswith("3") and "appendix" in name else 1
        add_doc(name + ".xhtml", title, body, level=level)

    # 3) 차례 페이지(본문 안 TOC)
    toc_html = ['<h1>%s</h1><div class="toc">' % LABELS["contents"]]
    for level, title, name in nav:
        if name in ("cover.xhtml", "title.xhtml", "copyright.xhtml", "toc.xhtml"): continue
        toc_html.append('<p class="%s"><a href="%s">%s</a></p>' % ("l2" if level == 2 else "l1", name, E(title)))
    toc_html.append("</div>")
    toc_doc = XHTML % (LABELS["contents"], "", "\n".join(toc_html))
    docs["toc.xhtml"] = toc_doc
    # 차례는 판권 다음에 끼운다
    pos = spine.index("copyright.xhtml") + 1 if "copyright.xhtml" in spine else (2 if has_cover else 1)
    spine.insert(pos, "toc.xhtml"); nav.insert(pos, (1, LABELS["contents"], "toc.xhtml"))

    if missing_fig:
        print("그림 누락 %d: %s" % (len(missing_fig), ", ".join("%s:%s" % m for m in missing_fig[:20])))
    if hangul:
        print("한글 잔존 파일:", ", ".join(hangul))
    if a.strict and (missing_fig or hangul):
        sys.exit("--strict: 누락/잔존이 있어 중단")

    # 4) nav.xhtml / toc.ncx
    nav_items = []
    for level, title, name in nav:
        if name == "cover.xhtml": continue
        nav_items.append('<li class="l%d"><a href="%s">%s</a></li>' % (level, name, E(title)))
    nav_xhtml = ('<?xml version="1.0" encoding="utf-8"?>\n<!DOCTYPE html>\n'
                 '<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="en" lang="en">'
                 '<head><meta charset="utf-8"/><title>Contents</title><link rel="stylesheet" type="text/css" href="style.css"/></head><body>'
                 '<nav epub:type="toc" id="toc"><h1>Contents</h1><ol>%s</ol></nav>'
                 '<nav epub:type="landmarks" hidden="hidden"><ol>'
                 '%s<li><a epub:type="toc" href="toc.xhtml">Table of Contents</a></li>'
                 '<li><a epub:type="bodymatter" href="%s">Start</a></li></ol></nav></body></html>') % (
        "".join(nav_items),
        '<li><a epub:type="cover" href="cover.xhtml">Cover</a></li>' if has_cover else "",
        "00a_preface.xhtml" if "00a_preface.xhtml" in docs else spine[-1])
    ncx_pts = []
    for n, (level, title, name) in enumerate([x for x in nav if x[2] != "cover.xhtml"], 1):
        ncx_pts.append('<navPoint id="np%d" playOrder="%d"><navLabel><text>%s</text></navLabel><content src="%s"/></navPoint>' % (n, n, E(title), name))
    ncx = ('<?xml version="1.0" encoding="utf-8"?>\n<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">'
           '<head><meta name="dtb:uid" content="%s"/><meta name="dtb:depth" content="2"/><meta name="dtb:totalPageCount" content="0"/><meta name="dtb:maxPageNumber" content="0"/></head>'
           '<docTitle><text>%s</text></docTitle><navMap>%s</navMap></ncx>') % (BOOK_ID, E(TITLE), "".join(ncx_pts))

    # 5) OPF
    man = ['<item id="css" href="style.css" media-type="text/css"/>',
           '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
           '<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>']
    ids = {}
    for n, name in enumerate(spine):
        ids[name] = "d%d" % n
        man.append('<item id="d%d" href="%s" media-type="application/xhtml+xml"/>' % (n, name))
    for n, (fn, _) in enumerate(sorted(images.items())):
        mt = "image/jpeg" if fn.lower().endswith((".jpg", ".jpeg")) else "image/png"
        props = ' properties="cover-image"' if fn == "cover.jpg" else ""
        man.append('<item id="img%d" href="%s" media-type="%s"%s/>' % (n, fn, mt, props))
    opf = ('<?xml version="1.0" encoding="utf-8"?>\n'
           '<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid" xml:lang="en">'
           '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">'
           '<dc:identifier id="bookid">%s</dc:identifier><dc:title id="t1">%s</dc:title>'
           '<meta refines="#t1" property="title-type">main</meta>'
           '<dc:title id="t2">%s</dc:title><meta refines="#t2" property="title-type">subtitle</meta>'
           '<dc:creator id="cr">%s</dc:creator><meta refines="#cr" property="role" scheme="marc:relators">aut</meta>'
           '<dc:language>%s</dc:language><dc:publisher>%s</dc:publisher><dc:date>%s</dc:date>'
           '<dc:rights>' + (LABELS["rights"] % E(AUTHOR)) + '</dc:rights>'
           '<meta property="dcterms:modified">%s</meta>%s'
           '</metadata><manifest>%s</manifest><spine toc="ncx">%s</spine></package>') % (
        BOOK_ID, E(TITLE), E(SUBTITLE), E(AUTHOR), LANG, E(PUBLISHER), time.strftime("%Y-%m-%d"),
        time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        '<meta name="cover" content="img0"/>' if has_cover else "",
        "".join(man), "".join('<itemref idref="%s"%s/>' % (ids[n], ' linear="no"' if n == "cover.xhtml" else "") for n in spine))

    # 6) zip  (언어 속성 치환: 템플릿은 en 으로 작성돼 있음)
    if LANG != "en":
        fix = lambda x: x.replace('xml:lang="en" lang="en"', 'xml:lang="%s" lang="%s"' % (LANG, LANG)).replace('xml:lang="en"', 'xml:lang="%s"' % LANG)
        docs = {k: fix(v) for k, v in docs.items()}; nav_xhtml = fix(nav_xhtml); opf = fix(opf); ncx = fix(ncx)
    with zipfile.ZipFile(OUT, "w") as z:
        z.writestr(zipfile.ZipInfo("mimetype"), "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        z.writestr("META-INF/container.xml", '<?xml version="1.0" encoding="utf-8"?><container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>', zipfile.ZIP_DEFLATED)
        z.writestr("OEBPS/content.opf", opf, zipfile.ZIP_DEFLATED)
        z.writestr("OEBPS/nav.xhtml", nav_xhtml, zipfile.ZIP_DEFLATED)
        z.writestr("OEBPS/toc.ncx", ncx, zipfile.ZIP_DEFLATED)
        z.writestr("OEBPS/style.css", CSS, zipfile.ZIP_DEFLATED)
        for name, x in docs.items(): z.writestr("OEBPS/" + name, x, zipfile.ZIP_DEFLATED)
        for fn, path in images.items():
            z.writestr("OEBPS/" + fn, optimize_image(fn, path), zipfile.ZIP_DEFLATED)
    import xml.etree.ElementTree as ET
    bad = []
    for name, x in list(docs.items()) + [("nav.xhtml", nav_xhtml)]:
        try: ET.fromstring(x.encode("utf-8"))
        except ET.ParseError as e: bad.append("%s: %s" % (name, e))
    for name, x in docs.items():
        for href in re.findall(r'href="([^"#]+)', x):
            if href.endswith(".xhtml") and href not in docs: bad.append("%s → 끊긴 링크 %s" % (name, href))
    if bad:
        print("XHTML 검증 실패: " + " | ".join(bad)); sys.exit(2)
    words = sum(len(re.findall(r"[A-Za-zÁÉÍÓÚÑÜáéíóúñü’']+", re.sub(r"<[^>]+>", " ", x))) for x in docs.values())
    print("OK  %s  · %.2f MB · 문서 %d · 그림 %d · 약 %s 단어" % (OUT, os.path.getsize(OUT) / 1e6, len(docs), len(images), format(words, ",")))

if __name__ == "__main__":
    main()
