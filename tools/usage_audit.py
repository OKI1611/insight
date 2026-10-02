# -*- coding: utf-8 -*-
"""usage_audit.py — 정본역 전권 어법·유사도 전수조사 (2026-10 사용자 지시)

review_scan.py 의 S1(타 역본 유사도) 계산을 그대로 쓰되,
  · 흠정역(hkjv)도 A·B 를 모두 문제 삼고(시비 차단), 한글킹제임스·표준킹제임스·개역한글은 A 와 '강한 B' 를 본다
  · 표현 선택의 여지가 없는 절(짧은 절·이름 나열)은 '불가피 일치' 로 따로 센다
어법 린트(U): 「그녀」·옛 어투·현대체 어미·이중 피동·맞춤법 혼동 쌍·겹조사·공백 등 규칙 기반.

⚠ 타 역본 본문은 tools/_review/sources/ (gitignore) 에서만 읽고, 산출물에는 싣지 않는다(수치만).
산출: tools/_review/usage_audit.jsonl  (절 단위)   tools/_review/usage_audit_summary.json
사용: python tools/usage_audit.py [--book Genesis]
"""
import json, os, re, sys, argparse
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import review_scan as R          # s1_compare / norm_tokens / SOURCES / BOOKS

ROOT = R.ROOT; BIBLE = R.BIBLE; REV = R.REV
NAMES = set(json.load(open(os.path.join(BIBLE, 'kjv-korean.json'), encoding='utf-8')).values())

# ───────── S1 등급 (역본 구분 없이 같은 자) ─────────
def grade(m, our_len):
    if m['exact'] or (m['charsim'] >= 0.9 and our_len >= 15): return 'A'
    if m['run'] >= 6 or m['cov3'] >= 0.6: return 'B'
    if m['cov3'] >= 0.4: return 'C'
    return ''

def unavoidable(text, toks):
    """표현 선택의 여지가 거의 없는 절 — 짧은 절, 이름·수 나열"""
    core = [t for t in toks if t != '@']
    if len(''.join(core)) < 12 or len(core) <= 4: return '짧은 절'
    words = re.findall(r'[가-힣]+', text)
    if words:
        nm = sum(1 for w in words if R.JOSA_RE.sub('', w) in NAMES or w in NAMES)
        if nm / len(words) >= 0.5: return '이름 나열'
    if len(re.findall(r'[0-9]|[일이삼사오육칠팔구십백천만]{2,}', text)) >= 4 and len(core) <= 12: return '수 나열'
    return ''

# ───────── U 어법 린트 ─────────
U_RULES = [
    # (id, 등급, 정규식, 설명)
    ('그녀',        'A', r'그녀', "「그녀」 — 미사용 원칙(그 여자/그/이름으로)"),
    ('가라사대',    'A', r'가라사대', "옛 어투 「가라사대」 → 이르시되"),
    ('현대체어미',  'A', r"(습니다|합니다|입니다)(?=[\s.,!?\"']|$)|(했다|하였다|이었다|었다|았다)(?=[.!?]|$)|(?<![나니소리사까오더지])이다(?=[.!?]|$)", "현대 평서체 어미(권위체 위반)"),
    ('평서_간접인용', 'C', r"(했다|하였다|었다|았다)[\"']?\s(하|함)", "평서형 간접 인용(~었다 하니) — 정상 용법, 참고"),
    ('평서_한다',    'C', r'[가-힣](한다|는다|ㄴ다)(?=[.!?]|$)', "문장 끝 「~한다」(간접 인용이 아니면 권위체 위반)"),
    ('이중피동',    'A', r'(되어지|보여지|쓰여지|불리워|잊혀지|지어지게 되|여겨지게 되)', "이중 피동"),
    ('되어진',      'A', r'[가-힣]+되어진', "이중 피동 「~되어진」"),
    ('옛대명사_저희', 'B', r'(?<![가-힣])저희(?=[가를는은의에도와과만]|[\s,]|에게|로|더러|끼리)', "「저희」 — 3인칭 복수 옛 용법이면 「그들」"),
    ('옛대명사_저',   'C', r'(?<![가-힣])저가(?=\s)', "「저가」 — 3인칭 옛 용법이면 「그가」"),
    ('옛말_가로되',  'A', r'가로되|갈아사대|가론', "옛 어투 「가로되」 → 이르되"),
    ('옛말_하니이다', 'C', r'하였삽|하옵나|하옵소|하시옵', "지나친 옛 겸양 선어말(삽/옵)"),
    ('옛말_일러',    'C', r'일러 가로|이르사대', "옛 어투"),
    ('던지든지',    'B', r'[가-힣]+던지\s[가-힣]+던지|하던지\s(말|아니)', "선택의 「-든지」를 「-던지」로 적음"),
    ('몇일',        'A', r'몇\s?일(?![가-힣]*[0-9])|몇일', "「며칠」"),
    ('금새',        'A', r'금새', "「금세」"),
    ('바램',        'A', r'바램', "「바람」(바라다)"),
    ('설레임',      'A', r'설레임|헤매임', "명사형 오류"),
    ('오랫만',      'A', r'오랫만|오랜동안', "「오랜만/오랫동안」"),
    ('웬왠',        'A', r'왠\s?(일|말|떡|걸)|웬지', "「웬/왠」 혼동"),
    ('알맞는',      'A', r'알맞는|걸맞는', "「알맞은/걸맞은」"),
    ('삼가하',      'A', r'삼가하|삼가해', "「삼가다」(삼가하다 ×)"),
    ('잠그다',      'A', r'잠궈|잠궜|담궈|담궜', "「잠가/담가」"),
    ('치루다',      'A', r'치루(었|어|고|니|며)|치뤄|치뤘', "「치르다」"),
    ('들르다',      'A', r'들렸다\s?가(?!\S)|들려서\s(가|오)', "「들르다」 활용 확인"),
    ('뵈요',        'A', r'뵈요|봬어', "「봬요/뵈어」"),
    ('중복공백',    'B', r'\s{2,}', "중복 공백"),
    ('구두점앞공백', 'B', r'\s[,.!?;:](?!\.)', "구두점 앞 공백"),
    ('쉼표뒤붙음',  'B', r',(?=[가-힣])', "쉼표 뒤 공백 없음"),
    ('마침표중복',  'B', r'[.]{2}(?![.])|,,|[.],|,[.]', "문장부호 중복"),
    ('전각기호',    'B', r'[“”‘’「」『』]', "따옴표 종류 혼용(곧은따옴표로 통일)"),
    ('영문잔존',    'A', r'[A-Za-z]{3,}', "한글 본문에 영문 잔존"),
    ('한자잔존',    'B', r'[一-鿿]', "한글 본문에 한자 잔존"),
    ('당신_하나님께', 'C', r'(주여|하나님이여|여호와여|아버지여)[^.]{0,40}당신', "하나님께 「당신」 — 높임 확인"),
    ('것이었',      'C', r'것이었(다|더라|으니)', "번역투 「~것이었다」"),
    ('그그',        'B', r'(?<![가-힣])그\s그\s', "「그 그」 중복"),
    ('수있',        'B', r'[가-힣](할수|될수|갈수|볼수|올수|줄수)\s?(있|없)', "「~ㄹ 수」 띄어쓰기"),
    ('뿐만아니라',  'C', r'뿐만아니라|뿐아니라', "「뿐만 아니라」 띄어쓰기"),
    ('못하다띄',    'C', r'[가-힣]지못(하|한|할)', "「~지 못하」 띄어쓰기"),
    ('아니하띄',    'C', r'[가-힣]지아니(하|한|할)', "「~지 아니하」 띄어쓰기"),
]
U_RE = [(i, g, re.compile(p), d) for i, g, p, d in U_RULES]

def u_check(text):
    out = []
    for i, g, rx, d in U_RE:
        ms = rx.findall(text)
        if ms:
            m = rx.search(text)
            out.append({'rule': i, 'g': g, 'hit': text[max(0, m.start()-8): m.end()+8], 'n': len(ms), 'desc': d})
    # 인용부호 홀수(절 경계를 넘는 인용은 정상이라 참고만)
    return out

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--book'); a = ap.parse_args()
    vers = [v for v in ('hkjv', 'kkjv', 'skjv', 'krv', 'nkrv') if v in R.SOURCES and len(R.SOURCES[v]) > 1000]
    rows = []; summ = defaultdict(Counter); nverse = 0; cover = Counter()
    for b in R.BOOKS:
        bf = b['file']
        if a.book and bf != a.book: continue
        for ch in range(1, b['ch'] + 1):
            kr = json.load(open(os.path.join(BIBLE, 'kr', f'{bf}-{ch}.json'), encoding='utf-8'))
            for i, text in enumerate(kr):
                nverse += 1; text = text or ''
                ref = f'{bf}-{ch}-{i+1}'
                row = {'ref': ref, 'book': bf, 'ko': b['ko'], 'ch': ch, 'v': i + 1}
                toks = R.norm_tokens(text)
                s1 = {}
                for ver in vers:
                    rt = R.SOURCES[ver].get(ref)
                    if not rt: continue
                    cover[ver] += 1
                    m = R.s1_compare(text, rt)
                    g = grade(m, len(text))
                    if g:
                        s1[ver] = {'g': g, 'cs': m['charsim'], 'run': m['run'], 'cov3': m['cov3'], 'exact': m['exact']}
                if s1:
                    un = unavoidable(text, toks)
                    row['s1'] = s1
                    if un: row['unavoidable'] = un
                    for ver, m in s1.items():
                        summ[bf][f'{ver}_{m["g"]}' + ('_un' if un else '')] += 1
                u = u_check(text)
                if u:
                    row['u'] = u
                    for it in u: summ[bf]['u_' + it['rule']] += it['n'] if it['rule'] in ('그녀',) else 1
                if 's1' in row or 'u' in row:
                    row['text'] = text
                    rows.append(row)
    suf = f'-{a.book}' if a.book else ''
    with open(os.path.join(REV, f'usage_audit{suf}.jsonl'), 'w', encoding='utf-8') as f:
        for r in rows: f.write(json.dumps(r, ensure_ascii=False) + '\n')
    tot = Counter()
    for bf, c in summ.items(): tot.update(c)
    json.dump({'verses': nverse, 'coverage': cover, 'total': tot, 'by_book': {k: dict(v) for k, v in summ.items()}},
              open(os.path.join(REV, f'usage_audit_summary{suf}.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'절 {nverse:,} · 후보 {len(rows):,} · 참조 역본 {dict(cover)}')
    for k in sorted(tot): print(f'  {k}: {tot[k]}')

if __name__ == '__main__':
    main()
