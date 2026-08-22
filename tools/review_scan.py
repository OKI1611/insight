# -*- coding: utf-8 -*-
"""review_scan.py — 정본역 전수 검토 1단계: 전권 자동 스캔 + 검토 에이전트 입력 조립.

신호
  S1 타 역본 유사도  : tools/_review/sources/<ver>.json (로컬 전용·저작권) 과 비교.
                        정규화(문장부호 제거·조사 제거·신명/용어 마스킹) 후
                        exact / charsim(편집유사도) / run(최장 공통 어절 연속) / cov3(어절 3-gram 커버리지)
                        등급 A(동일·charsim≥0.9,15자+) B(run≥6 또는 cov3≥0.6) C(cov3 0.4~0.6)
                        기준선 = 참고 역본끼리의 유사도(독립 계열 nkrv↔hkjv·kkjv) → excess 기록
                        흠정역·한킹·표준KJV(같은 KJV 직역)는 A만 문제 삼는다(B·C는 기록만).
  S2 KJV 핵심어 불일치: tools/review_kjv_glossary.json + tools/_audit/lex/<Book>.json(STEPBible 렉심)
                        KJV 토큰에 사전어 있음 + 한국어 절에 허용 어간 없음 → mismatch
                        해당 절 원어가 KJV 단어와 어긋나는 렉심(agrees=false) → kjv_ne_orig (사장님 결정 후보)
  S3 문법·용어 린트   : 조사(이/가·을/를·과/와·로/으로 — 확실한 경우만), 중복 공백, 공백+구두점,
                        인용부호 짝, forbid_ko(세례·천국·하나님 나라 …)
  S4 운율 지표        : 절 길이 z-score(권별), 같은 연결어미 3회 이상 반복
산출
  tools/_review/candidates.jsonl   (신호가 하나라도 있는 절)
  tools/_review/scan_summary.md    (권별 집계)
  --emit-input --book Romans       → tools/_review/inputs/Romans-<ch>[-p].json  (검토 에이전트 입력)
사용
  python tools/review_scan.py                    # 전권
  python tools/review_scan.py --book Romans      # 한 권
  python tools/review_scan.py --book Romans --emit-input
"""
import json, os, re, sys, io, argparse, difflib, statistics, math
from collections import defaultdict, Counter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIBLE = os.path.join(ROOT, 'bible')
REV = os.path.join(ROOT, 'tools', '_review')
SRCD = os.path.join(REV, 'sources')
LEXD = os.path.join(ROOT, 'tools', '_audit', 'lex')
INP = os.path.join(REV, 'inputs')
os.makedirs(REV, exist_ok=True); os.makedirs(INP, exist_ok=True)

BOOKS = json.load(open(os.path.join(BIBLE, 'books.json'), encoding='utf-8'))
GLOSS = json.load(open(os.path.join(ROOT, 'tools', 'review_kjv_glossary.json'), encoding='utf-8'))['entries']
for g in GLOSS:
    g['_re'] = re.compile(g['kjvre'])
    g['_ko'] = [re.compile(p) for p in g.get('ko', [])]
    g['_forbid'] = [re.compile(p) for p in g.get('forbid_ko', [])]
    for s, v in g.get('lex', {}).items():
        v['_ko'] = [re.compile(p) for p in v.get('ko', [])]
LOCKED = json.load(open(os.path.join(ROOT, 'tools', 'review_locked.json'), encoding='utf-8')) if os.path.exists(os.path.join(ROOT, 'tools', 'review_locked.json')) else {}
BATTERY = json.load(open(os.path.join(ROOT, 'tools', 'tr_battery.json'), encoding='utf-8'))
MUST = {it['ref']: it.get('must', '') for it in BATTERY.get('tr_phrases', [])}
FORBIDDEN = [f for f in BATTERY.get('forbidden', []) if isinstance(f, str)]

VERS_KR = ['nkrv', 'krv']            # 개역 계열 (B 이상 문제)
VERS_KJ = ['hkjv', 'kkjv', 'skjv']   # KJV 한국어 직역 계열 (A 만 문제)
VNAME = {'nkrv': '개역개정', 'krv': '개역한글', 'hkjv': '흠정역', 'kkjv': '한글킹제임스', 'skjv': '표준킹제임스'}
SOURCES = {}
for v in VERS_KR + VERS_KJ:
    p = os.path.join(SRCD, v + '.json')
    if os.path.exists(p):
        SOURCES[v] = json.load(open(p, encoding='utf-8'))

# ───────────── S1 정규화 ─────────────
MASK_TERMS = ['여호와', '하나님', '주님', '예수 그리스도', '그리스도 예수', '예수', '그리스도', '성령', '주', '이스라엘', '예루살렘', '유대', '이방',
              '칭의', '성화', '침례', '구속', '중생', '회개', '언약', '율법', '복음', '교회', '은혜', '믿음', '사랑', '영광', '구원', '천사', '선지자',
              '왕국', '음부', '지옥', '무덤', '사탄', '마귀', '아멘', '할렐루야']
MASK_RE = re.compile('|'.join(sorted(map(re.escape, MASK_TERMS), key=len, reverse=True)))
JOSA_RE = re.compile(r'(께서|에게서|으로써|으로서|이라고|라고|에서|에게|까지|부터|처럼|으로|에는|에도|이나|이며|이요|이라|이니|로서|로써|께|은|는|이|가|을|를|과|와|의|에|로|도|만|나|며|요|라|니)$')
PUNCT_RE = re.compile(r'[\"\'“”‘’「」『』()\[\]{}<>《》〈〉.,;:!?·…—\-–~/\\]')

def norm_tokens(s):
    s = PUNCT_RE.sub(' ', s or '')
    s = MASK_RE.sub(' @ ', s)
    toks = []
    for t in s.split():
        if t == '@': toks.append('@'); continue
        t = re.sub(r'[0-9]+', '#', t)
        t2 = JOSA_RE.sub('', t)
        toks.append(t2 if len(t2) >= 1 else t)
    return toks

def charsim(a, b):
    a = ''.join(a); b = ''.join(b)
    if not a or not b: return 0.0
    return difflib.SequenceMatcher(None, a, b).ratio()

def longest_run(a, b):
    best = 0; prev = [0] * (len(b) + 1)
    for i in range(1, len(a) + 1):
        cur = [0] * (len(b) + 1)
        for j in range(1, len(b) + 1):
            if a[i-1] == b[j-1] and a[i-1] != '@':
                cur[j] = prev[j-1] + 1
                if cur[j] > best: best = cur[j]
        prev = cur
    return best

def cov3(a, b):
    n = 3 if len(a) >= 3 else 2
    if len(a) < n or len(b) < n: return 0.0
    ga = {tuple(a[i:i+n]) for i in range(len(a)-n+1)}
    gb = {tuple(b[i:i+n]) for i in range(len(b)-n+1)}
    ga = {g for g in ga if '@' not in g} or ga
    if not ga: return 0.0
    return len(ga & gb) / len(ga)

def s1_compare(our, ref):
    ta, tb = norm_tokens(our), norm_tokens(ref)
    exact = ''.join(ta) == ''.join(tb) and len(''.join(ta)) >= 6
    return {'exact': exact, 'charsim': round(charsim(ta, tb), 3), 'run': longest_run(ta, tb), 'cov3': round(cov3(ta, tb), 3), 'ntok': len(ta)}

def s1_grade(m, our_len, kind):
    if m['exact'] or (m['charsim'] >= 0.9 and our_len >= 15): return 'A'
    if kind == 'kj': return ''                 # KJV 직역 계열은 A 만
    if m['run'] >= 6 or m['cov3'] >= 0.6: return 'B'
    if m['cov3'] >= 0.4: return 'C'
    return ''

# ───────────── S2 ─────────────
def s2_check(kjv, kr, lexs):
    out = []
    kl = (kjv or '').lower()
    strongs = {w['s'] for w in lexs if w.get('tr', True)}
    for g in GLOSS:
        if not g['_re'].search(kl): continue
        if g.get('only_if_lex') and not (set(g['only_if_lex']) & strongs): continue
        present = [s for s in g.get('lex', {}) if s in strongs]
        if present:
            pats = [p for s in present for p in g['lex'][s]['_ko']]
            ne = [s for s in present if g['lex'][s].get('agrees') is False]
        else:
            pats = g['_ko']; ne = []
        ok = any(p.search(kr) for p in pats) if pats else True
        forb = [p.pattern for p in g['_forbid'] if p.search(kr)]
        if ok and not forb and not ne: continue
        item = {'word': g['id'], 'strongs': present, 'ok': ok}
        if not ok: item['expected'] = sorted({p.pattern for p in pats})[:6]
        if forb: item['forbidden_ko'] = forb
        if ne:
            item['kjv_ne_orig'] = [{'strong': s, 'sense': g['lex'][s].get('sense', '')} for s in ne]
        out.append(item)
    return out

# ───────────── S3 ─────────────
def has_batchim(ch):
    c = ord(ch)
    if 0xAC00 <= c <= 0xD7A3: return (c - 0xAC00) % 28 != 0
    return None
def batchim_is_rieul(ch):
    c = ord(ch)
    return 0xAC00 <= c <= 0xD7A3 and (c - 0xAC00) % 28 == 8

def s3_check(kr):
    issues = []
    s = kr or ''
    if '  ' in s: issues.append('중복 공백')
    if re.search(r'\s[,.!?;:]', s): issues.append('구두점 앞 공백')
    if re.search(r'[,;:][^\s\d"”’)\]]', s) and not re.search(r'\d[,]\d', s): issues.append('쉼표 뒤 공백 없음')
    # 인용부호 짝은 절 경계를 넘어 이어지는 경우가 많아(2,443절) 오류가 아님 — 린트에서 제외(에이전트 입력에만 참고로 둠)
    # 조사 — 확실한 경우만
    for m in re.finditer(r'([가-힣])(가|를|와)(?=[\s,.!?;:”’」)]|$)', s):
        prev = m.group(1); j = m.group(2)
        if has_batchim(prev):
            # 받침 + 가/를/와 : 예외 — 접미어 '-가(家·歌·價…)' 명사 ('국가' '왕가' '평가' '추가'), 동사 어간 '…르'
            if j == '가' and prev in '국왕평추증참작대화일인상효여':
                continue
            issues.append(f'조사 의심: …{prev}{j}')
    for m in re.finditer(r'([가-힣])(과)(?=[\s,.!?;:”’」)]|$)', s):
        prev = m.group(1)
        if has_batchim(prev) is False and prev not in '사결효성':   # 결과·효과·성과·사과 제외
            issues.append(f'조사 의심: …{prev}과')
    for m in re.finditer(r'([가-힣])(으로)(?=[\s,.!?;:”’」)]|$)', s):
        prev = m.group(1)
        if has_batchim(prev) is False or batchim_is_rieul(prev):
            issues.append(f'조사 의심: …{prev}으로')
    for m in re.finditer(r'([가-힣])(로)(?=[\s,.!?;:”’」)]|$)', s):
        prev = m.group(1)
        if has_batchim(prev) and not batchim_is_rieul(prev) and prev not in '으':
            issues.append(f'조사 의심: …{prev}로')
    for f in FORBIDDEN:
        if f and f in s: issues.append(f'금지어: {f}')
    # 조사 의심은 고유명사(알가·알와)·부사(삼가)·합성어(강가·길가)가 대부분이라 '확인 필요' 표기
    return [i if not i.startswith('조사 의심') else i.replace('조사 의심', '조사 확인 필요') for i in issues]

# ───────────── S4 ─────────────
END_RE = re.compile(r'(하고|하며|하니|하여|하사|하매|이요|거늘|으되|하시고|하시며|하시니)(?=[\s,])')
def s4_check(kr, zlen):
    out = {}
    c = Counter(END_RE.findall(kr or ''))
    rep = [f'{k}×{v}' for k, v in c.items() if v >= 3]
    if rep: out['repeat'] = rep
    if abs(zlen) >= 2.5: out['len_z'] = round(zlen, 1)
    return out

# ───────────── 메인 스캔 ─────────────
def load_kr(bf, ch):
    return json.load(open(os.path.join(BIBLE, 'kr', f'{bf}-{ch}.json'), encoding='utf-8'))
def load_kjv(bf):
    return json.load(open(os.path.join(BIBLE, 'kjv', f'{bf}.json'), encoding='utf-8'))
def load_lex(bf):
    p = os.path.join(LEXD, f'{bf}.json')
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else {}

def scan_book(b, stats):
    bf = b['file']; kjv = load_kjv(bf); lex = load_lex(bf)
    # 권별 절 길이 분포
    lens = []
    krs = {}
    for ch in range(1, b['ch'] + 1):
        try: krs[ch] = load_kr(bf, ch)
        except Exception: krs[ch] = []
        lens += [len(v or '') for v in krs[ch]]
    mu = statistics.mean(lens) if lens else 0; sd = statistics.pstdev(lens) if len(lens) > 1 else 1
    rows = []
    for ch in range(1, b['ch'] + 1):
        kr = krs[ch]; kv = kjv.get(str(ch), [])
        for i, text in enumerate(kr):
            v = i + 1; ref = f'{bf}-{ch}-{v}'
            kjv_v = kv[i] if i < len(kv) else ''
            lexs = lex.get(f'{ch}:{v}', [])
            row = {'ref': ref, 'book': bf, 'ch': ch, 'v': v, 'len': len(text or '')}
            # S1
            best = None; s1 = {}
            for ver, src in SOURCES.items():
                rt = src.get(ref)
                if not rt: continue
                m = s1_compare(text, rt)
                kind = 'kr' if ver in VERS_KR else 'kj'
                m['grade'] = s1_grade(m, len(text or ''), kind); m['ver'] = ver
                s1[ver] = m
                if m['grade'] and (best is None or (m['grade'], m['charsim']) < (best['grade'], best['charsim']) or (m['grade'] == best['grade'] and m['charsim'] > best['charsim'])):
                    best = m
            # 기준선: 독립 계열끼리 (개역개정 ↔ 흠정역/한킹)
            base = []
            if 'nkrv' in SOURCES and SOURCES['nkrv'].get(ref):
                for o in ('hkjv', 'kkjv'):
                    if o in SOURCES and SOURCES[o].get(ref):
                        base.append(s1_compare(SOURCES['nkrv'][ref], SOURCES[o][ref])['cov3'])
            baseline = round(statistics.mean(base), 3) if base else None
            if best:
                best = dict(best); best['baseline'] = baseline
                if baseline is not None: best['excess'] = round(best['cov3'] - baseline, 3)
                row['s1'] = best
                row['s1_all'] = {k: {'g': m['grade'], 'cs': m['charsim'], 'run': m['run'], 'cov3': m['cov3']} for k, m in s1.items() if m['grade'] or m['cov3'] >= 0.4}
            # S2
            s2 = s2_check(kjv_v, text or '', lexs)
            if s2: row['s2'] = s2
            # S3
            s3 = s3_check(text or '')
            if s3: row['s3'] = s3
            # S4
            z = (len(text or '') - mu) / sd if sd else 0
            s4 = s4_check(text or '', z)
            if s4: row['s4'] = s4
            if ref in LOCKED: row['locked'] = LOCKED[ref]
            if ref in MUST: row['must'] = MUST[ref]
            if any(k in row for k in ('s1', 's2', 's3', 's4')):
                rows.append(row)
            # 통계
            st = stats[bf]
            st['verses'] += 1
            if best: st['s1_' + best['grade']] += 1; st['s1_ver_' + best['ver']] += 1
            for it in s2:
                if not it['ok']: st['s2_mismatch'] += 1; st['s2_word_' + it['word']] += 1
                if it.get('kjv_ne_orig'): st['s2_kjv_ne_orig'] += 1
                if it.get('forbidden_ko'): st['s2_forbid'] += 1
            for it in s3:
                st['s3_' + it.split(':')[0].split(' ')[0]] += 1
            if s4: st['s4'] += 1
    return rows

def write_summary(stats, path):
    L = ['# 정본역 전수 검토 — 자동 스캔 요약', '',
         f"참고 역본: {', '.join(VNAME[v] + f'({len(SOURCES[v]):,}절)' for v in SOURCES)}", '',
         '| 권 | 절 | S1 A | S1 B | S1 C | S2 불일치 | KJV≠원어 | 금지역어 | S3 | S4 |', '|---|---|---|---|---|---|---|---|---|---|']
    tot = Counter()
    for b in BOOKS:
        st = stats.get(b['file'])
        if not st: continue
        s3 = sum(v for k, v in st.items() if k.startswith('s3_'))
        L.append(f"| {b['ko']} | {st['verses']} | {st['s1_A']} | {st['s1_B']} | {st['s1_C']} | {st['s2_mismatch']} | {st['s2_kjv_ne_orig']} | {st['s2_forbid']} | {s3} | {st['s4']} |")
        for k, v in st.items(): tot[k] += v
    s3t = sum(v for k, v in tot.items() if k.startswith('s3_'))
    L.append(f"| **합계** | {tot['verses']} | {tot['s1_A']} | {tot['s1_B']} | {tot['s1_C']} | {tot['s2_mismatch']} | {tot['s2_kjv_ne_orig']} | {tot['s2_forbid']} | {s3t} | {tot['s4']} |")
    L += ['', '## S1 최고 등급이 나온 역본', '']
    for v in SOURCES: L.append(f"- {VNAME[v]}: {tot['s1_ver_' + v]}")
    L += ['', '## S2 불일치 상위 단어', '']
    for k, v in sorted(((k[8:], v) for k, v in tot.items() if k.startswith('s2_word_')), key=lambda x: -x[1])[:25]:
        L.append(f'- {k}: {v}')
    L += ['', '## S3 유형', '']
    for k, v in sorted(((k[3:], v) for k, v in tot.items() if k.startswith('s3_')), key=lambda x: -x[1]):
        L.append(f'- {k}: {v}')
    open(path, 'w', encoding='utf-8').write('\n'.join(L) + '\n')

# ───────────── 에이전트 입력 조립 ─────────────
def guideline_excerpt():
    t = open(os.path.join(BIBLE, '번역지침.md'), encoding='utf-8').read()
    parts = []
    for h in ('## 1. 번역 철학', '## 3. 문체·어조', '## 5. 핵심 용어집'):
        i = t.find(h)
        if i < 0: continue
        j = t.find('\n## ', i + 5)
        parts.append(t[i:j if j > 0 else None].strip())
    return '\n\n'.join(parts)

def emit_inputs(b, rows):
    bf = b['file']; kjv = load_kjv(bf); lex = load_lex(bf)
    byref = {r['ref']: r for r in rows}
    guide = guideline_excerpt()
    gloss_short = [{'id': g['id'], 'kjv': g['kjvre'], 'ko': g.get('ko', []), 'forbid_ko': g.get('forbid_ko', []),
                    'lex': {s: {'ko': v.get('ko', []), 'agrees': v.get('agrees', True), 'sense': v.get('sense', '')} for s, v in g.get('lex', {}).items()}} for g in GLOSS]
    n_files = 0
    for ch in range(1, b['ch'] + 1):
        kr = load_kr(bf, ch); kv = kjv.get(str(ch), [])
        n = len(kr); CH = 40
        parts = [(s, min(n, s + CH)) for s in range(0, n, CH)]
        for pi, (s0, s1) in enumerate(parts):
            verses = []
            for i in range(max(0, s0 - 2), s1):
                v = i + 1; ref = f'{bf}-{ch}-{v}'
                r = byref.get(ref, {})
                item = {'v': v, 'context_only': i < s0, 'kjv': kv[i] if i < len(kv) else '', 'kr': kr[i]}
                if i < s0: verses.append(item); continue
                lx = [{'s': w['s'], 'l': w['l'], 'g': w['g'], 'e': w['e'], 'm': w['m']} for w in lex.get(f'{ch}:{v}', []) if w.get('tr', True) and w['s'] not in ('G3588', 'G2532', 'G1161', 'G1063', 'H9001', 'H9002', 'H9003', 'H9005', 'H9009', 'H9016', 'H0853')]
                item['lex'] = lx
                flags = {}
                if 's1' in r:
                    b1 = r['s1']
                    flags['s1'] = {'grade': b1['grade'], 'ver': VNAME[b1['ver']], 'charsim': b1['charsim'], 'run': b1['run'], 'cov3': b1['cov3'], 'excess': b1.get('excess')}
                    # 타 역본 본문: B 이상일 때만, 최고 등급 역본 하나만 (저작권·어투 오염 최소화 — 출력·노트에 인용 금지)
                    if b1['grade'] in ('A', 'B'):
                        flags['s1']['ref_text_DO_NOT_QUOTE'] = SOURCES[b1['ver']].get(ref, '')
                if 's2' in r: flags['s2'] = r['s2']
                if 's3' in r: flags['s3'] = r['s3']
                if 's4' in r: flags['s4'] = r['s4']
                item['flags'] = flags
                if ref in LOCKED: item['locked'] = LOCKED[ref]
                if ref in MUST: item['battery_must'] = MUST[ref]
                verses.append(item)
            doc = {'book': bf, 'book_ko': b['ko'], 'chapter': ch, 'part': pi + 1, 'parts': len(parts),
                   'verse_range': [s0 + 1, s1],
                   'guideline_excerpt': guide, 'kjv_glossary': gloss_short,
                   'forbidden_words': FORBIDDEN,
                   'verses': verses}
            name = f'{bf}-{ch}' + (f'-p{pi+1}' if len(parts) > 1 else '') + '.json'
            json.dump(doc, open(os.path.join(INP, name), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
            n_files += 1
    return n_files

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--book')
    ap.add_argument('--emit-input', action='store_true')
    a = ap.parse_args()
    books = [b for b in BOOKS if not a.book or b['file'] == a.book]
    stats = defaultdict(Counter)
    all_rows = []
    for b in books:
        rows = scan_book(b, stats)
        all_rows += rows
        if a.emit_input:
            nf = emit_inputs(b, rows)
            print(f"  입력 파일 {nf}개 → tools/_review/inputs/ ({b['ko']})")
    out = os.path.join(REV, 'candidates.jsonl' if not a.book else f'candidates-{a.book}.jsonl')
    with open(out, 'w', encoding='utf-8') as f:
        for r in all_rows: f.write(json.dumps(r, ensure_ascii=False) + '\n')
    summ = os.path.join(REV, 'scan_summary.md' if not a.book else f'scan_summary-{a.book}.md')
    write_summary(stats, summ)
    print(f'스캔 완료: {len(books)}권 · 후보 {len(all_rows):,}절 → {out}')
    print(f'요약 → {summ}')

if __name__ == '__main__':
    main()
