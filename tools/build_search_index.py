# -*- coding: utf-8 -*-
"""성경 본문 검색 인덱스 생성 (전체 성경판).
전체 66권 KJV 영어 본문 + 번역된 한국어(있는 절만)를 하나로 묶는다.
→ 한글 검색은 번역분에서, 영어/원어매핑 검색은 구약 미번역분까지 전 성경에서 가능.
포맷: { "books":[{f,k,t}...66], "verses":[[bookIdx, ch, verse, koText|"", enText], ...] }
번역/원문 추가 후 이 스크립트를 다시 실행하면 검색 인덱스가 갱신된다.
"""
import json, os, glob, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

books = json.load(open('bible/books.json', encoding='utf-8'))

book_list = []   # [{f,k,t}] — 전체 66권(정경 순서)
verses = []      # [bookIdx, ch, v, ko, en]
translated_books = 0
ko_count = 0

for bi, b in enumerate(books):
    file = b['file']
    book_list.append({'f': file, 'k': b.get('ko', file), 't': b.get('t', 'nt')})
    kjv_path = f'bible/kjv/{file}.json'
    kjv = {}
    if os.path.exists(kjv_path):
        try:
            kjv = json.load(open(kjv_path, encoding='utf-8-sig'))
        except Exception:
            kjv = {}
    # 이 책에서 번역된 장 로드(있으면)
    kr_by_ch = {}
    for kr_path in glob.glob(f'bible/kr/{file}-*.json'):
        m = re.search(rf'{re.escape(file)}-(\d+)\.json$', kr_path.replace('\\', '/'))
        if not m:
            continue
        try:
            kr_by_ch[int(m.group(1))] = json.load(open(kr_path, encoding='utf-8'))
        except Exception:
            pass
    if kr_by_ch:
        translated_books += 1
    # 전체 장/절 순회 (영어는 전부, 한글은 있으면)
    for ch_key in sorted(kjv.keys(), key=lambda x: int(x)):
        ch = int(ch_key)
        en_verses = kjv[ch_key]
        ko_verses = kr_by_ch.get(ch, [])
        for i, en in enumerate(en_verses):
            ko = ko_verses[i] if i < len(ko_verses) else ''
            if ko:
                ko_count += 1
            verses.append([bi, ch, i + 1, ko, en])

out = {'books': book_list, 'verses': verses,
       'count': len(verses), 'koCount': ko_count}
with open('bible/search-index.json', 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, separators=(',', ':'))

size = os.path.getsize('bible/search-index.json') / 1024 / 1024
print(f'search-index.json: {len(verses)}절(전 성경) / 한글 {ko_count}절 / 번역책 {translated_books}권 / {size:.1f} MB')
