# -*- coding: utf-8 -*-
"""스페인어·일본어·중국어 번역 작업본을 기존 사전에 채워 넣는다(영어 등 기존 값은 그대로).

작업 폴더 i18n/pages/_work/l3/
  <이름>.todo.json      빠진 키 → 영어(참고용)
  <이름>.<lang>.json    번역 결과 {키: 번역}
대상: 이름이 common 이면 i18n/common.json, 그 밖에는 i18n/pages/<이름>.json
사용: python tools/i18n_merge_l3.py guide academy welcome common
검사(하나라도 걸리면 그 언어 그 키는 넣지 않고 보고): 한글 잔존 · {n} 개수 · 태그 동일 · 빈 값
"""
import json, os, re, sys
try: sys.stdout.reconfigure(encoding='utf-8')
except Exception: pass
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = f'{ROOT}/i18n/pages/_work/l3'
tags = lambda s: sorted(re.findall(r'<[^>]+>', s))
bad_total = 0
for name in sys.argv[1:]:
    tgt = f'{ROOT}/i18n/common.json' if name == 'common' else f'{ROOT}/i18n/pages/{name}.json'
    d = json.load(open(tgt, encoding='utf-8'))
    todo = json.load(open(f'{W}/{name}.todo.json', encoding='utf-8'))
    for L in ('es', 'ja', 'zh'):
        p = f'{W}/{name}.{L}.json'
        if not os.path.exists(p): print(f'{name} {L}: 작업본 없음'); continue
        tr = json.load(open(p, encoding='utf-8')); ok = bad = 0
        for k in todo:
            v = tr.get(k)
            why = ('없음' if v is None else '빈 값' if not v.strip() else '한글 잔존' if re.search('[가-힣]', v)
                   else '{n} 개수' if k.count('{n}') != v.count('{n}') else '태그 다름' if tags(k) != tags(v) else '')
            if why: bad += 1; print(f'  ✗ {name} {L} {why}: {k[:60]}'); continue
            if k in d and isinstance(d[k], dict): d[k][L] = v; ok += 1
        bad_total += bad
        print(f'{name} {L}: {ok}/{len(todo)} 채움' + (f', 문제 {bad}' if bad else ''))
    json.dump(d, open(tgt, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
print('문제 합계', bad_total)
