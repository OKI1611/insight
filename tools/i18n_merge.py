# -*- coding: utf-8 -*-
"""페이지별 번역 작업본(i18n/pages/_work/<page>.<lang>.json)을 i18n/pages/<page>.json 하나로 합친다.

사용: python tools/i18n_merge.py index
  - 키 목록: i18n/pages/_work/<page>.items.json ({"k","type"})
  - 언어별 작업본이 없거나 키가 빠지면 그 언어는 한국어로 남는다(알려 줌)
  - 끝나면 i18n.js 의 PAGES 배열에 페이지 이름이 있는지 확인할 것
"""
import json, sys, os, re
try: sys.stdout.reconfigure(encoding='utf-8')
except Exception: pass
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
page = sys.argv[1]
W = f'{ROOT}/i18n/pages/_work'
items = json.load(open(f'{W}/{page}.items.json', encoding='utf-8'))
out = {'_about': f'{page} 페이지 화면 글자. 원본 목록 _work/{page}.items.json, 합치기 tools/i18n_merge.py. 용어 기준 i18n/GLOSSARY.md'}
SKIP = {'한국어'}  # 언어 선택 단추 글자(번역 대상 아님)
items = [it for it in items if it['k'] not in SKIP]
for it in items: out[it['k']] = {}
for L in ['en', 'es', 'ja', 'zh']:
    p = f'{W}/{page}.{L}.json'
    if not os.path.exists(p): print(f'  {L}: 작업본 없음'); continue
    tr = json.load(open(p, encoding='utf-8')); miss = 0
    for it in items:
        v = tr.get(it['k'])
        if v and not re.search('[가-힣]', v): out[it['k']][L] = v
        else: miss += 1
    print(f'  {L}: {len(items) - miss}/{len(items)}')
# 숫자 칸 옆에 따로 이름표가 붙는 곳('384편' + '무료 강의')은 숫자만 남긴다 — 'n lectures Free lectures' 겹침 방지
OVERRIDE = {'{n}편': {'en': '{n}', 'es': '{n}', 'ja': '{n}', 'zh': '{n}'}}
for k, v in OVERRIDE.items():
    if k in out: out[k] = v
json.dump(out, open(f'{ROOT}/i18n/pages/{page}.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('저장:', f'i18n/pages/{page}.json')
js = open(f'{ROOT}/i18n.js', encoding='utf-8').read()
if f"'{page}'" not in js.split('var PAGES')[1].split(';')[0]: print('⚠ i18n.js PAGES 배열에', page, '추가 필요')
