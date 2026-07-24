# -*- coding: utf-8 -*-
"""audit_enrich.py — 감수 2.5단계: 후보(candidates.jsonl)에 원어 형태소 근거를 병합하고 재등급.

재등급 규칙:
  divine (구약):
    lex에 H3068/H3069(여호와) → A 확정(원어 근거 첨부)
    lex에 아도나이(H0136)·엘로힘(H0430)·엘(H0410)만 → C(주/하나님 정당 — 전통 표기)
    형태소 데이터 없음 → 등급 유지
  divine (신약): B 유지(κύριος 전통상 '주')
  passive:
    구약: 니팔/푸알/호팔 존재 → B 유지 + 원어 근거 / 능동 어간만 존재 → C(원어 비수동 — 자동 기각)
    신약: P(수동)/E(중수동) 존재 → B 유지 + 근거 / 능동·중간만 → C
  per2: 원어 2인칭 수(p2) 근거 첨부. 원어가 KJV와 일치하면 A 확정 표시.

사용: python tools/audit_enrich.py
산출: tools/_audit/candidates.jsonl (덮어씀), enrich_summary.txt
"""
import json, os, sys, io
from collections import Counter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUD = os.path.join(ROOT, 'tools', '_audit')
MORPH = os.path.join(AUD, 'morph')

def main():
    cands = [json.loads(l) for l in open(os.path.join(AUD, 'candidates.jsonl'), encoding='utf-8')]
    books = {b['file']: b for b in json.load(open(os.path.join(ROOT, 'bible', 'books.json'), encoding='utf-8'))}
    cache = {}
    def morph_of(bf, ch, v):
        if bf not in cache:
            p = os.path.join(MORPH, bf + '.json')
            cache[bf] = json.load(open(p, encoding='utf-8')) if os.path.exists(p) else {}
        return cache[bf].get(f'{ch}:{v}')

    shifts = Counter()
    for c in cands:
        m = morph_of(c['book'], c['ch'], c['v'])
        if not m:
            shifts[(c['cat'], 'no-morph')] += 1
            continue
        c['morph'] = m
        is_nt = books[c['book']]['t'] == 'nt'
        cat, g0 = c['cat'], c['grade0']

        if cat == 'divine' and not is_nt:
            lex = set(m.get('lex') or [])
            ev = c.get('evidence') or {}
            plain_missing = (ev.get('have') == 0) and not ev.get('vocative') and not ev.get('pattern')
            if {'H3068', 'H3069'} & lex:
                # 완전 미표기(비호격)만 A 확정 승격. 호격·패턴·횟수부족은 아도나이 병존 가능 → 등급 유지
                if plain_missing:
                    if g0 != 'A':
                        shifts[('divine', f'{g0}→A(원어 여호와)')] += 1
                    c['grade0'] = 'A'
                c['morph_note'] = '원어 렉심에 여호와(H3068) 존재'
            elif lex & {'H0136', 'H0430', 'H0410', 'H3050'}:
                shifts[('divine', f'{g0}→C(원어 아도나이/엘로힘)')] += 1
                c['grade0'] = 'C'
                c['morph_note'] = '원어가 아도나이/엘로힘 계열 — 주/하나님 번역 정당(KJV 인쇄 관례)'
            else:
                shifts[('divine', '렉심 미검출')] += 1

        elif cat == 'passive':
            if is_nt:
                voices = set(m.get('voices') or [])
                if {'P', 'E'} & voices:
                    c['morph_note'] = '헬라어(TR)에 수동/중수동 동사 존재'
                    shifts[('passive', 'B 유지(헬라 수동)')] += 1
                elif voices:
                    c['grade0'] = 'C'
                    c['morph_note'] = '헬라어(TR) 동사가 능동/중간뿐 — 영어 be+분사는 완료·형용 용법 추정'
                    shifts[('passive', 'B→C(헬라 비수동)')] += 1
                else:
                    shifts[('passive', '동사 미검출')] += 1
            else:
                stems = set(m.get('stems') or [])
                if stems & {'niphal', 'pual', 'hophal'}:
                    c['morph_note'] = f"히브리어 수동 어간 존재: {sorted(stems & {'niphal','pual','hophal'})}"
                    shifts[('passive', 'B 유지(히브리 수동)')] += 1
                elif stems:
                    c['grade0'] = 'C'
                    c['morph_note'] = '히브리어 동사가 능동 어간뿐 — 상태·완료 표현 추정'
                    shifts[('passive', 'B→C(히브리 비수동)')] += 1
                else:
                    shifts[('passive', '동사 미검출')] += 1

        elif cat == 'per2':
            p2 = set(m.get('p2') or [])
            want = 'p' if '복수' in c['rule'].split('인데')[0] else 's'
            if p2 == {want}:
                c['morph_note'] = f"원어 2인칭 수 = {'복수' if want=='p' else '단수'} — KJV와 일치, 오류 확정"
                shifts[('per2', 'A 확정(원어 일치)')] += 1
            elif p2 and want not in p2:
                c['grade0'] = 'B'
                c['morph_note'] = f"원어 2인칭 수({sorted(p2)})가 KJV와 다름 — 본문·정책 검토 필요"
                shifts[('per2', 'A→B(원어-KJV 불일치)')] += 1
            elif p2:
                c['morph_note'] = f"원어 2인칭 수 혼재: {sorted(p2)}"
                shifts[('per2', '혼재')] += 1
            else:
                shifts[('per2', '2인칭 미검출')] += 1

    out = os.path.join(AUD, 'candidates.jsonl')
    with open(out, 'w', encoding='utf-8') as f:
        for c in cands:
            f.write(json.dumps(c, ensure_ascii=False) + '\n')

    grade_now = Counter((c['cat'], c['grade0']) for c in cands)
    lines = ['재등급 이동:']
    for k, v in sorted(shifts.items()):
        lines.append(f'  {k[0]} {k[1]}: {v}')
    lines.append('현재 등급 분포:')
    for (cat, g), v in sorted(grade_now.items()):
        lines.append(f'  {cat} [{g}]: {v}')
    text = '\n'.join(lines)
    open(os.path.join(AUD, 'enrich_summary.txt'), 'w', encoding='utf-8').write(text + '\n')
    print(text)

if __name__ == '__main__':
    main()
