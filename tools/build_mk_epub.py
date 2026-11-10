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
PUBLISHER = "BIBLY Bible Insight"
LANG = "en"
BOOK_ID = "urn:uuid:" + str(uuid.uuid5(uuid.NAMESPACE_URL, "https://biblynote.com/books/millennium-en"))

# 파일 → (표시 제목, 그룹) — 파트 머리 페이지는 START_PART 에 지정
PARTS = {
    "01": ("Part One", "Identity", "What Is the Millennial Kingdom?"),
    "05": ("Part Two", "Arrival", "How Does the Kingdom Come?"),
    "10": ("Part Three", "People", "Who Enters, and How Do They Live?"),
    "18": ("Part Four", "Kingdom", "The Stage and the System"),
    "25": ("Part Five", "Completion", "The End of the Thousand Years, and Eternity"),
}
APPENDIX_START = "30_appendix_A"

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
"""

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
    body = re.sub(r"<h1>Chapter (\d+)\.\s*(.*?)</h1>", r'<h1><span class="num">Chapter \1</span>\2</h1>', body, count=1)
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
    ap = argparse.ArgumentParser(); ap.add_argument("--strict", action="store_true"); a = ap.parse_args()
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
        add_doc("cover.xhtml", "Cover", '<div style="text-align:center;margin:0;padding:0"><img src="cover.jpg" alt="Cover" style="max-height:100%;max-width:100%"/></div>', ' style="margin:0;padding:0"')
    add_doc("title.xhtml", "Title Page",
            '<div class="titlepage"><p class="t">%s</p><p class="s">%s</p><p class="a">%s</p><p class="p">%s<br/>biblynote.com</p></div>' % (E(TITLE), E(SUBTITLE), E(AUTHOR), E(PUBLISHER)))
    copyright_md = os.path.join(EN, "36_colophon.md")
    if os.path.exists(copyright_md):
        add_doc("copyright.xhtml", "Copyright", '<div class="copyright">%s</div>' % md_to_xhtml(io.open(copyright_md, encoding="utf-8").read()))

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
        body = md_to_xhtml(md_text)
        for fm in re.finditer(r'src="(fig-[^"]+)"', body):
            fp = os.path.join(FIG, fm.group(1))
            if os.path.exists(fp): images[fm.group(1)] = fp
            else: missing_fig.append((name, fm.group(1)))
        level = 2 if (num.isdigit() and name[:2] in [f"{i:02d}" for i in range(1, 29)]) or name.startswith("3") and "appendix" in name else 1
        add_doc(name + ".xhtml", title, body, level=level)

    # 3) 차례 페이지(본문 안 TOC)
    toc_html = ['<h1>Contents</h1><div class="toc">']
    for level, title, name in nav:
        if name in ("cover.xhtml", "title.xhtml", "copyright.xhtml", "toc.xhtml"): continue
        toc_html.append('<p class="%s"><a href="%s">%s</a></p>' % ("l2" if level == 2 else "l1", name, E(title)))
    toc_html.append("</div>")
    toc_doc = XHTML % ("Contents", "", "\n".join(toc_html))
    docs["toc.xhtml"] = toc_doc
    # 차례는 판권 다음에 끼운다
    pos = spine.index("copyright.xhtml") + 1 if "copyright.xhtml" in spine else (2 if has_cover else 1)
    spine.insert(pos, "toc.xhtml"); nav.insert(pos, (1, "Contents", "toc.xhtml"))

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
           '<dc:rights>Copyright © 2026 %s. All rights reserved.</dc:rights>'
           '<meta property="dcterms:modified">%s</meta>%s'
           '</metadata><manifest>%s</manifest><spine toc="ncx">%s</spine></package>') % (
        BOOK_ID, E(TITLE), E(SUBTITLE), E(AUTHOR), LANG, E(PUBLISHER), time.strftime("%Y-%m-%d"), E(AUTHOR),
        time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        '<meta name="cover" content="img0"/>' if has_cover else "",
        "".join(man), "".join('<itemref idref="%s"%s/>' % (ids[n], ' linear="no"' if n == "cover.xhtml" else "") for n in spine))

    # 6) zip
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
    words = sum(len(re.findall(r"[A-Za-z’']+", re.sub(r"<[^>]+>", " ", x))) for x in docs.values())
    print("OK  %s  · %.2f MB · 문서 %d · 그림 %d · 약 %s 단어" % (OUT, os.path.getsize(OUT) / 1e6, len(docs), len(images), format(words, ",")))

if __name__ == "__main__":
    main()
