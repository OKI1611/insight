# -*- coding: utf-8 -*-
"""정본역(正本譯) 킹제임스 성경 : 헤리티지 에디션 · 한영대역 — EPUB 2.0 빌더

  절마다 한국어 본문과 KJV 영어 본문을 이어서 배치한다.
  (전자책은 화면 폭이 제각각이라 인쇄판의 좌우 2단 대신 위·아래 대역이 읽기 좋다)

  규격: EPUB 2.0 · mimetype STORED 첫 항목 · NCX 2단 목차 — 부크크 외부유통 기준
  소스: bible/books.json + bible/en/<파일>-<장>.json  각 절 {ko, en}
  실행: python tools/build_epub_parallel.py
"""
import json, io, os, re, sys, zipfile, html, uuid, time

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_appendix as APX                       # 앞·뒤 부록(2026-08-05 확정 구성)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "책원고", "정본역킹제임스성경_한영대역.epub")
COVER = os.path.join(ROOT, "책원고", "출판준비", "_cover_parallel.jpg")

books = json.load(io.open(os.path.join(ROOT, "bible", "books.json"), encoding="utf-8"))
E = html.escape
BOOK_ID = str(uuid.uuid4())

# 자체 집필 소제목 + 한글 따옴표류 제거(2026-08-03) — build_pdfs.py 와 동일 규칙
try:
    HEADINGS = json.load(io.open(os.path.join(ROOT, "bible", "headings", "ko.json"), encoding="utf-8"))
except Exception:
    HEADINGS = {}

def headings_for(book, ch):
    return {v: t for v, t in HEADINGS.get(book, {}).get(str(ch), [])}

_KO_QUOTES = re.compile(u'[“”‘’"\'「」『』《》〈〉]')
def clean_ko(s):
    return re.sub(r"\s{2,}", " ", _KO_QUOTES.sub("", str(s))).strip()


def en_ch(b, c):
    p = os.path.join(ROOT, "bible", "en", "%s-%d.json" % (b, c))
    if not os.path.exists(p):
        return None
    return json.loads(io.open(p, encoding="utf-8").read())


# ───────────────── 표지 (큰글자판과 같은 시리즈 디자인) ─────────────────
def make_cover():
    from PIL import Image, ImageDraw, ImageFont
    FD = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Windows\Fonts")
    fb = os.path.join(FD, "NotoSerifCJKkr-Bold.otf")
    fr = os.path.join(FD, "NotoSerifCJKkr-Regular.otf")
    if not os.path.exists(fb):                       # 폴백 — 저장소 동봉 서체
        fb = os.path.join(ROOT, "tools", "fonts", "NotoSerifKR-Bold.ttf")
        fr = os.path.join(ROOT, "tools", "fonts", "NotoSerifKR-Regular.ttf")
    W, H = 1500, 2220
    img = Image.new("RGB", (W, H), (247, 244, 237))
    d = ImageDraw.Draw(img)
    GREEN, INK, GOLD, GRAY = (0, 90, 60), (35, 45, 40), (160, 128, 60), (90, 100, 95)
    d.rectangle([0, 0, W, 26], fill=GREEN)
    d.rectangle([0, H - 26, W, H], fill=GREEN)

    def center(y, txt, fp, size, fill):
        f = ImageFont.truetype(fp, size)
        d.text(((W - d.textlength(txt, font=f)) // 2, y), txt, font=f, fill=fill)

    # 역본명이 길어져 3줄 구성 — 정본역(正本譯) / 킹제임스 성경 / 헤리티지 에디션
    center(280, "B I B L E   I N S I G H T", fr, 42, GOLD)
    center(500, "정본역(正本譯)", fb, 128, INK)
    center(660, "킹제임스 성경", fb, 128, INK)
    center(830, "헤리티지 에디션", fr, 66, GRAY)
    d.line([(W // 2 - 200, 1000), (W // 2 + 200, 1000)], fill=GOLD, width=3)
    center(1070, "한영대역", fb, 96, GREEN)
    center(1220, "한국어 · King James Version · 전 66권", fr, 46, GRAY)
    center(1900, "바이블 인사이트 출판사", fr, 48, GRAY)
    os.makedirs(os.path.dirname(COVER), exist_ok=True)
    img.save(COVER, "JPEG", quality=90)
    return COVER


CSS = """body{font-family:serif;line-height:1.7;margin:0.4em 0.55em;}
h1{font-size:1.5em;text-align:center;margin:1.2em 0 0.9em;color:#00593c;}
h2{font-size:1.2em;margin:1em 0 .6em;color:#00593c;}
h3.sub{font-size:1em;margin:1em 0 .4em;color:#4a5a52;}
p.v{margin:0 0 0.12em 0;text-indent:0;}
p.e{margin:0 0 0.85em 0;text-indent:0;font-size:0.92em;color:#4a5a52;padding-left:0.9em;
    border-left:2px solid #dfe6e1;}
sup.n{font-size:0.62em;color:#2d7a5c;font-weight:bold;padding-right:0.18em;}
p.center{text-align:center;}
a{color:#00593c;text-decoration:none;}
.grid a{display:inline-block;min-width:1.9em;text-align:center;padding:0.28em 0.34em;margin:0.12em;
        border:1px solid #bfcac2;border-radius:0.3em;font-size:1.05em;}
.tocbook{display:block;padding:0.5em 0.2em;border-bottom:1px solid #e2e6e2;font-size:1.08em;}
.small{font-size:0.85em;color:#555;}
.part{margin:1.4em 0 0.4em;font-weight:bold;color:#8a7350;}
""" + APX.EPUB_CSS


def xhtml(title, body):
    return ('<?xml version="1.0" encoding="utf-8"?>\n'
            '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">\n'
            '<html xmlns="http://www.w3.org/1999/xhtml"><head><title>%s</title>'
            '<link rel="stylesheet" type="text/css" href="style.css"/></head><body>%s</body></html>'
            % (E(title), body))


files = []
def add(path, content, fid, mt, spine=True):
    files.append((path, content.encode("utf-8") if isinstance(content, str) else content, fid, mt, spine))


def main():
    t0 = time.time()
    cover = make_cover()
    print("표지 생성:", cover)

    add("OEBPS/cover.xhtml",
        xhtml("표지", '<p class="center"><img src="images/cover.jpg" alt="정본역(正本譯) 킹제임스 성경 : 헤리티지 에디션 한영대역" style="max-width:100%;"/></p>'),
        "cover-page", "application/xhtml+xml")
    add("OEBPS/images/cover.jpg", open(cover, "rb").read(), "cover-img", "image/jpeg", spine=False)
    add("OEBPS/style.css", CSS, "css", "text/css", spine=False)

    front = ('<div style="margin-top:28%;"></div>'
             '<h1 style="font-size:1.9em;">정본역(正本譯) 킹제임스 성경 : 헤리티지 에디션</h1>'
             '<p class="center" style="font-size:1.25em;color:#00593c;font-weight:bold;">한영대역</p>'
             '<p class="center small">THE HERITAGE KJV · AUTHENTIC VERSION · 1611</p>'
             '<div style="margin-top:34%;"></div>'
             '<p class="center">바이블 인사이트 출판사</p>')
    add("OEBPS/titlepage.xhtml", xhtml("속표지", front), "titlepage", "application/xhtml+xml")

    colophon = ('<h1>일러두기 · 판권</h1>'
        '<p><b>도서명</b>  정본역(正本譯) 킹제임스 성경 : 헤리티지 에디션 (한영대역)</p>'
        '<p>‘정본역(正本譯)’은 공인본문(Textus Receptus)과 맛소라 본문을 저본으로 삼았음을 뜻하는 말이며, 다른 번역본의 가치를 부정하는 표현이 아닙니다.</p>'
        '<p>이 책의 한국어 본문은 킹제임스 성경(KJV, 1611)의 영어 본문과 그 저본인 공인본문(Textus Receptus)·맛소라 본문을 '
        '히브리어·아람어·헬라어 원문과 대조하여 바이블 인사이트가 직접 번역한 것입니다. 기존 한국어 역본을 저본으로 삼지 않은 '
        '독자적인 번역이며, 번역 원칙 전문은 biblynote.com/translation 에 공개되어 있습니다.</p>'
        '<p>절마다 한국어 본문을 먼저 싣고 그 아래에 King James Version 영어 본문을 함께 담아, 두 본문을 한 절씩 대조하며 '
        '읽을 수 있도록 하였습니다. 글자 크기는 보시는 기기에서 자유롭게 조정하실 수 있습니다.</p>'
        '<p>본문 소제목은 독자의 이해를 돕기 위하여 바이블 인사이트가 새로 지은 것으로, 성경 원문의 일부가 아닙니다.</p>'
        '<p>영어 본문(King James Version, 1611)은 대한민국 저작권법상 보호 기간이 만료된 퍼블릭 도메인 저작물입니다.</p>'
        '<p>한국어 번역 저작권 ⓒ 오광일 · 바이블 인사이트, 2026. 이 책의 한국어 본문을 출판사의 서면 허락 없이 복제·전재·배포할 수 없습니다. '
        '다만 개인 묵상·설교·강의·논문에서의 통상적인 인용은 출처(정본역(正本譯) 킹제임스 성경 : 헤리티지 에디션)를 밝히는 조건으로 허용합니다.</p>'
        '<p><b>펴낸곳</b>  바이블 인사이트 출판사<br/><b>옮긴이</b>  오광일<br/>'
        '<b>문의</b>  contact@biblynote.com · biblynote.com</p>')
    add("OEBPS/colophon.xhtml", xhtml("판권", colophon), "colophon", "application/xhtml+xml")

    # ── 앞부록(펴내며·번역 원칙·저본·일러두기·약자표) ──
    apx_front = APX.epub_xhtml_sections(APX.resolve_verses(APX.front_sections()))
    for _sid, _ttl, _bd in apx_front:
        add("OEBPS/apx-f-%s.xhtml" % _sid, xhtml(_ttl, _bd), "apxf-%s" % _sid, "application/xhtml+xml")

    toc = ['<h1>목차</h1>', '<p class="part">구약전서</p>']
    nt_done = False
    for i, bk in enumerate(books):
        if bk.get("nt") and not nt_done:
            toc.append('<p class="part">신약전서</p>'); nt_done = True
        toc.append('<a class="tocbook" href="b%02d.xhtml">%s <span class="small">%s · %d장</span></a>'
                   % (i, E(bk["ko"]), E(bk["en"]), bk["ch"]))
    add("OEBPS/toc.xhtml", xhtml("목차", "".join(toc)), "tocpage", "application/xhtml+xml")

    total_v = 0
    for i, bk in enumerate(books):
        grid = "".join('<a href="b%02dc%03d.xhtml">%d</a>' % (i, c, c) for c in range(1, bk["ch"] + 1))
        bb = ('<div style="margin-top:16%%;"></div><h1 style="font-size:1.8em;">%s</h1>'
              '<p class="center small">%s</p><div class="grid" style="text-align:center;margin-top:1.2em;">%s</div>'
              '<p class="center" style="margin-top:2em;"><a href="toc.xhtml">← 전체 목차</a></p>'
              ) % (E(bk["ko"]), E(bk["en"]), grid)
        add("OEBPS/b%02d.xhtml" % i, xhtml(bk["ko"], bb), "b%02d" % i, "application/xhtml+xml")

        for c in range(1, bk["ch"] + 1):
            vs = en_ch(bk["file"], c) or []
            hd = headings_for(bk["file"], c)
            parts = []
            for n, v in enumerate(vs):
                ko = clean_ko(v.get("ko") or "")
                en = (v.get("en") or "").strip()
                if (n + 1) in hd:
                    parts.append('<h3 class="sub">%s</h3>' % E(hd[n + 1]))
                if ko:
                    parts.append('<p class="v" id="v%d"><sup class="n">%d</sup>%s</p>' % (n + 1, n + 1, E(ko)))
                if en:
                    parts.append('<p class="e">%s</p>' % E(en))
                total_v += 1
            nav = ('<p class="center small"><a href="b%02d.xhtml">%s 장 목차</a> · '
                   '<a href="toc.xhtml">전체 목차</a></p>') % (i, E(bk["ko"]))
            body = '<h2>%s %d장</h2>%s%s' % (E(bk["ko"]), c, "".join(parts), nav)
            add("OEBPS/b%02dc%03d.xhtml" % (i, c), xhtml("%s %d장" % (bk["ko"], c), body),
                "b%02dc%03d" % (i, c), "application/xhtml+xml")
        if (i + 1) % 20 == 0:
            print("  %d/66권 %.0fs" % (i + 1, time.time() - t0), flush=True)

    # ── 뒤부록(교리 용어·원어 도표·구원의 길·환산표·KJV 고어 사전·QR) ──
    apx_back = APX.epub_xhtml_sections(APX.resolve_verses(APX.back_sections("parallel")))
    for _sid, _ttl, _bd in apx_back:
        add("OEBPS/apx-b-%s.xhtml" % _sid, xhtml(_ttl, _bd), "apxb-%s" % _sid, "application/xhtml+xml")
    add("OEBPS/images/qr.png", open(APX.QR_PNG, "rb").read(), "qr-img", "image/png", spine=False)

    manifest = "\n".join('<item id="%s" href="%s" media-type="%s"/>' % (fid, path.replace("OEBPS/", ""), mt)
                         for path, _, fid, mt, _ in files)
    manifest += '\n<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>'
    spine = "\n".join('<itemref idref="%s"/>' % fid for _, _, fid, _, sp in files if sp)
    opf = ('<?xml version="1.0" encoding="utf-8"?>\n'
        '<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="bid" version="2.0">\n'
        '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">\n'
        '<dc:title>정본역(正本譯) 킹제임스 성경 : 헤리티지 에디션 (한영대역)</dc:title>\n'
        '<dc:creator opf:role="trl">오광일</dc:creator>\n'
        '<dc:publisher>바이블 인사이트 출판사</dc:publisher>\n'
        '<dc:language>ko</dc:language>\n<dc:language>en</dc:language>\n'
        '<dc:identifier id="bid">urn:uuid:%s</dc:identifier>\n'
        '<dc:date>2026</dc:date>\n'
        '<dc:description>킹제임스 성경(KJV, 1611) 영어 본문과 새로 옮긴 한국어 본문을 절 단위로 대조한 한영대역 성경.</dc:description>\n'
        '<meta name="cover" content="cover-img"/>\n'
        '</metadata>\n<manifest>\n%s\n</manifest>\n<spine toc="ncx">\n%s\n</spine>\n'
        '<guide><reference type="cover" title="표지" href="cover.xhtml"/>'
        '<reference type="toc" title="목차" href="toc.xhtml"/></guide>\n</package>') % (BOOK_ID, manifest, spine)

    # NCX — 부모(권)가 자식(장)보다 playOrder 가 앞서도록 순차 생성
    np, order = [], 1
    def leaf(pid, label, src):
        nonlocal order
        s = ('<navPoint id="%s" playOrder="%d"><navLabel><text>%s</text></navLabel>'
             '<content src="%s"/></navPoint>') % (pid, order, E(label), src)
        order += 1
        return s
    np.append(leaf("np-cover", "표지", "cover.xhtml"))
    np.append(leaf("np-title", "속표지", "titlepage.xhtml"))
    np.append(leaf("np-colo", "판권", "colophon.xhtml"))
    for _sid, _ttl, _bd in apx_front:
        np.append(leaf("np-apxf-%s" % _sid, _ttl, "apx-f-%s.xhtml" % _sid))
    np.append(leaf("np-toc", "목차", "toc.xhtml"))
    for i, bk in enumerate(books):
        parent = ('<navPoint id="np-b%02d" playOrder="%d"><navLabel><text>%s</text></navLabel>'
                  '<content src="b%02d.xhtml"/>') % (i, order, E(bk["ko"]), i)
        order += 1
        kids = []
        for c in range(1, bk["ch"] + 1):
            kids.append(('<navPoint id="np-b%02dc%03d" playOrder="%d"><navLabel><text>%s %d장</text></navLabel>'
                         '<content src="b%02dc%03d.xhtml"/></navPoint>') % (i, c, order, E(bk["ko"]), c, i, c))
            order += 1
        np.append(parent + "".join(kids) + "</navPoint>")
    for _sid, _ttl, _bd in apx_back:
        np.append(leaf("np-apxb-%s" % _sid, _ttl, "apx-b-%s.xhtml" % _sid))
    ncx = ('<?xml version="1.0" encoding="utf-8"?>\n'
        '<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">\n'
        '<head><meta name="dtb:uid" content="urn:uuid:%s"/><meta name="dtb:depth" content="2"/>'
        '<meta name="dtb:totalPageCount" content="0"/><meta name="dtb:maxPageNumber" content="0"/></head>\n'
        '<docTitle><text>정본역(正本譯) 킹제임스 성경 : 헤리티지 에디션 (한영대역)</text></docTitle>\n'
        '<navMap>%s</navMap></ncx>') % (BOOK_ID, "".join(np))

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with zipfile.ZipFile(OUT, "w") as z:
        z.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        z.writestr("META-INF/container.xml",
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">'
            '<rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>'
            '</rootfiles></container>', compress_type=zipfile.ZIP_DEFLATED)
        z.writestr("OEBPS/content.opf", opf, compress_type=zipfile.ZIP_DEFLATED)
        z.writestr("OEBPS/toc.ncx", ncx, compress_type=zipfile.ZIP_DEFLATED)
        for path, data, fid, mt, sp in files:
            z.writestr(path, data, compress_type=zipfile.ZIP_DEFLATED)

    print("EPUB 저장: %s\n  %.2fMB · 항목 %d · navPoint %d · 절 %s · %.0fs"
          % (OUT, os.path.getsize(OUT) / 1e6, len(files) + 2, order - 1,
             format(total_v, ","), time.time() - t0))


if __name__ == "__main__":
    main()
