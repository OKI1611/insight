# -*- coding: utf-8 -*-
"""매일 말씀과 함께 — 묵상 색인 생성.
content/daily/<YYYY-MM-DD>.json 들을 스캔해 content/daily/index.json(날짜·제목·본문 목록) 작성.
묵상글 추가/발행 후 이 스크립트를 실행하면 daily.html 목록이 갱신된다.
"""
import json, os, glob, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

items = []
for f in glob.glob('content/daily/*.json'):
    name = os.path.basename(f)
    if name.startswith('_') or name == 'index.json':
        continue
    m = re.match(r'(\d{4}-\d{2}-\d{2})\.json$', name)
    if not m:
        continue
    try:
        d = json.load(open(f, encoding='utf-8'))
    except Exception:
        continue
    items.append({'date': m.group(1), 'ref': d.get('ref', ''), 'title': d.get('title', '')})

items.sort(key=lambda x: x['date'])
out = {'dates': [x['date'] for x in items], 'items': items, 'count': len(items)}
json.dump(out, open('content/daily/index.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'index.json: {len(items)}개 묵상 색인 ({items[0]["date"] if items else "-"} ~ {items[-1]["date"] if items else "-"})')
