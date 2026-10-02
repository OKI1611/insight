# -*- coding: utf-8 -*-
"""retrans_batch.py — 유사도 재번역 작업대 (2026-10 전수조사 후속)

emit  : 재번역 대상 절을 KJV 영어와 함께 작업 파일로 낸다(타 역본 본문은 싣지 않는다).
check : 새 번역(JSON {ref: text})을 타 역본과 다시 대조하고 어법·금지어·문체를 검사한다.
        통과분은 review_apply.py 가 읽는 approved 형식으로 저장한다.

사용
  python tools/retrans_batch.py emit --refs refs.txt --out batch.txt
  python tools/retrans_batch.py emit --chapter John-6 --out batch.txt
  python tools/retrans_batch.py check --new new.json --approved approved.json
  python tools/review_apply.py --approved approved.json
"""
import json, os, re, sys, argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import review_scan as R
import usage_audit as U

BIBLE = R.BIBLE
_kjv = {}
def kjv(bf, ch, v):
    if bf not in _kjv: _kjv[bf] = json.load(open(os.path.join(BIBLE, 'kjv', bf + '.json'), encoding='utf-8'))
    a = _kjv[bf].get(str(ch), [])
    return a[v - 1] if v - 1 < len(a) else ''
_kr = {}
def kr(bf, ch):
    k = (bf, ch)
    if k not in _kr: _kr[k] = json.load(open(os.path.join(BIBLE, 'kr', f'{bf}-{ch}.json'), encoding='utf-8'))
    return _kr[k]
def split(ref):
    bf, ch, v = ref.rsplit('-', 2)
    return bf, int(ch), int(v)

FORBIDDEN = R.FORBIDDEN
END_OK = re.compile(r'(라|다|요|냐|뇨|까|서|자|라\)|로다|도다|지어다|소서|이까|리요|하고|하며|하니|하매|하되|거늘|이요|[가-힣])[.!?,;:"\'’”)]*$')

def grades(text, ref):
    out = {}
    for ver, src in R.SOURCES.items():
        rt = src.get(ref)
        if not rt: continue
        m = R.s1_compare(text, rt)
        g = U.grade(m, len(text))
        if g: out[ver] = (g, m['charsim'], m['run'], m['cov3'])
    return out

def cmd_emit(a):
    refs = []
    if a.chapter:
        bf, ch = a.chapter.rsplit('-', 1)
        refs = [f'{bf}-{ch}-{i+1}' for i in range(len(kr(bf, int(ch))))]
    else:
        refs = [l.strip() for l in open(a.refs, encoding='utf-8') if l.strip()]
    L = []; skipped = []; done = 0
    COMMON = {'LORD', 'Lord', 'God', 'GOD', 'I', 'O', 'Israel', 'Jesus', 'Christ', 'Holy', 'Ghost', 'Spirit', 'Father', 'Son', 'Jews', 'Amen'}
    for ref in refs:
        bf, ch, v = split(ref)
        cur = kr(bf, ch)[v - 1]
        en = kjv(bf, ch, v)
        if not a.chapter:
            g = grades(cur, ref)
            if not any(x[0] == 'A' for x in g.values()):      # 이미 고쳐졌거나 A 가 아닌 절은 건너뜀
                done += 1; continue
            ws = re.findall(r"[A-Za-z']+", en)
            caps = [w for w in ws[1:] if w[0].isupper() and w not in COMMON]
            if ws and len(caps) / len(ws) >= 0.28:           # 이름 나열 — 표현 선택의 여지 없음
                skipped.append(ref); continue
        L.append(f'## {ref}\nEN: {en}\nKO: {cur}')
    open(a.out, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    if skipped:
        with open(os.path.join(os.path.dirname(a.out), 'unavoidable_names.refs'), 'a', encoding='utf-8') as f:
            f.write('\n'.join(skipped) + '\n')
    print(f'{len(L)}절 → {a.out} (이름 나열 제외 {len(skipped)} · 이미 해결 {done})')

def cmd_check(a):
    new = json.load(open(a.new, encoding='utf-8'))
    ok, bad = [], []
    for ref, text in new.items():
        bf, ch, v = split(ref)
        old = kr(bf, ch)[v - 1]
        text = text.strip()
        prob = []
        g = grades(text, ref)
        un = U.unavoidable(text, R.norm_tokens(text))
        worst = [f'{k}:{x[0]}({x[1]})' for k, x in g.items() if x[0] == 'A']
        if worst and not un: prob.append('유사 A ' + ' '.join(worst))
        if a.strict:
            wb = [f'{k}:B(run{x[2]},cov{x[3]})' for k, x in g.items() if x[0] == 'B' and k in ('hkjv', 'kkjv', 'skjv')]
            if wb and not un: prob.append('유사 B ' + ' '.join(wb))
        for f in FORBIDDEN:
            if f and f in text: prob.append('금지어 ' + f)
        for it in U.u_check(text):
            if it['g'] in ('A',) : prob.append('어법 ' + it['rule'])
            if it['rule'] in ('옛대명사_저희', '옛대명사_저', '그녀'): prob.append('어법 ' + it['rule'])
        if text.count('"') % 2 != old.count('"') % 2: prob.append(f'큰따옴표 수 홀짝 변동({old.count(chr(34))}→{text.count(chr(34))})')
        if text.count("'") % 2 != old.count("'") % 2: prob.append('작은따옴표 홀짝 변동')
        if '  ' in text: prob.append('중복 공백')
        if re.search(r'[A-Za-z]', text): prob.append('영문')
        if text == old: prob.append('변경 없음')
        (bad if prob else ok).append((ref, old, text, prob, g))
    for ref, old, text, prob, g in bad:
        print(f'✗ {ref}: {"; ".join(prob)}\n    {text}')
    print(f'통과 {len(ok)} · 실패 {len(bad)}')
    if a.approved:
        json.dump([{'ref': r, 'old': o, 'new': t} for r, o, t, _, _ in ok], open(a.approved, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print(f'승인 파일 → {a.approved}')

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest='cmd')
    e = sp.add_parser('emit'); e.add_argument('--refs'); e.add_argument('--chapter'); e.add_argument('--out', required=True)
    c = sp.add_parser('check'); c.add_argument('--new', required=True); c.add_argument('--approved'); c.add_argument('--strict', action='store_true')
    a = ap.parse_args()
    {'emit': cmd_emit, 'check': cmd_check}[a.cmd](a)
