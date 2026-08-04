# -*- coding: utf-8 -*-
"""TR 정합 배터리 러너 — tools/tr_battery.json 의 전 항목을 검사해 PASS/FAIL 출력.

  검사: ①통절·대형단락 존재(비어 있지 않음) ②TR 특유 어구 수록 ③정량 카운트
        ④금지어 0건 ⑤구조(장 1,189 · 절 31,102)
  실행: python tools/tr_battery_run.py   (실패 있으면 exit 1)
"""
import json, io, os, re, sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BAT = json.load(io.open(os.path.join(ROOT, "tools", "tr_battery.json"), encoding="utf-8"))
books = json.load(io.open(os.path.join(ROOT, "bible", "books.json"), encoding="utf-8"))
NT = {b["file"] for b in books if b.get("nt")}

_cache = {}
def kr(book, ch):
    key = (book, ch)
    if key not in _cache:
        p = os.path.join(ROOT, "bible", "kr", "%s-%d.json" % (book, ch))
        _cache[key] = json.loads(io.open(p, encoding="utf-8-sig").read())
    return _cache[key]

def verse(ref):
    book, ch, v = ref.rsplit("-", 2)
    vs = kr(book, int(ch))
    i = int(v) - 1
    return vs[i] if 0 <= i < len(vs) and isinstance(vs[i], str) else None

fails, passes = [], 0
def check(ok, label, detail=""):
    global passes
    if ok:
        passes += 1
    else:
        fails.append("  FAIL %s %s" % (label, detail))

# ① 통절 존재
for it in BAT["verses_must_exist"]:
    t = verse(it["ref"])
    check(bool(t and t.strip()), "존재 %-18s" % it["ref"], it["reason"])

# ② TR 어구
for it in BAT["tr_phrases"]:
    t = verse(it["ref"]) or ""
    check(it["must"] in t, "어구 %-18s" % it["ref"], "'%s' — %s" % (it["must"], it["reason"]))

# ③④⑤ 전권 스캔
total_ch = total_v = 0
cnt = {c["name"]: 0 for c in BAT["counts"]}
forb = {w: [] for w in BAT["forbidden"]}
for b in books:
    is_nt = b["file"] in NT
    for ch in range(1, b["ch"] + 1):
        vs = kr(b["file"], ch)
        total_ch += 1
        for n, v in enumerate(vs):
            if not isinstance(v, str):
                continue
            total_v += 1
            for c in BAT["counts"]:
                sc = c["scope"]
                if sc == "nt" and not is_nt:
                    continue
                if sc.startswith("books:") and b["file"] not in sc[6:].split(","):
                    continue
                cnt[c["name"]] += v.count(c["pattern"])
            for w in BAT["forbidden"]:
                if w in v and len(forb[w]) < 5:
                    forb[w].append("%s %d:%d" % (b["ko"], ch, n + 1))

for c in BAT["counts"]:
    check(cnt[c["name"]] == c["expect"], "정량 %-18s" % c["name"],
          "기대 %d · 실측 %d" % (c["expect"], cnt[c["name"]]))
for w in BAT["forbidden"]:
    check(not forb[w], "금지어 %-16s" % ("'%s'" % w), " · ".join(forb[w]))
st = BAT["structure"]
check(total_ch == st["chapters"], "구조 장수", "기대 %d · 실측 %d" % (st["chapters"], total_ch))
check(total_v == st["verses"], "구조 절수", "기대 %d · 실측 %d" % (st["verses"], total_v))

n_items = passes + len(fails)
print("TR 배터리: %d항목 중 PASS %d · FAIL %d" % (n_items, passes, len(fails)))
for f in fails:
    print(f)
if not fails:
    print("전 항목 통과 ✓")
sys.exit(1 if fails else 0)
