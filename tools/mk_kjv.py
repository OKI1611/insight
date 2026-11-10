# -*- coding: utf-8 -*-
"""mk_kjv.py — 한국어 성구 약칭 → KJV 본문 조회기 (영문판 『The Millennial Kingdom Explained』 제작용)

  번역 에이전트는 성구를 기억으로 쓰지 말고 반드시 이 도구 출력만 붙인다.
  입력 예: "살전 4:16-17"  "계 20:4-6"  "슥 14:4"  "단 7:8, 23-27"  "겔 40-48장"  "시 2; 72편"  "요한복음 3:16"

  사용
    python tools/mk_kjv.py "살전 4:16-17" "계 20:4-6"
    python tools/mk_kjv.py --scan 책원고/영문판_천년왕국/src_ko/01_*.md   # 파일 안의 모든 성구 참조를 찾아 일괄 출력
    python tools/mk_kjv.py --json "요 10:28"                             # 기계용 JSON
  출력: 영문 참조(1 Thessalonians 4:16–17) + 절 번호가 붙은 KJV 본문. 장 단위 참조는 절 수만 알려 주고
        --full 을 주면 장 전체를 찍는다.
"""
import json, os, re, sys, io, argparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KJV_DIR = os.path.join(ROOT, "bible", "kjv")
BOOKS = json.load(io.open(os.path.join(ROOT, "bible", "books.json"), encoding="utf-8-sig"))

# 개역 관례 약칭(저작권 무관한 관용 약자) — books.json 순서와 1:1
ABBR = ["창","출","레","민","신","수","삿","룻","삼상","삼하","왕상","왕하","대상","대하","스","느","에",
        "욥","시","잠","전","아","사","렘","애","겔","단","호","욜","암","옵","욘","미","나","합","습","학","슥","말",
        "마","막","눅","요","행","롬","고전","고후","갈","엡","빌","골","살전","살후","딤전","딤후","딛","몬",
        "히","약","벧전","벧후","요일","요이","요삼","유","계"]
assert len(ABBR) == len(BOOKS) == 66

EN_NAME = {}   # file → 표기용 영문 이름
KO2FILE = {}
for a, b in zip(ABBR, BOOKS):
    f = b["file"]
    KO2FILE[a] = f
    KO2FILE[b["ko"]] = f
    en = b["en"]
    en = re.sub(r"^([123])(?=[A-Z])", r"\1 ", en)          # 1Thessalonians → 1 Thessalonians
    if en == "SongofSolomon": en = "Song of Solomon"
    EN_NAME[f] = en
# 자주 쓰는 변형 표기
KO2FILE.update({"살전":"1Thessalonians","살후":"2Thessalonians","요한복음":"John","요한일서":"1John",
                "요한이서":"2John","요한삼서":"3John","사도행전":"Acts","로마서":"Romans","히브리서":"Hebrews",
                "요한계시록":"Revelation","계시록":"Revelation","마태복음":"Matthew","마가복음":"Mark","누가복음":"Luke",
                "창세기":"Genesis","출애굽기":"Exodus","레위기":"Leviticus","신명기":"Deuteronomy","이사야":"Isaiah",
                "예레미야":"Jeremiah","에스겔":"Ezekiel","다니엘":"Daniel","스가랴":"Zechariah","시편":"Psalms",
                "잠언":"Proverbs","호세아":"Hosea","요엘":"Joel","아모스":"Amos","미가":"Micah","말라기":"Malachi",
                "고린도전서":"1Corinthians","고린도후서":"2Corinthians","갈라디아서":"Galatians","에베소서":"Ephesians",
                "빌립보서":"Philippians","골로새서":"Colossians","데살로니가전서":"1Thessalonians",
                "데살로니가후서":"2Thessalonians","디모데전서":"1Timothy","디모데후서":"2Timothy","디도서":"Titus",
                "베드로전서":"1Peter","베드로후서":"2Peter","야고보서":"James","유다서":"Jude","열왕기상":"1Kings",
                "열왕기하":"2Kings","사무엘상":"1Samuel","사무엘하":"2Samuel","역대상":"1Chronicles","역대하":"2Chronicles",
                "민수기":"Numbers","여호수아":"Joshua","사사기":"Judges","느헤미야":"Nehemiah","에스더":"Esther",
                "욥기":"Job","전도서":"Ecclesiastes","아가":"SongofSolomon","예레미야애가":"Lamentations",
                "오바댜":"Obadiah","요나":"Jonah","나훔":"Nahum","하박국":"Habakkuk","스바냐":"Zephaniah","학개":"Haggai",
                "룻기":"Ruth","에스라":"Ezra","빌레몬서":"Philemon"})

_cache = {}
def book(f):
    if f not in _cache:
        _cache[f] = json.load(io.open(os.path.join(KJV_DIR, f + ".json"), encoding="utf-8-sig"))
    return _cache[f]

def verses(f, ch, v1=None, v2=None):
    """(file, 장, 시작절, 끝절) → [(절번호, 본문)]"""
    arr = book(f).get(str(ch))
    if arr is None:
        raise ValueError("%s %d장 없음" % (f, ch))
    if v1 is None:
        v1, v2 = 1, len(arr)
    v2 = v2 or v1
    if v2 > len(arr):
        raise ValueError("%s %d:%d — %d장은 %d절까지" % (f, ch, v2, ch, len(arr)))
    return [(v, arr[v - 1]) for v in range(v1, v2 + 1)]

BOOK_RE = "|".join(sorted(map(re.escape, KO2FILE.keys()), key=len, reverse=True))
# "슥 14:4-10", "단 7:8, 23-27", "겔 40-48장", "시 2; 72편", "계 19장", "사 11:6-9; 35장"
REF_RE = re.compile(r"(?P<book>" + BOOK_RE + r")\s*(?P<rest>\d+(?:\s*[:：]\s*\d+(?:\s*[-–~]\s*\d+)?(?:\s*,\s*\d+(?:\s*[-–~]\s*\d+)?)*)?(?:\s*[-–~]\s*\d+)?(?:\s*장|\s*편)?(?:\s*;\s*\d+(?:\s*[:：]\s*\d+(?:\s*[-–~]\s*\d+)?(?:\s*,\s*\d+(?:\s*[-–~]\s*\d+)?)*)?(?:\s*[-–~]\s*\d+)?(?:\s*장|\s*편)?)*)")

def parse(ref):
    """한국어 참조 문자열 → [(file, ch, v1, v2)]  (v1=None 이면 장 전체)"""
    ref = ref.strip().replace("：", ":")
    m = re.match(r"\s*(" + BOOK_RE + r")\s*(.*)$", ref)
    if not m:
        raise ValueError("책 이름을 못 찾음: " + ref)
    f, rest = KO2FILE[m.group(1)], m.group(2)
    out = []
    for seg in re.split(r"\s*;\s*", rest):
        seg = re.sub(r"\s*(장|편)\s*$", "", seg.strip())
        if not seg: continue
        if ":" in seg:
            ch, vs = seg.split(":", 1)
            ch = int(ch)
            for part in re.split(r"\s*,\s*", vs):
                a = re.split(r"\s*[-–~]\s*", part)
                v1 = int(a[0]); v2 = int(a[1]) if len(a) > 1 else v1
                out.append((f, ch, v1, v2))
        else:
            a = re.split(r"\s*[-–~]\s*", seg)
            c1 = int(a[0]); c2 = int(a[1]) if len(a) > 1 else c1
            for ch in range(c1, c2 + 1):
                out.append((f, ch, None, None))
    return out

def en_ref(f, ch, v1=None, v2=None):
    name = EN_NAME[f]
    if f == "Psalms": name = "Psalm"
    if v1 is None: return "%s %d" % (name, ch)
    return "%s %d:%d" % (name, ch, v1) if v1 == v2 else "%s %d:%d–%d" % (name, ch, v1, v2)

def render(ref, full=False):
    lines = []
    for f, ch, v1, v2 in parse(ref):
        if v1 is None and not full:
            n = len(book(f)[str(ch)])
            lines.append("## %s  (whole chapter, %d verses — use --full to print)" % (en_ref(f, ch), n))
            continue
        lines.append("## " + en_ref(f, ch, v1, v2))
        for v, t in verses(f, ch, v1, v2):
            lines.append("%d %s" % (v, t))
    return "\n".join(lines)

def scan_refs(text):
    """본문에서 성구 참조를 모두 찾아 (원문 그대로) 순서대로 돌려준다(중복 제거)."""
    seen, out = set(), []
    for m in REF_RE.finditer(text):
        s = m.group(0).strip()
        if s not in seen:
            seen.add(s); out.append(s)
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("refs", nargs="*")
    ap.add_argument("--scan", nargs="*", help="파일 안의 참조를 모두 찾아 출력")
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass
    refs = list(a.refs)
    for p in a.scan or []:
        refs += scan_refs(io.open(p, encoding="utf-8").read())
    if a.json:
        res = {}
        for r in refs:
            try:
                res[r] = [{"ref": en_ref(f, ch, v1, v2), "verses": verses(f, ch, v1, v2) if (v1 or a.full) else []}
                          for f, ch, v1, v2 in parse(r)]
            except Exception as e:
                res[r] = {"error": str(e)}
        print(json.dumps(res, ensure_ascii=False, indent=1)); return
    for r in refs:
        print("### " + r)
        try: print(render(r, a.full))
        except Exception as e: print("!! ERROR: %s" % e)
        print()

if __name__ == "__main__":
    main()
