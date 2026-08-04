# -*- coding: utf-8 -*-
"""audit_report.py — 정본역 킹제임스 성경 감수 4단계: 바탕화면 보고서 생성.

산출: 바탕화면/정본역킹제임스성경_감수/ 폴더
  00_감수요약.md  10_인칭단복수.md  20_수동태.md  30_성별.md  40_고유명사.md  50_신명표기.md

승인 방식: 각 md의 체크박스를 [x] 로 바꾸면 tools/audit_collect_approved.py 가 수집.
"""
import json, os, sys, io, re
from collections import Counter, defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUD = os.path.join(ROOT, 'tools', '_audit')
BIBLE = os.path.join(ROOT, 'bible')
# 출력 경로 — 특정 PC 하드코딩 금지, 저장소 상대 경로 사용(2026-08-05 수정)
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tools', '_audit', 'report')
os.makedirs(OUT, exist_ok=True)

cands = [json.loads(l) for l in open(os.path.join(AUD, 'candidates.jsonl'), encoding='utf-8')]
verdicts = {}
for l in open(os.path.join(AUD, 'verdicts.jsonl'), encoding='utf-8'):
    v = json.loads(l)
    verdicts[v['id']] = v
by_id = {c['id']: c for c in cands}
books = json.load(open(os.path.join(BIBLE, 'books.json'), encoding='utf-8'))
BK = {b['file']: b for b in books}

def item_md(c, v=None, checkbox=True):
    fix = (v or {}).get('fix') or ''
    reason = (v or {}).get('reason') or ''
    box = '- [ ] ' if checkbox else '- '
    s = f"{box}**{c['ref']}** `{c['grade0']}` <!--id:{c['id']}-->\n"
    s += f"  - KJV: {c['kjv']}\n"
    s += f"  - 현행: {c['ko']}\n"
    s += f"  - 문제: {c['rule']}\n"
    if c.get('morph_note'):
        s += f"  - 원어: {c['morph_note']}\n"
    if fix:
        s += f"  - **수정안**: {fix}\n"
    if reason:
        s += f"  - 판정 근거: {reason}\n"
    return s

# ───── 그녀 사용 전수 집계 ─────
gnyeo = []
for b in books:
    for ch in range(1, b['ch'] + 1):
        p = os.path.join(BIBLE, 'kr', f"{b['file']}-{ch}.json")
        try:
            kr = json.load(open(p, encoding='utf-8'))
        except Exception:
            continue
        for i, v in enumerate(kr):
            if '그녀' in v:
                gnyeo.append((b['ko'], ch, i + 1, v))

# ═════ 10 인칭·단복수 ═════
per2 = [c for c in cands if c['cat'] == 'per2']
per13 = [c for c in cands if c['cat'] == 'per13']
err = [c for c in per2 if verdicts.get(c['id'], {}).get('verdict') == 'error']
pol = [c for c in per2 if verdicts.get(c['id'], {}).get('verdict') == 'policy']
okd = [c for c in per2 if verdicts.get(c['id'], {}).get('verdict') in ('ok', 'tradition')]
p13_err = [c for c in per13 if verdicts.get(c['id'], {}).get('verdict') == 'error']
p13_rest = [c for c in per13 if c not in p13_err]

md = ['# 10 · 인칭·단복수 (2인칭 thou/ye · 1·3인칭)', '',
      f'전권 스캔 {len(per2)+len(per13)}건 → 전건 판독 완료(2인칭) / 1·3인칭은 확정 1건 외 검토 그룹.', '',
      '## A. 확정 오류 — 수정안 확정 (체크하면 적용됩니다)', '']
for c in err:
    md.append(item_md(c, verdicts.get(c['id'])))
for c in p13_err:
    md.append(item_md(c, verdicts.get(c['id'])))
md += ['## B. 정책 결정 필요 — 집합적 단수(이스라엘 의인화)', '',
       'KJV·원어는 **단수**(thou, 2ms)로 이스라엘을 한 사람처럼 부르지만, 개역 전통과 현행 번역은 **너희**로 옮겼습니다.',
       '11건 개별이 아니라 **하나의 정책**으로 결정해 주세요:', '',
       '- [ ] **정책 P1**: 집합적 단수도 KJV·원어대로 단수(너/네)로 통일한다 <!--id:POLICY.collective-singular-->',
       '  - (체크하지 않으면 현행 유지 = 개역 전통 존중)', '  - 해당 절:']
for c in pol:
    md.append(f"    - {c['ref']} — {c['ko'][:60]}…")
md += ['', '## C. 판독 결과 정상(오탐/전통) — 참고', '']
for c in okd:
    v = verdicts.get(c['id'], {})
    md.append(f"- {c['ref']} — {v.get('reason','')[:80]}")
md += ['', '## D. 1·3인칭 검토 그룹 (LLM 개별 판독 전 후보)', '',
       f'{len(p13_rest)}건 — 한국어 대명사 생략·총칭 관용 때문에 오탐이 많은 범주입니다. 필요 시 2차 감수에서 개별 판독.', '']
for c in p13_rest[:15]:
    md.append(f"- {c['ref']} — {c['rule'][:30]} | {c['ko'][:56]}…")
if len(p13_rest) > 15:
    md.append(f'- … 외 {len(p13_rest)-15}건 (tools/_audit/candidates.jsonl)')
open(os.path.join(OUT, '10_인칭단복수.md'), 'w', encoding='utf-8').write('\n'.join(md) + '\n')

# ═════ 20 수동태 ═════
pas = [c for c in cands if c['cat'] == 'passive']
pasB = [c for c in pas if c['grade0'] == 'B']
pasC = [c for c in pas if c['grade0'] == 'C']
theo = [c for c in pasB if c.get('priority')]
bybook = Counter(c['book'] for c in pasB)
md = ['# 20 · 수동태 (영어 be+분사 ↔ 한국어 피동)', '',
      f'전권 스캔 후보 {len(pas)}건 → 원어 대조로 {len(pasC)}건 자동 기각(원어 비수동) → 남은 검토 후보 **{len(pasB)}건**.', '',
      '**파일럿 판독 결과(마태·창세기 표본 24건): 진짜 오류 0건.**',
      '남은 후보도 대부분 한국어가 능동·자동사·관용(예: 구원을 얻다)으로 정당하게 소화한 사례로 추정됩니다.',
      '따라서 수동태는 **일괄 수정 비권장** — 아래 신학 요주의 동사 포함 절만 우선 검토 대상으로 제시합니다.', '',
      f'## A. 신학 요주의 동사 포함 절 ({len(theo)}건) — 개별 검토 권장', '']
for c in theo[:40]:
    md.append(f"- [ ] **{c['ref']}** pp={','.join(c['evidence'].get('theo') or [])} <!--id:{c['id']}-->")
    md.append(f"  - KJV: {c['kjv'][:110]}")
    md.append(f"  - 현행: {c['ko'][:110]}")
    if c.get('morph_note'):
        md.append(f"  - 원어: {c['morph_note']}")
if len(theo) > 40:
    md.append(f'- … 외 {len(theo)-40}건')
md += ['', '## B. 책별 분포 (검토 후보 전체)', '']
for bf, n in bybook.most_common():
    md.append(f'- {BK[bf]["ko"]}: {n}건')
md += ['', f'## C. 자동 기각 {len(pasC)}건', '',
       '원어(히브리어 어간·헬라어 태)가 수동이 아니어서 기각 — 영어 be+분사가 완료·형용 용법인 경우.']
open(os.path.join(OUT, '20_수동태.md'), 'w', encoding='utf-8').write('\n'.join(md) + '\n')

# ═════ 30 성별 ═════
gen = [c for c in cands if c['cat'] == 'gender']
md = ['# 30 · 성별 (he/she ↔ 그/그녀)', '',
      f'전권 스캔 {len(gen)}건 — 파일럿 판독 결과 전부 **개역 전통 표기**(여성 3인칭도 그/그가, 그녀 미사용 원칙)로 정상.', '',
      '## A. 정책 확인 — 그녀 사용 일관성', '',
      f"현행 번역에서 `그녀`가 쓰인 절: **{len(gnyeo)}절** (나머지는 모두 '그'로 통일되어 있음)", '',
      '- [ ] **정책 P2**: 아래 절의 그녀를 개역 전통대로 그/그 여자로 통일한다 <!--id:POLICY.gnyeo-->', '']
for bko, ch, v, txt in gnyeo[:50]:
    md.append(f'  - {bko} {ch}:{v} — {txt[:70]}…')
if len(gnyeo) > 50:
    md.append(f'  - … 외 {len(gnyeo)-50}절')
md += ['', '## B. 전통 표기 기록 (참고, 조치 불필요)', '',
       f'여성(she)을 그/그가로 지칭한 절 등 {len(gen)}건 — 개역 전통과 일치. tools/_audit/candidates.jsonl 참조.']
open(os.path.join(OUT, '30_성별.md'), 'w', encoding='utf-8').write('\n'.join(md) + '\n')

# ═════ 40 고유명사 ═════
nc = json.load(open(os.path.join(AUD, 'name_concordance.json'), encoding='utf-8'))
md = ['# 40 · 고유명사 표기 통일 (이름 단위 — 1체크 = 해당 절 일괄)', '',
      '영어 철자(KJV) 기준 전권 콩코던스에서 한글 표기가 갈리는 이름입니다.', '']
for name, d in sorted(nc['variants'].items(), key=lambda x: -sum(x[1]['variants'].values())):
    forms = ' / '.join(f"{f}×{c}" for f, c in sorted(d['variants'].items(), key=lambda y: -y[1]))
    md.append(f"- [ ] **{name}** → `{d['expected']}` 로 통일 <!--id:NAME.{name}-->")
    md.append(f"  - 현황: {d['expected']}×{d['expected_hits']} vs {forms} (전체 {d['total']}회)")
    for f, refs in d['variant_refs'].items():
        md.append(f"  - {f} 출현: {', '.join(refs[:12])}{' …' if len(refs) > 12 else ''}")
md += ['', '## 참고 — 사전 뜻 충돌로 자동 검증 불가한 단어',
       f"{len(nc['unreliable_mapping'])}개 (Lot=제비, Ai=동물명 충돌 등) — 감수 대상 아님, 사전 정비 시 참조."]
open(os.path.join(OUT, '40_고유명사.md'), 'w', encoding='utf-8').write('\n'.join(md) + '\n')

# ═════ 50 신명 표기 ═════
dv = [c for c in cands if c['cat'] == 'divine']
dvA = [c for c in dv if c['grade0'] == 'A']
dvB = [c for c in dv if c['grade0'] == 'B']
dvC = [c for c in dv if c['grade0'] == 'C']
lordgod = [c for c in dvB if (c['evidence'] or {}).get('pattern') == 'Lord GOD']
lorddgod2 = [c for c in dvB if (c['evidence'] or {}).get('pattern') == 'LORD God']
dvB_rest = [c for c in dvB if not (c['evidence'] or {}).get('pattern')]
md = ['# 50 · 신명 표기 (LORD/GOD/JEHOVAH → 여호와, 번역지침 §4)', '',
      f'전권 스캔 {len(dv)}건 → 원어 렉심 대조로 자동 판별(H3068=여호와 / H0136=아도나이 / κύριος=주).', '',
      '## A. 확정 오류 (체크하면 적용)', '']
for c in dvA:
    v = verdicts.get(c['id'])
    if v and v.get('verdict') == 'error':
        md.append(item_md(c, v))
for c in dvA:
    v = verdicts.get(c['id'], {})
    if v.get('verdict') not in ('error', 'review', 'tradition', None):
        continue
gv = verdicts.get('GROUP.amos-lordgod.divine', {})
md += ['', "## B. 'Lord GOD'(아도나이 여호와) 패턴 — 그룹 결정", '',
       f"KJV `Lord GOD` = 아도나이+YHWH → 규례 **'주 여호와'**(개역 동일). 현행은 다수가 '주 하나님'.", '',
       f"- [ ] **그룹 G1**: 'Lord GOD' 패턴 {len(lordgod)}건 + 아모스 확정 8건을 '주 여호와'로 일괄 통일 <!--id:GROUP.lordgod-->",
       f"  - 근거: {gv.get('reason','')}", '  - 해당 절:']
amos_ids = {'Amos.1.8.divine','Amos.3.7.divine','Amos.3.8.divine','Amos.3.11.divine',
            'Amos.3.13.divine','Amos.4.2.divine','Amos.4.5.divine','Amos.5.3.divine'}
for c in dvA:
    if c['id'] in amos_ids:
        md.append(f"    - {c['ref']} — {c['ko'][:56]}…")
for c in lordgod[:30]:
    md.append(f"    - {c['ref']} — {c['ko'][:56]}…")
if len(lordgod) > 30:
    md.append(f'    - … 외 {len(lordgod)-30}건')
md += ['', "## C. 'LORD God'(여호와 엘로힘) 패턴", '']
for c in lorddgod2:
    v = verdicts.get(c['id'])
    md.append(item_md(c, v))
md += ['', '## D. 검토·해석 갈림 (참고)', '']
for cid in ('Nehemiah.3.5.divine', 'Hosea.12.14.divine'):
    c = by_id.get(cid)
    if c:
        md.append(item_md(c, verdicts.get(cid), checkbox=False))
md += ['', f'## E. 정당 판별 {len(dvC)}건 (자동 기각 — 조치 불필요)', '',
       '원어가 아도나이/아돈/엘로힘이거나(주·하나님이 정당), NT κύριος(주), 주어 생략 축약 등.']
open(os.path.join(OUT, '50_신명표기.md'), 'w', encoding='utf-8').write('\n'.join(md) + '\n')

# ═════ 00 요약 ═════
n_err = len(err) + len(p13_err) + len([c for c in dvA if verdicts.get(c['id'], {}).get('verdict') == 'error'])
md = ['# 정본역 킹제임스 성경 전수 감수 보고서', '',
      '영어 KJV(31,102절)와 원어(히브리어 TAHOT·헬라어 TAGNT/TR)를 전권 비교대조한 결과입니다.', '',
      '## 한눈 요약', '',
      '| 범주 | 스캔 후보 | 자동 판별 | 남은 결정 |',
      '|---|---|---|---|',
      f'| 인칭·단복수 | {len(per2)+len(per13)} | 판독 완료 | 확정 오류 {len(err)+len(p13_err)}건 + 정책 1건 |',
      f'| 수동태 | {len(pas)} | 원어로 {len(pasC)}건 기각 | 요주의 {len(theo)}건 검토(일괄 수정 비권장) |',
      f'| 성별 | {len(gen)} | 전통 표기 확인 | 그녀 일관성 정책 1건({len(gnyeo)}절) |',
      f'| 고유명사 | 491개 이름 | 7개 플래그 | 이름 단위 7건 |',
      f'| 신명 표기 | {len(dv)} | 원어 렉심 판별 | 확정 3건 + Lord GOD 그룹 1건 |', '',
      f'**즉시 수정 가능한 확정 오류: {n_err}건** (10·50번 파일의 A 섹션)', '',
      '## 승인 방법', '',
      '1. 각 파일의 체크박스 `- [ ]` 를 `- [x]` 로 바꾸면 승인입니다.',
      '2. 정책 항목(P1·P2·G1)은 1체크로 해당 절 전체에 일괄 적용됩니다.',
      '3. 저장 후 "승인 반영해줘"라고 말씀해 주시면 수정을 적용합니다(적용 전 dry-run 확인).', '',
      '## 데이터 정합성 주의(별도 발견)', '',
      '- 한국어 번역이 bible/kr(사이트 표시본)과 bible/en(주해본 ko필드) 두 곳에 있는데,',
      '  **구약 일부 책에서 en쪽이 낡아 있습니다**(3,290절 상이·62장은 절 분할 자체가 다름 — 에스겔·이사야·시편·에스더 등).',
      '  이번 감수·수정은 사이트 표시본(kr) 기준이며, en쪽 동기화는 별도 작업으로 권장합니다.', '',
      '## 방법·출처', '',
      '- 기준쌍: bible/kjv(KJV 영문) ↔ bible/kr(한국어) — 31,102절 완전 정렬 확인.',
      '- 규칙 스캔(6범주) → 원어 형태소 대조 → 파일럿(마태·창세기) 전건 판독으로 규칙 보정 → A급 40건 전건 판독.',
      '- 원어 데이터: STEPBible.org **TAHOT**(히브리어)·**TAGNT**(헬라어, TR 이문 태깅) — **CC BY 4.0**.',
      '  (원천 데이터는 저장소에 커밋하지 않고 로컬 캐시만 사용, 본 보고서에 출처 표기)',
      '- 신약은 KJV 기저본문(TR) 기준으로 판정 — NA(개역 계열)와 갈리는 절은 근거에 명시.']
open(os.path.join(OUT, '00_감수요약.md'), 'w', encoding='utf-8').write('\n'.join(md) + '\n')

print(f'보고서 생성 완료 → {OUT}')
print(f'  확정 오류 {n_err}건 / 정책 3건 / 이름 7건 / 요주의 수동태 {len(theo)}건')
print(f'  그녀 사용 {len(gnyeo)}절 / 수동태 자동기각 {len(pasC)}건 / 신명 자동판별 C {len(dvC)}건')
