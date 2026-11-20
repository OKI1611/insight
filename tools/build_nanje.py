# -*- coding: utf-8 -*-
"""성경 난제 풀이 → 질의응답(content/qna.json) 빌드

원고: tools/nanje/NNN.json  (한 편당 한 파일, 성경 순서대로 번호)
  {
    "q": "질문(제목)",
    "a": "한두 문장 결론(목록 미리보기·글 첫머리)",
    "verses": ["창 37:28", "창 37:36"],      # 본문 상자에 넣을 구절 — 글자는 정본역에서 자동으로 가져온다
    "sections": [{"h": "소제목", "p": ["문단", "문단"]}],
    "points": ["한눈에 정리 1", "…"],
    "tags": ["요셉", "…"],
    "more": ["삿 8:24"],                     # (선택) 말씀 칩에만 추가로 보일 구절
    "cat": "삶의 질문"                       # (선택) 기본은 「성경 난제」. 101번 이후 일반 주제는 분류를 따로 준다
  }

구절 글자를 원고에 직접 쓰지 않는다 — 정본역(bible/kr)을 고친 뒤 이 스크립트만 다시 돌리면 그대로 반영된다.
실행:  python tools/build_nanje.py        (→ content/qna.json 의 gen-nanje-* 항목을 통째로 다시 만든다)
       python tools/build_nanje.py --check  (구절만 검사, 저장 안 함)
"""
import glob
import html
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "tools", "nanje")
QNA = os.path.join(ROOT, "content", "qna.json")
CAT = "성경 난제"
PREFIX = "gen-nanje-"

ABBR = {'창': 'Genesis', '출': 'Exodus', '레': 'Leviticus', '민': 'Numbers', '신': 'Deuteronomy', '수': 'Joshua', '삿': 'Judges', '룻': 'Ruth',
        '삼상': '1Samuel', '삼하': '2Samuel', '왕상': '1Kings', '왕하': '2Kings', '대상': '1Chronicles', '대하': '2Chronicles', '스': 'Ezra',
        '느': 'Nehemiah', '에': 'Esther', '욥': 'Job', '시': 'Psalms', '잠': 'Proverbs', '전': 'Ecclesiastes', '아': 'SongofSolomon',
        '사': 'Isaiah', '렘': 'Jeremiah', '애': 'Lamentations', '겔': 'Ezekiel', '단': 'Daniel', '호': 'Hosea', '욜': 'Joel', '암': 'Amos',
        '옵': 'Obadiah', '욘': 'Jonah', '미': 'Micah', '나': 'Nahum', '합': 'Habakkuk', '습': 'Zephaniah', '학': 'Haggai', '슥': 'Zechariah',
        '말': 'Malachi', '마': 'Matthew', '막': 'Mark', '눅': 'Luke', '요': 'John', '행': 'Acts', '롬': 'Romans', '고전': '1Corinthians',
        '고후': '2Corinthians', '갈': 'Galatians', '엡': 'Ephesians', '빌': 'Philippians', '골': 'Colossians', '살전': '1Thessalonians',
        '살후': '2Thessalonians', '딤전': '1Timothy', '딤후': '2Timothy', '딛': 'Titus', '몬': 'Philemon', '히': 'Hebrews', '약': 'James',
        '벧전': '1Peter', '벧후': '2Peter', '요일': '1John', '요이': '2John', '요삼': '3John', '유': 'Jude', '계': 'Revelation'}
KO = {b["file"]: b["ko"] for b in json.load(open(os.path.join(ROOT, "bible", "books.json"), encoding="utf-8"))}
_cache = {}


def parse(ref):
    m = re.match(r"^\s*([가-힣]+)\s*(\d+):(\d+)(?:\s*[-~]\s*(\d+))?\s*$", ref)
    if not m or m.group(1) not in ABBR:
        raise SystemExit(f"구절 표기 오류: {ref!r}")
    f = ABBR[m.group(1)]
    a = int(m.group(3))
    return f, int(m.group(2)), a, int(m.group(4) or a)


def verses(ref):
    f, c, a, z = parse(ref)
    k = f"{f}-{c}"
    if k not in _cache:
        p = os.path.join(ROOT, "bible", "kr", k + ".json")
        if not os.path.exists(p):
            raise SystemExit(f"정본역 파일 없음: {p} ({ref})")
        _cache[k] = json.load(open(p, encoding="utf-8"))
    ch = _cache[k]
    out = []
    for v in range(a, z + 1):
        if v > len(ch) or not (ch[v - 1] or "").strip():
            raise SystemExit(f"정본역에 없는 절: {ref} ({v}절)")
        out.append((v, ch[v - 1].strip()))
    label = f"{KO[f]} {c}:{a}" + (f"~{z}" if z != a else "")
    return label, out


E = lambda s: html.escape(str(s), quote=False)


def build_html(d):
    h = ['<h3>본문</h3>', '<blockquote>']
    for ref in d.get("verses", []):
        label, vs = verses(ref)
        body = " ".join((f"<sup>{n}</sup>" if len(vs) > 1 else "") + E(t) for n, t in vs)
        h.append(f"<p><strong>{E(label)}</strong>  {body}</p>")
    h.append('</blockquote>')
    for s in d.get("sections", []):
        h.append(f"<h3>{E(s['h'])}</h3>")
        for p in s.get("p", []):
            h.append(f"<p>{E(p)}</p>")
    if d.get("points"):
        h.append('<h3>한눈에 정리</h3><ul>' + "".join(f"<li>{E(x)}</li>" for x in d["points"]) + '</ul>')
    return "".join(h)


def main():
    check = "--check" in sys.argv
    files = sorted(glob.glob(os.path.join(SRC, "*.json")))
    items = []
    for fp in files:
        no = os.path.splitext(os.path.basename(fp))[0]
        d = json.load(open(fp, encoding="utf-8"))
        for k in ("q", "a", "verses", "sections"):
            if not d.get(k):
                raise SystemExit(f"{fp}: '{k}' 비어 있음")
        chips = []
        for r in d["verses"] + d.get("more", []):
            parse(r)
            if r not in chips:
                chips.append(r)
        for r in d.get("more", []):
            verses(r)
        items.append({"id": PREFIX + no, "room": "gen", "cat": d.get("cat") or CAT, "q": d["q"], "a": d["a"],
                      "html": build_html(d), "scriptures": chips, "tags": d.get("tags", [])})
    print(f"난제 {len(items)}편 — 구절 검사 통과")
    if check:
        return
    qna = json.load(open(QNA, encoding="utf-8"))
    rest = [x for x in qna if not str(x.get("id", "")).startswith(PREFIX)]
    out = rest + items
    with open(QNA, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"content/qna.json 저장: 전체 {len(out)}개 (난제 {len(items)})")


if __name__ == "__main__":
    main()
