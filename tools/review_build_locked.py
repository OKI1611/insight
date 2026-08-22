# -*- coding: utf-8 -*-
"""review_build_locked.py — 전수 검토에서 '재작성 금지(경고만)' 절 목록을 만든다.

근거:
  1) tools/tr_battery.json 의 verses_must_exist · tr_phrases(ref)   — TR 정합 확정 절
  2) 지난 감수에서 사용자 승인으로 확정한 절 — 커밋을 부모와 비교해 실제로 바뀐 절만 추출
       7f6145c  ὑπακούω/ὑποτάσσω 전수감수 8절(2026-07-25)
       3fb048e  음부 3분 체계 정밀 보수(2026-08-08)
       717523c  출간 전 전수감수 TR 정합 17절 복원 + 표기 통일 111곳
  3) 배터리 counts 가 세는 단어(독생자·셀라)를 품은 절 — 단어 수 변동 금지

산출: tools/review_locked.json  { "Romans-6-2": ["battery:must 그럴 수 없느니라"], ... }
사용: python tools/review_build_locked.py
"""
import json, os, sys, io, subprocess, re
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIBLE = os.path.join(ROOT, 'bible')
OUT = os.path.join(ROOT, 'tools', 'review_locked.json')
COMMITS = {'7f6145c': '감수 2026-07-25 순종/복종', '3fb048e': '감수 2026-08-08 음부 3분 체계', '717523c': '감수 2026-07-31 TR 정합·표기 통일'}

locked = defaultdict(list)
books = json.load(open(os.path.join(BIBLE, 'books.json'), encoding='utf-8'))

# 1) 배터리
b = json.load(open(os.path.join(ROOT, 'tools', 'tr_battery.json'), encoding='utf-8'))
for it in b.get('verses_must_exist', []):
    locked[it['ref']].append('battery:must_exist')
for it in b.get('tr_phrases', []):
    locked[it['ref']].append('battery:must ' + it.get('must', ''))

# 2) 감수 확정 커밋 — 부모와 비교해 바뀐 절
def git_show(rev, path):
    try:
        out = subprocess.run(['git', 'show', f'{rev}:{path}'], cwd=ROOT, capture_output=True).stdout
        return json.loads(out.decode('utf-8'))
    except Exception:
        return None
for c, label in COMMITS.items():
    files = subprocess.run(['git', 'show', '--stat=200', '--format=', c], cwd=ROOT, capture_output=True).stdout.decode('utf-8', 'replace')
    for m in re.finditer(r'bible/kr/([A-Za-z0-9]+)-(\d+)\.json', files):
        bf, ch = m.group(1), m.group(2)
        new = git_show(c, f'bible/kr/{bf}-{ch}.json'); old = git_show(c + '~1', f'bible/kr/{bf}-{ch}.json')
        if not isinstance(new, list) or not isinstance(old, list): continue
        for i in range(min(len(new), len(old))):
            if new[i] != old[i]:
                locked[f'{bf}-{ch}-{i+1}'].append(label)

# 3) counts 대상 단어를 품은 절
for it in b.get('counts', []):
    pat = it.get('pattern'); scope = it.get('scope', 'all')
    if not pat or pat == '여호와': continue         # 신약 여호와 0건은 금지어로 이미 처리
    bk = [x for x in books if scope == 'all' or (scope.startswith('books:') and x['file'] in scope[6:].split(',')) or (scope in ('ot', 'nt') and x['t'] == scope)]
    for x in bk:
        for ch in range(1, x['ch'] + 1):
            try: arr = json.load(open(os.path.join(BIBLE, 'kr', f"{x['file']}-{ch}.json"), encoding='utf-8'))
            except Exception: continue
            for i, v in enumerate(arr):
                if pat in (v or ''): locked[f"{x['file']}-{ch}-{i+1}"].append(f'battery:count {pat}')

json.dump(dict(sorted(locked.items())), open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
src = defaultdict(int)
for v in locked.values():
    for s in v: src[s.split(' ')[0]] += 1
print(f'잠금 절 {len(locked)}개 → tools/review_locked.json')
print('  출처별:', dict(src))
