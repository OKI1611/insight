# -*- coding: utf-8 -*-
"""mk_qa.py — 영문판 번역 품질 게이트

  검사: ① 영문 본문의 모든 (Book c:v) 인용 → 따옴표 안 문장이 KJV 본문에 들어 있는지
        ② 한글 잔존  ③ 용어집 금지 표현  ④ 장별 단어 수(원문 글자 수 대비 0.4~0.7)  ⑤ 필수 섹션 존재
  사용: python tools/mk_qa.py [en/01.md ...]   (인수 없으면 en/ 전체)
"""
import sys, os, re, io, json, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mk_kjv as K

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(ROOT, "책원고", "영문판_천년왕국")
EN2FILE = {v: k for k, v in K.EN_NAME.items()}
EN2FILE["Psalm"] = "Psalms"
BOOK_EN_RE = "|".join(sorted(map(re.escape, EN2FILE.keys()), key=len, reverse=True))
CITE = re.compile(r"\(((?:%s)\s+\d+:\d+(?:[–-]\d+)?(?:;\s*(?:%s)?\s*\d+:\d+(?:[–-]\d+)?)*)\)" % (BOOK_EN_RE, BOOK_EN_RE))
QUOTE = re.compile(r"“([^”]{12,})”")
BANNED = [r"\bMillennial Reign\b", r"\bHeaven\b(?! and)", r"!"]
REQUIRED = ["Key Takeaways", "In One Sentence", "So, Today", "Going Deeper"]
# 원문에 해당 절이 없는 장(검토 완료)
NO_SECTION = {"02.md": ["So, Today"]}

def curly(s):
    """직선 따옴표를 여는/닫는 굽은 따옴표로 정규화(앞이 공백·시작·여는 괄호면 여는 따옴표)"""
    out=[]
    for i,ch in enumerate(s):
        if ch == '"':
            prev = s[i-1] if i else " "
            out.append("“" if prev in " \n\t([{—–-/" else "”")
        else: out.append(ch)
    return "".join(out)

def norm(s):
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"[^a-z0-9' ]+", " ", s.lower()).split()

def kjv_text(cite):
    """'1 Thessalonians 4:16–17' → 이어 붙인 KJV 본문"""
    out = []
    book = None
    for seg in re.split(r";\s*", cite):
        m = re.match(r"(?:(%s)\s+)?(\d+):(\d+)(?:[–-](\d+))?" % BOOK_EN_RE, seg.strip())
        if not m: continue
        if m.group(1): book = EN2FILE[m.group(1)]
        ch, v1 = int(m.group(2)), int(m.group(3)); v2 = int(m.group(4) or v1)
        try: out += [t for _, t in K.verses(book, ch, v1, v2)]
        except Exception as e: return None
    return " ".join(out)

def check(path):
    txt = io.open(path, encoding="utf-8").read()
    body = re.sub(r"<!--.*?-->", "", txt, flags=re.S)
    body = curly(body)
    probs = []
    # ① 인용 대조: 인용문 뒤 120자 안의 참조와 비교
    for qm in QUOTE.finditer(body):
        q = qm.group(1)
        tail = body[qm.end(): qm.end() + 160]
        head = body[max(0, qm.start() - 60): qm.start()]
        cm = CITE.search(tail) or CITE.search(head)
        if not cm:
            continue        # 참조 없는 따옴표(일반 인용)는 통과
        k = kjv_text(cm.group(1))
        if k is None:
            probs.append(("REF?", cm.group(1), q[:60])); continue
        qw, kw = norm(q), norm(k)
        # 인용문의 단어열이 KJV 안에 연속으로 있는지(생략부호로 나뉜 조각은 조각별)
        ok = True
        for piece in re.split(r"\s*(?:\.\.\.|…)\s*", q):
            pw = norm(piece)
            if len(pw) < 3: continue
            s = " ".join(pw)
            if s not in " ".join(kw):
                ok = False; break
        if not ok:
            probs.append(("VERSE", cm.group(1), q[:90]))
    # ② 한글
    for m in re.finditer(r"[가-힣]+", body):
        if os.path.basename(path) == "36_colophon.md": break      # 원제 병기는 허용
        probs.append(("HANGUL", m.group(0), body[max(0, m.start()-30): m.end()+30].replace("\n", " ")))
    # ③ 금지 표현
    for b in BANNED:
        for m in re.finditer(b, body):
            ctx = body[max(0, m.start()-40): m.end()+40].replace("\n", " ")
            if b == "!" and ("<!--" in ctx or "![" in ctx or "](" in ctx): continue
            line_start = body.rfind("\n", 0, m.start()) + 1
            before = body[line_start:m.start()]
            if before.count("*") % 2 == 1: continue                 # 이탤릭 서명(*Heaven*, *… Come!*) 안
            if body[line_start:line_start + 1] == "#": continue      # 제목 행(제목 대문자 표기)
            probs.append(("STYLE", b, ctx))
    # ④ 분량
    words = len(re.findall(r"[A-Za-z’']+", body))
    src = os.path.join(BASE, "src_ko", os.path.basename(path))
    ratio = None
    if os.path.exists(src):
        ko = io.open(src, encoding="utf-8").read()
        kochars = len(re.findall(r"[가-힣]", ko))
        ratio = words / max(1, kochars)
        if not (0.40 <= ratio <= 0.75) and re.match(r"\d\d\.md$", os.path.basename(path)):
            probs.append(("LENGTH", "%d words / %d ko chars = %.2f" % (words, kochars, ratio), ""))
    # ⑤ 필수 섹션(본문 장만)
    if re.match(r"\d\d\.md$", os.path.basename(path)):
        for r in REQUIRED:
            if r not in body and r not in NO_SECTION.get(os.path.basename(path), []): probs.append(("MISSING", r, ""))
    return words, ratio, probs

def main():
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass
    files = sys.argv[1:] or sorted(glob.glob(os.path.join(BASE, "en", "*.md")))
    total = 0
    for p in files:
        w, r, probs = check(p)
        total += len(probs)
        print("%-20s %6d words  ratio %s  issues %d" % (os.path.basename(p), w, ("%.2f" % r) if r else "-", len(probs)))
        for kind, a, b in probs:
            print("   [%s] %s  | %s" % (kind, a, b))
    print("TOTAL issues:", total)
    sys.exit(1 if total else 0)

if __name__ == "__main__":
    main()
