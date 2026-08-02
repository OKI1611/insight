# -*- coding: utf-8 -*-
"""소제목 배치 병합 + 검증 → bible/headings/ko.json

  검증: 책명이 books.json 에 있는가 · 장 번호 유효 · 절 번호가 1..절수 범위 ·
        장 내 절 오름차순 · 제목 비어 있지 않음
"""
import json, io, os, glob, sys
sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HD   = os.path.join(ROOT, "bible", "headings")
books = {b["file"]: b for b in json.load(io.open(os.path.join(ROOT, "bible", "books.json"), encoding="utf-8"))}
counts = json.load(io.open(os.path.join(ROOT, "bible", "headings_verse_counts.json"), encoding="utf-8"))

merged, errors = {}, []
for p in sorted(glob.glob(os.path.join(HD, "_batch*.json"))):
    try:
        data = json.load(io.open(p, encoding="utf-8"))
    except Exception as e:
        errors.append("%s: JSON 파싱 실패 — %s" % (os.path.basename(p), e))
        continue
    for bk, chs in data.items():
        if bk not in books:
            errors.append("%s: 알 수 없는 책명 %r" % (os.path.basename(p), bk))
            continue
        dst = merged.setdefault(bk, {})
        for ch, hs in chs.items():
            try:
                ci = int(ch)
            except ValueError:
                errors.append("%s %s: 장 번호가 숫자가 아님 %r" % (bk, ch, ch)); continue
            if not (1 <= ci <= books[bk]["ch"]):
                errors.append("%s: %s장은 존재하지 않음(총 %d장)" % (bk, ch, books[bk]["ch"])); continue
            vmax = counts[bk][str(ci)]
            prev = 0
            clean = []
            for item in hs:
                v, t = int(item[0]), str(item[1]).strip()
                if not t:
                    errors.append("%s %s장 %d절: 제목이 비어 있음" % (bk, ch, v)); continue
                if not (1 <= v <= vmax):
                    errors.append("%s %s장: %d절은 범위(1~%d) 밖" % (bk, ch, v, vmax)); continue
                if v <= prev:
                    errors.append("%s %s장: 절 순서 역전(%d ≤ %d)" % (bk, ch, v, prev)); continue
                prev = v
                clean.append([v, t])
            if ch in dst:
                errors.append("%s %s장: 배치 간 중복 정의" % (bk, ch))
            if clean:
                dst[ch] = clean

total = sum(len(hs) for chs in merged.values() for hs in chs.values())
covered = sum(len(chs) for chs in merged.values())
print("소제목 %d개 · %d개 장 · %d권" % (total, covered, len(merged)))
missing_books = [b for b in books if b not in merged and b != "Psalms"]
if missing_books:
    print("소제목 없는 책(시편 외):", missing_books)

if errors:
    print("\n오류 %d건:" % len(errors))
    for e in errors[:40]:
        print("  -", e)
    sys.exit(1)

out = os.path.join(HD, "ko.json")
io.open(out, "w", encoding="utf-8").write(json.dumps(merged, ensure_ascii=False, indent=1))
print("저장:", out, "· %.0fKB" % (os.path.getsize(out)/1024))
