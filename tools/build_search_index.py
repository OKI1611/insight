# -*- coding: utf-8 -*-
"""성경 본문 검색 인덱스 생성.
번역된 한국어 절(bible/kr/<Book>-<ch>.json) + 대응 KJV 영어 절(bible/kjv/<Book>.json)을
콤팩트 배열 포맷으로 묶어 bible/search-index.json 으로 출력한다.
포맷: { "books":[{f,k,t}...], "verses":[[bookIdx, ch, verse, koText, enText], ...] }
번역 추가 후 이 스크립트를 다시 실행하면 검색 인덱스가 갱신된다.
"""
import json, os, glob, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

books = json.load(open('bible/books.json', encoding='utf-8'))
meta = {b['file']: b for b in books}

book_list = []          # [{f,k,t}]
book_index = {}         # file -> idx
verses = []             # [bookIdx, ch, v, ko, en]

def book_idx(file):
    if file not in book_index:
        m = meta.get(file, {'file': file, 'ko': file, 't': 'nt'})
        book_index[file] = len(book_list)
        book_list.append({'f': file, 'k': m.get('ko', file), 't': m.get('t', 'nt')})
    return book_index[file]

# 책별로 모아 정경 순서대로
for b in books:
    file = b['file']
    kjv_path = f'bible/kjv/{file}.json'
    kjv = {}
    if os.path.exists(kjv_path):
        try:
            kjv = json.load(open(kjv_path, encoding='utf-8-sig'))
        except Exception:
            kjv = {}
    # 이 책의 번역된 장들
    chs = []
    for kr_path in glob.glob(f'bible/kr/{file}-*.json'):
        m = re.search(rf'{re.escape(file)}-(\d+)\.json$', kr_path.replace('\\', '/'))
        if m:
            chs.append(int(m.group(1)))
    if not chs:
        continue
    bi = None
    for ch in sorted(chs):
        kr_path = f'bible/kr/{file}-{ch}.json'
        try:
            ko_verses = json.load(open(kr_path, encoding='utf-8'))
        except Exception:
            continue
        en_verses = kjv.get(str(ch), [])
        if bi is None:
            bi = book_idx(file)
        for i, ko in enumerate(ko_verses):
            en = en_verses[i] if i < len(en_verses) else ''
            verses.append([bi, ch, i + 1, ko, en])

out = {'books': book_list, 'verses': verses,
       'count': len(verses), 'bookCount': len(book_list)}
with open('bible/search-index.json', 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, separators=(',', ':'))

size = os.path.getsize('bible/search-index.json') / 1024
print(f'search-index.json 작성: {len(verses)}절 / {len(book_list)}권 / {size:.1f} KB')
