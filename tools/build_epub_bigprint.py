# -*- coding: utf-8 -*-
"""인사이트 킹제임스 성경 · 큰글자판 — EPUB 2.0 빌더

  부크크 외부유통 규격: EPUB 2.0 · mimetype STORED 첫 항목 · NCX 목차
  2026-08-03: '한글 전용' 표기 삭제 · 자체 집필 소제목 수록 · 한글 따옴표류 제거
  실행: python tools/build_epub_bigprint.py
"""
import json, io, os, re, sys, zipfile, html, uuid

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(ROOT, "책원고", "인사이트킹제임스성경_큰글자판.epub")
COVER_JPG = os.path.join(ROOT, "책원고", "출판준비", "_cover_bigprint.jpg")

books = json.load(io.open(os.path.join(ROOT, "bible", "books.json"), encoding="utf-8"))
def kr(b, c):
    return json.loads(io.open(os.path.join(ROOT, "bible", "kr", f"{b}-{c}.json"), encoding="utf-8-sig").read())

try:
    HEADINGS = json.load(io.open(os.path.join(ROOT, "bible", "headings", "ko.json"), encoding="utf-8"))
except Exception:
    HEADINGS = {}
def headings_for(book, ch):
    return {v: t for v, t in HEADINGS.get(book, {}).get(str(ch), [])}

_KO_QUOTES = re.compile(u'[“”‘’"\'「」『』《》〈〉]')
def clean_ko(s):
    return re.sub(r"\s{2,}", " ", _KO_QUOTES.sub("", str(s))).strip()

BOOK_ID = str(uuid.uuid4())
E = html.escape

# ── 표지 이미지 ──
from PIL import Image, ImageDraw, ImageFont
FD = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Windows\Fonts")
f_bold = os.path.join(FD, "NotoSerifCJKkr-Bold.otf")
f_reg  = os.path.join(FD, "NotoSerifCJKkr-Regular.otf")
if not os.path.exists(f_bold):
    f_bold = os.path.join(ROOT, "tools", "fonts", "NotoSerifKR-Bold.ttf")
    f_reg  = os.path.join(ROOT, "tools", "fonts", "NotoSerifKR-Regular.ttf")
W, H = 1500, 2220
img = Image.new("RGB", (W, H), (247, 244, 237))
d = ImageDraw.Draw(img)
GREEN = (0, 90, 60); INK = (35, 45, 40); GOLD = (160, 128, 60)
d.rectangle([0, 0, W, 26], fill=GREEN); d.rectangle([0, H-26, W, H], fill=GREEN)
def center(y, txt, fp, size, fill):
    f = ImageFont.truetype(fp, size)
    d.text(((W - d.textlength(txt, font=f)) // 2, y), txt, font=f, fill=fill)
center(300, "B I B L E   I N S I G H T", f_reg, 44, GOLD)
center(560, "인사이트", f_bold, 150, INK)
center(740, "킹제임스 성경", f_bold, 150, INK)
d.line([(W//2-200, 1030), (W//2+200, 1030)], fill=GOLD, width=3)
center(1100, "큰글자판", f_bold, 96, GREEN)
center(1250, "전 66권", f_reg, 52, (90, 100, 95))
center(1900, "바이블 인사이트 출판사", f_reg, 48, (90, 100, 95))
os.makedirs(os.path.dirname(COVER_JPG), exist_ok=True)
img.save(COVER_JPG, "JPEG", quality=90)
print("표지 생성:", COVER_JPG)

CSS = """body{font-family:serif;line-height:1.85;margin:0.4em 0.55em;font-size:118%;}
h1{font-size:1.5em;text-align:center;margin:1.2em 0 0.9em;color:#00593c;}
h2{font-size:1.2em;margin:1em 0 .6em;color:#00593c;}
h3.sub{font-size:1.02em;margin:1em 0 .45em;color:#4a5a52;}
p.v{margin:0 0 0.55em 0;text-indent:0;}
sup.n{font-size:0.62em;color:#2d7a5c;font-weight:bold;padding-right:0.18em;}
p.center{text-align:center;}
a{color:#00593c;text-decoration:none;}
.grid a{display:inline-block;min-width:1.9em;text-align:center;padding:0.28em 0.34em;margin:0.12em;
        border:1px solid #bfcac2;border-radius:0.3em;font-size:1.05em;}
.tocbook{display:block;padding:0.5em 0.2em;border-bottom:1px solid #e2e6e2;font-size:1.08em;}
.small{font-size:0.85em;color:#555;}
.part{margin:1.4em 0 0.4em;font-weight:bold;color:#8a7350;}
"""

def xhtml(title, body):
    return ('<?xml version="1.0" encoding="utf-8"?>\n'
            '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">\n'
            '<html xmlns="http://www.w3.org/1999/xhtml"><head><title>%s</title>'
            '<link rel="stylesheet" type="text/css" href="style.css"/></head><body>%s</body></html>' % (E(title), body))

files = []
def add(path, content, fid, mt, spine=True):
    files.append((path, content.encode("utf-8") if isinstance(content, str) else content, fid, mt, spine))

add("OEBPS/cover.xhtml", xhtml("표지", '<p class="center"><img src="images/cover.jpg" alt="인사이트 킹제임스 성경 큰글자판" style="max-width:100%;"/></p>'), "cover-page", "application/xhtml+xml")
add("OEBPS/images/cover.jpg", open(COVER_JPG, "rb").read(), "cover-img", "image/jpeg", spine=False)
add("OEBPS/style.css", CSS, "css", "text/css", spine=False)

front = ('<div style="margin-top:28%;"></div>'
 '<h1 style="font-size:1.9em;">인사이트 킹제임스 성경</h1>'
 '<p class="center" style="font-size:1.25em;color:#00593c;font-weight:bold;">큰글자판</p>'
 '<p class="center small">THE INSIGHT KING JAMES BIBLE · 1611</p>'
 '<div style="margin-top:34%;"></div>'
 '<p class="center">바이블 인사이트 출판사</p>')
add("OEBPS/titlepage.xhtml", xhtml("속표지", front), "titlepage", "application/xhtml+xml")

colophon = ('<h1>일러두기 · 판권</h1>'
 '<p><b>도서명</b>  인사이트 킹제임스 성경 (큰글자판)</p>'
 '<p>이 책의 한국어 본문은 킹제임스 성경(KJV, 1611)의 영어 본문과 그 저본인 공인본문(Textus Receptus)·맛소라 본문을 '
 '히브리어·아람어·헬라어 원문과 대조하여 바이블 인사이트가 직접 번역한 것입니다. 기존 한국어 역본을 저본으로 삼지 않은 '
 '독자적인 번역이며, 번역 원칙 전문은 biblynote.com/translation 에 공개되어 있습니다.</p>'
 '<p>본문 소제목은 독자의 이해를 돕기 위하여 바이블 인사이트가 새로 지은 것으로, 성경 원문의 일부가 아닙니다.</p>'
 '<p>글자 크기는 보시는 기기에서 자유롭게 더 키우실 수 있습니다. 이 책은 눈이 편안하도록 기본 글자를 크게 하고 줄 간격을 넉넉하게 담았습니다.</p>'
 '<p>한국어 번역 저작권 ⓒ 오광일 · 바이블 인사이트, 2026. 이 책의 한국어 본문을 출판사의 서면 허락 없이 복제·전재·배포할 수 없습니다. '
 '다만 개인 묵상·설교·강의·논문에서의 통상적인 인용은 출처(인사이트 킹제임스 성경)를 밝히는 조건으로 허용합니다.</p>'
 '<p><b>펴낸곳</b>  바이블 인사이트 출판사<br/><b>옮긴이</b>  오광일<br/>'
 '<b>문의</b>  contact@biblynote.com · biblynote.com</p>')
add("OEBPS/colophon.xhtml", xhtml("판권", colophon), "colophon", "application/xhtml+xml")

toc_body = ['<h1>목차</h1>', '<p class="part">구약전서</p>']
for i, bk in enumerate(books):
    if bk.get("nt") and '<p class="part">신약전서</p>' not in toc_body:
        toc_body.append('<p class="part">신약전서</p>')
    toc_body.append('<a class="tocbook" href="b%02d.xhtml">%s <span class="small">%s · %d장</span></a>' % (i, E(bk["ko"]), E(bk["en"]), bk["ch"]))
add("OEBPS/toc.xhtml", xhtml("목차", "".join(toc_body)), "tocpage", "application/xhtml+xml")

for i, bk in enumerate(books):
    grid = "".join('<a href="b%02dc%03d.xhtml">%d</a>' % (i, c, c) for c in range(1, bk["ch"]+1))
    bb = ('<div style="margin-top:16%%;"></div><h1 style="font-size:1.8em;">%s</h1>'
          '<p class="center small">%s</p><div class="grid" style="text-align:center;margin-top:1.2em;">%s</div>'
          '<p class="center" style="margin-top:2em;"><a href="toc.xhtml">← 전체 목차</a></p>') % (E(bk["ko"]), E(bk["en"]), grid)
    add("OEBPS/b%02d.xhtml" % i, xhtml(bk["ko"], bb), "b%02d" % i, "application/xhtml+xml")
    for c in range(1, bk["ch"]+1):
        vs = kr(bk["file"], c)
        hd = headings_for(bk["file"], c)
        parts = []
        for n, v in enumerate(vs):
            if not isinstance(v, str):
                continue
            if (n+1) in hd:
                parts.append('<h3 class="sub">%s</h3>' % E(hd[n+1]))
            parts.append('<p class="v" id="v%d"><sup class="n">%d</sup>%s</p>' % (n+1, n+1, E(clean_ko(v))))
        nav = '<p class="center small"><a href="b%02d.xhtml">%s 장 목차</a> · <a href="toc.xhtml">전체 목차</a></p>' % (i, E(bk["ko"]))
        cb = '<h2>%s %d장</h2>%s%s' % (E(bk["ko"]), c, "".join(parts), nav)
        add("OEBPS/b%02dc%03d.xhtml" % (i, c), xhtml("%s %d장" % (bk["ko"], c), cb), "b%02dc%03d" % (i, c), "application/xhtml+xml")

manifest = "\n".join('<item id="%s" href="%s" media-type="%s"/>' % (fid, path.replace("OEBPS/", ""), mt)
                     for path, _, fid, mt, _ in files)
manifest += '\n<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>'
spine = "\n".join('<itemref idref="%s"/>' % fid for path, _, fid, mt, sp in files if sp)
opf = ('<?xml version="1.0" encoding="utf-8"?>\n'
 '<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="bid" version="2.0">\n'
 '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">\n'
 '<dc:title>인사이트 킹제임스 성경 (큰글자판)</dc:title>\n'
 '<dc:creator opf:role="trl">오광일</dc:creator>\n'
 '<dc:publisher>바이블 인사이트 출판사</dc:publisher>\n'
 '<dc:language>ko</dc:language>\n'
 '<dc:identifier id="bid">urn:uuid:%s</dc:identifier>\n'
 '<dc:date>2026</dc:date>\n'
 '<meta name="cover" content="cover-img"/>\n'
 '</metadata>\n<manifest>\n%s\n</manifest>\n<spine toc="ncx">\n%s\n</spine>\n'
 '<guide><reference type="cover" title="표지" href="cover.xhtml"/>'
 '<reference type="toc" title="목차" href="toc.xhtml"/></guide>\n</package>') % (BOOK_ID, manifest, spine)

np_xml = []; order = 1
def navp(pid, label, src):
    global order
    s = '<navPoint id="%s" playOrder="%d"><navLabel><text>%s</text></navLabel><content src="%s"/></navPoint>' % (pid, order, E(label), src)
    order += 1
    return s
np_xml.append(navp("np-cover", "표지", "cover.xhtml"))
np_xml.append(navp("np-title", "속표지", "titlepage.xhtml"))
np_xml.append(navp("np-colo", "판권", "colophon.xhtml"))
np_xml.append(navp("np-toc", "목차", "toc.xhtml"))
for i, bk in enumerate(books):
    parent = '<navPoint id="np-b%02d" playOrder="%d"><navLabel><text>%s</text></navLabel><content src="b%02d.xhtml"/>' % (i, order, E(bk["ko"]), i)
    order += 1
    kids = []
    for c in range(1, bk["ch"]+1):
        kids.append('<navPoint id="np-b%02dc%03d" playOrder="%d"><navLabel><text>%s %d장</text></navLabel><content src="b%02dc%03d.xhtml"/></navPoint>' % (i, c, order, E(bk["ko"]), c, i, c))
        order += 1
    np_xml.append(parent + "".join(kids) + "</navPoint>")
ncx = ('<?xml version="1.0" encoding="utf-8"?>\n'
 '<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">\n'
 '<head><meta name="dtb:uid" content="urn:uuid:%s"/><meta name="dtb:depth" content="2"/>'
 '<meta name="dtb:totalPageCount" content="0"/><meta name="dtb:maxPageNumber" content="0"/></head>\n'
 '<docTitle><text>인사이트 킹제임스 성경 (큰글자판)</text></docTitle>\n'
 '<navMap>%s</navMap></ncx>') % (BOOK_ID, "".join(np_xml))

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with zipfile.ZipFile(OUT, "w") as z:
    z.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
    z.writestr("META-INF/container.xml",
        '<?xml version="1.0" encoding="utf-8"?>\n<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">'
        '<rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>',
        compress_type=zipfile.ZIP_DEFLATED)
    z.writestr("OEBPS/content.opf", opf, compress_type=zipfile.ZIP_DEFLATED)
    z.writestr("OEBPS/toc.ncx", ncx, compress_type=zipfile.ZIP_DEFLATED)
    for path, data, fid, mt, sp in files:
        z.writestr(path, data, compress_type=zipfile.ZIP_DEFLATED)

print("EPUB 저장:", OUT, "|", round(os.path.getsize(OUT)/1e6, 2), "MB | 파일", len(files)+2)
