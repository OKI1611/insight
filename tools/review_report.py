# -*- coding: utf-8 -*-
"""review_report.py — 정본역 전수 검토: 권별 검수표(markdown) 생성 + 제안 코드 검증.

입력
  tools/_review/proposals/<Book>-<ch>[-pN].json   (검토 에이전트 출력, verses 배열)
     항목: {v, verdict:"keep|revise", change_kind:"mechanical|reword|meaning", proposed, reasons:[…],
            kjv_map:[…], orig_note, en_updates:{note,voc,idi}, footnote, needs_user, user_question,
            alt_proposed, confidence}
  tools/_review/candidates.jsonl 또는 candidates-<Book>.jsonl (스캔 신호)
산출
  tools/_review/report/<권 한글명>.md   — 맨 위 「사장님 결정 필요」, 이어 절별 카드(- [ ] 체크박스), 통계
  tools/_review/approved-<Book>.json    — 검수표에서 [x] 표시된 항목을 review_apply.py 입력 형식으로 추출(--collect)
검증(제안문에 대해 코드로)
  · S1 재실행: 제안문이 여전히 타 역본과 A/B 인지
  · S3 재실행 + 금지 어미(…합니다/…했다/…이다/…한다) + 금지어(배터리 forbidden) + 잠금 절 수정 여부
  · 고유명사·§5 용어 보존(현행 절에 있던 마스킹 용어가 제안문에서 사라졌는지)
  · 배터리 must 어구 보존
  → 경고를 카드에 표시(적용은 사장님 판단)
사용
  python tools/review_report.py --book Romans            # 검수표 생성
  python tools/review_report.py --book Romans --collect  # [x] 수집 → approved-Romans.json
  python tools/review_report.py --book Romans --out "C:\\Users\\josep\\Desktop\\정본역_전수검토"   # 복사본
"""
import json, os, re, sys, io, argparse, glob, shutil

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
BIBLE = os.path.join(ROOT, 'bible')
REV = os.path.join(ROOT, 'tools', '_review')
REP = os.path.join(REV, 'report'); os.makedirs(REP, exist_ok=True)
BOOKS = {b['file']: b for b in json.load(open(os.path.join(BIBLE, 'books.json'), encoding='utf-8'))}

import review_scan as RS   # 정규화·S1·S3·소스 재사용

BAD_END = re.compile(r'(합니다|습니다|했다|한다|이다|였다|된다|않다|없다|있다)[.!?]?\s*$')
MASK_KEEP = RS.MASK_TERMS

def load_kr(bf, ch):
    return json.load(open(os.path.join(BIBLE, 'kr', f'{bf}-{ch}.json'), encoding='utf-8'))
def load_kjv(bf):
    return json.load(open(os.path.join(BIBLE, 'kjv', f'{bf}.json'), encoding='utf-8'))

def verify(ref, cur, prop, must):
    warns = []
    # S1 재실행
    best = None
    for ver, src in RS.SOURCES.items():
        rt = src.get(ref)
        if not rt: continue
        m = RS.s1_compare(prop, rt); g = RS.s1_grade(m, len(prop), 'kr' if ver in RS.VERS_KR else 'kj')
        if g and (best is None or g < best[0]): best = (g, RS.VNAME[ver], m['charsim'])
    if best and best[0] in ('A', 'B'): warns.append(f'제안문도 {best[1]}와 {best[0]}등급(유사도 {best[2]})')
    for w in RS.s3_check(prop): warns.append('S3: ' + w)
    if BAD_END.search(prop): warns.append('금지 어미(현대체) 의심')
    for f in RS.FORBIDDEN:
        if f in prop and f not in cur: warns.append(f'금지어 유입: {f}')
    if must and must not in prop: warns.append(f'배터리 must 어구 소실: {must}')
    for t in MASK_KEEP:
        if t in cur and t not in prop: warns.append(f'용어/신명 소실: {t}')
    if ref in RS.LOCKED: warns.append('잠금 절(재작성 금지): ' + '; '.join(RS.LOCKED[ref]))
    return warns

def build(bf):
    b = BOOKS[bf]; kjv = load_kjv(bf)
    cand = {}
    cp = os.path.join(REV, f'candidates-{bf}.jsonl')
    if not os.path.exists(cp): cp = os.path.join(REV, 'candidates.jsonl')
    if os.path.exists(cp):
        for l in open(cp, encoding='utf-8'):
            r = json.loads(l)
            if r['book'] == bf: cand[r['ref']] = r
    props = {}
    for p in sorted(glob.glob(os.path.join(REV, 'proposals', f'{bf}-*.json'))):
        try: d = json.load(open(p, encoding='utf-8'))
        except Exception as e: print('!! 제안 파일 파싱 실패', p, e); continue
        ch = int(re.search(r'-(\d+)(?:-p\d+)?\.json$', p).group(1))
        for it in d.get('verses', d if isinstance(d, list) else []):
            props[f'{bf}-{ch}-{it["v"]}'] = it
    decide, cards = [], []
    stats = {'revise': 0, 'keep': 0, 'needs_user': 0, 'mechanical': 0, 'reword': 0, 'meaning': 0, 'warn': 0}
    for ch in range(1, b['ch'] + 1):
        kr = load_kr(bf, ch); kv = kjv.get(str(ch), [])
        for i, cur in enumerate(kr):
            v = i + 1; ref = f'{bf}-{ch}-{v}'
            it = props.get(ref)
            if not it or it.get('verdict', 'keep') != 'revise' or not it.get('proposed'):
                if it: stats['keep'] += 1
                continue
            stats['revise'] += 1; stats[it.get('change_kind', 'reword')] = stats.get(it.get('change_kind', 'reword'), 0) + 1
            c = cand.get(ref, {})
            warns = verify(ref, cur, it['proposed'], RS.MUST.get(ref))
            if warns: stats['warn'] += 1
            s1 = c.get('s1'); s2 = c.get('s2')
            lines = [f"### {b['ko']} {ch}:{v}  <!--id:{ref}-->", '',
                     f"- [ ] **채택**  (종류: {it.get('change_kind','reword')} · 사유: {', '.join(it.get('reasons', []))}" + (f" · 확신도 {it.get('confidence')}" if it.get('confidence') is not None else '') + ')',
                     f"- KJV: {kv[i] if i < len(kv) else ''}",
                     f"- 현행: {cur}",
                     f"- **수정안**: {it['proposed']}"]
            if it.get('alt_proposed'): lines.append(f"- 2안: {it['alt_proposed']}")
            if s1: lines.append(f"- 유사도: {RS.VNAME[s1['ver']]} {s1['grade']} (편집유사도 {s1['charsim']}, 공통 어절 {s1['run']}, 3-gram {s1['cov3']})")
            if s2: lines.append('- KJV 핵심어: ' + '; '.join(f"{x['word']}{'(원어 '+','.join(x['strongs'])+')' if x.get('strongs') else ''}{' 불일치' if not x['ok'] else ''}{' KJV≠원어' if x.get('kjv_ne_orig') else ''}" for x in s2))
            if it.get('kjv_map'): lines.append('- 단어 대응: ' + '; '.join(f"{m.get('kjv_word')}={m.get('strong','')} {m.get('gloss','')} → {m.get('ko_proposed','')}" for m in it['kjv_map'][:6]))
            if it.get('orig_note'): lines.append(f"- 원어 근거: {it['orig_note']}")
            if it.get('en_updates'): lines.append(f"- en 노트 변경: {json.dumps(it['en_updates'], ensure_ascii=False)[:300]}")
            if it.get('footnote'): lines.append(f"- 각주 제안: {it['footnote']}")
            if warns: lines.append('- ⚠ 검증 경고: ' + ' / '.join(warns))
            lines.append('')
            cards.append('\n'.join(lines))
            if it.get('needs_user'):
                stats['needs_user'] += 1
                decide.append('\n'.join([f"### {b['ko']} {ch}:{v}  <!--id:{ref}-->", '',
                    f"- KJV: {kv[i] if i < len(kv) else ''}", f"- 현행: {cur}",
                    f"- 원어: {it.get('orig_note','')}", f"- **질문**: {it.get('user_question','')}",
                    f"- 1안(KJV 단어 방향): {it['proposed']}", f"- 2안(원어/현행 방향): {it.get('alt_proposed','(현행 유지)')}",
                    '- 결정: [ ] 1안   [ ] 2안   [ ] 현행 유지   [ ] 기타(아래에 적어 주세요)', '']))
    head = [f"# 정본역 전수 검토 — {b['ko']} 검수표", '',
            f"제안 {stats['revise']}절(기계적 {stats.get('mechanical',0)} · 표현 {stats.get('reword',0)} · 의미 {stats.get('meaning',0)}) · 검증 경고 {stats['warn']}절 · 사장님 결정 필요 {stats['needs_user']}절",
            '', '사용법: 채택할 항목의 `- [ ]` 를 `- [x]` 로 바꾸거나, 채팅으로 "로마서 N장 M절 채택/제외" 로 알려 주세요.',
            '⚠ 이 파일에는 비교용으로 타 역본 유사도 수치만 담겨 있습니다(본문 미포함). 저장소에 올리지 않습니다.', '']
    md = '\n'.join(head)
    if decide: md += '\n## 사장님 결정 필요 (KJV 단어 ≠ 원어, 개역과 크게 다름)\n\n' + '\n'.join(decide)
    md += '\n## 절별 수정안\n\n' + '\n'.join(cards) if cards else '\n(제안 없음)\n'
    out = os.path.join(REP, f"{b['ko']}.md")
    open(out, 'w', encoding='utf-8').write(md)
    print(f"검수표 → {out}   (제안 {stats['revise']} · 결정필요 {stats['needs_user']} · 경고 {stats['warn']})")
    return out

def collect(bf):
    b = BOOKS[bf]; path = os.path.join(REP, f"{b['ko']}.md")
    md = open(path, encoding='utf-8').read()
    props = {}
    for p in sorted(glob.glob(os.path.join(REV, 'proposals', f'{bf}-*.json'))):
        d = json.load(open(p, encoding='utf-8')); ch = int(re.search(r'-(\d+)(?:-p\d+)?\.json$', p).group(1))
        for it in d.get('verses', []): props[f'{bf}-{ch}-{it["v"]}'] = it
    out = []
    for m in re.finditer(r'### .*?<!--id:([A-Za-z0-9-]+)-->\n\n- \[x\]', md):
        ref = m.group(1); it = props.get(ref)
        if not it: continue
        bf2, ch, v = re.match(r'^([A-Za-z0-9]+)-(\d+)-(\d+)$', ref).groups()
        cur = load_kr(bf2, int(ch))[int(v) - 1]
        out.append({'ref': ref, 'old': cur, 'new': it['proposed'], 'en': it.get('en_updates') or {}})
    op = os.path.join(REV, f'approved-{bf}.json')
    json.dump(out, open(op, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'채택 {len(out)}건 → {op}')

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--book', required=True); ap.add_argument('--collect', action='store_true'); ap.add_argument('--out')
    a = ap.parse_args()
    if a.collect: collect(a.book); return
    out = build(a.book)
    if a.out:
        os.makedirs(a.out, exist_ok=True); shutil.copy(out, os.path.join(a.out, os.path.basename(out))); print('복사 →', a.out)

if __name__ == '__main__':
    main()
