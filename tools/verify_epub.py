# -*- coding: utf-8 -*-
"""EPUB 2.0 규격 검증 — mimetype·컨테이너·OPF·NCX·XHTML 파싱·링크 무결성"""
import sys, io, os, zipfile, re
import xml.etree.ElementTree as ET
sys.stdout.reconfigure(encoding="utf-8")

P = sys.argv[1] if len(sys.argv) > 1 else r"책원고\정본역킹제임스성경_한영대역.epub"
z = zipfile.ZipFile(P)
names = z.namelist()
ok = True
def chk(label, cond, detail=""):
    global ok
    ok = ok and cond
    print("  %s %-42s %s" % ("PASS" if cond else "FAIL", label, detail))

print("파일:", P, "· %.2fMB · 항목 %d" % (os.path.getsize(P)/1e6, len(names)))

# 1) mimetype
i0 = z.infolist()[0]
chk("mimetype 이 첫 항목", i0.filename == "mimetype", i0.filename)
chk("mimetype 무압축(STORED)", i0.compress_type == zipfile.ZIP_STORED)
chk("mimetype 내용", z.read("mimetype") == b"application/epub+zip")

# 2) container
chk("META-INF/container.xml 존재", "META-INF/container.xml" in names)
root = ET.fromstring(z.read("META-INF/container.xml"))
rf = root.find(".//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile")
opf_path = rf.get("full-path")
chk("rootfile 경로 유효", opf_path in names, opf_path)

# 3) OPF
opf = ET.fromstring(z.read(opf_path))
NS = {"opf": "http://www.idpf.org/2007/opf", "dc": "http://purl.org/dc/elements/1.1/"}
title = opf.find(".//dc:title", NS).text
langs = [e.text for e in opf.findall(".//dc:language", NS)]
chk("dc:title", bool(title), title)
is_parallel = "en" in langs                       # 한영대역판인지 — 이후 검사 분기
chk("dc:language 유효", "ko" in langs, str(langs) + (" · 한영대역" if is_parallel else " · 한글 전용"))
chk("dc:publisher", opf.find(".//dc:publisher", NS).text == "바이블 인사이트 출판사")

items = {it.get("id"): it.get("href") for it in opf.findall(".//opf:manifest/opf:item", NS)}
base = os.path.dirname(opf_path)
missing = [h for h in items.values() if (base + "/" + h) not in names]
chk("manifest 파일 모두 존재", not missing, "누락 %d" % len(missing))

spine = [ir.get("idref") for ir in opf.findall(".//opf:spine/opf:itemref", NS)]
chk("spine 항목이 manifest 에 있음", all(s in items for s in spine), "%d편" % len(spine))
chk("spine toc=ncx 지정", opf.find(".//opf:spine", NS).get("toc") == "ncx")

# 4) NCX — playOrder 중복·순서
ncx = ET.fromstring(z.read(base + "/toc.ncx"))
NN = {"n": "http://www.daisy.org/z3986/2005/ncx/"}
pts = ncx.findall(".//n:navPoint", NN)
orders = [int(p.get("playOrder")) for p in pts]
chk("navPoint 수", len(pts) > 1200, "%d개" % len(pts))
chk("playOrder 중복 없음", len(orders) == len(set(orders)))
chk("playOrder 1..N 연속", sorted(orders) == list(range(1, len(orders) + 1)))
ncx_src = {p.find("n:content", NN).get("src").split("#")[0] for p in pts}
chk("NCX 대상 파일 모두 존재", all((base + "/" + s) in names for s in ncx_src))

# 5) XHTML 파싱 (DTD 미해석 위해 doctype 제거 후 파싱)
bad = []
xh = [n for n in names if n.endswith(".xhtml")]
for n in xh:
    s = z.read(n).decode("utf-8")
    s = re.sub(r"<!DOCTYPE[^>]*>", "", s, count=1)
    try:
        ET.fromstring(s)
    except Exception as e:
        bad.append((n, str(e)[:60]))
chk("XHTML 파싱 오류 없음", not bad, "%d/%d" % (len(xh) - len(bad), len(xh)))
for n, e in bad[:5]:
    print("      ", n, e)

# 6) 내부 링크 무결성
broken = set()
for n in xh:
    s = z.read(n).decode("utf-8")
    for href in re.findall(r'href="([^"]+)"', s):
        if href.startswith(("http", "mailto:")) or href.endswith(".css"):
            continue
        tgt = href.split("#")[0]
        if tgt and (base + "/" + tgt) not in names:
            broken.add((n, href))
chk("내부 링크 끊김 없음", not broken, "%d건" % len(broken))

# 7) 본문 표본 — 한/영 대역이 실제로 들어갔는지
sample = z.read(base + "/b42c003.xhtml").decode("utf-8")   # 요한복음 3장
chk("본문 한국어 수록", "하나님이 세상을" in sample or "독생자" in sample)
if is_parallel:                                   # 영어 수록은 한영대역판에만 해당
    chk("본문 KJV 영어 수록", "God so loved the world" in sample)
m = re.search(r'<p class="v" id="v16">.*?</p>\s*<p class="e">(.*?)</p>', sample, re.S)
if m:
    print("\n  [요한복음 3:16 대역 확인]")
    k = re.search(r'<p class="v" id="v16"><sup class="n">16</sup>(.*?)</p>', sample, re.S)
    print("    한 ", (k.group(1) if k else "")[:70])
    print("    영 ", m.group(1)[:70])

print("\n종합:", "적합 — 유통 규격 통과" if ok else "부적합 — 위 FAIL 항목 수정 필요")
sys.exit(0 if ok else 1)
