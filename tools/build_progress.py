# -*- coding: utf-8 -*-
"""정본역 킹제임스 성경 진행현황 빌드 — bible/kr/*.json 을 스캔해 bible/progress.json 생성.
번역을 추가한 뒤 `python tools/build_progress.py` 를 다시 실행하면 작업현황이 갱신된다.
(이 파일은 관리자 작업현황 페이지 kjv-admin.html 이 읽는 데이터다.)"""
import os, json, glob, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KR = os.path.join(ROOT, 'bible', 'kr')
EN = os.path.join(ROOT, 'bible', 'en')

with open(os.path.join(ROOT, 'bible', 'books.json'), encoding='utf-8-sig') as f:
    books = json.load(f)

done = {}   # file -> set(chapters)
for path in glob.glob(os.path.join(KR, '*.json')):
    name = os.path.basename(path)[:-5]
    m = re.match(r'^(.*)-(\d+)$', name)
    if not m:
        continue
    book, ch = m.group(1), int(m.group(2))
    # 유효한 JSON 배열인지, 빈 배열이 아닌지 확인
    try:
        with open(path, encoding='utf-8-sig') as fp:
            data = json.load(fp)
        if not isinstance(data, list) or len(data) == 0:
            continue
    except Exception:
        continue
    done.setdefault(book, set()).add(ch)

en_done = {}
for path in glob.glob(os.path.join(EN, '*.json')):
    name = os.path.basename(path)[:-5]
    m = re.match(r'^(.*)-(\d+)$', name)
    if m:
        en_done.setdefault(m.group(1), set()).add(int(m.group(2)))

out_books = []
total_ch = 0
total_done = 0
for b in books:
    fl = b['file']
    d = sorted(done.get(fl, set()))
    ed = en_done.get(fl, set())
    total_ch += b['ch']
    total_done += len(d)
    out_books.append({
        'file': fl, 'ko': b['ko'], 'ch': b['ch'], 't': b['t'],
        'done': len(d),
        'enDone': len([c for c in d if c in ed]),
        'chapters': d,
    })

result = {
    'totalChapters': total_ch,
    'totalDone': total_done,
    'percent': round(total_done / total_ch * 100, 1) if total_ch else 0,
    'booksStarted': len([b for b in out_books if b['done'] > 0]),
    'booksComplete': len([b for b in out_books if b['done'] == b['ch']]),
    'books': out_books,
}

with open(os.path.join(ROOT, 'bible', 'progress.json'), 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=1)

print('progress.json written:',
      result['totalDone'], '/', result['totalChapters'],
      '(' + str(result['percent']) + '%)',
      '| books complete:', result['booksComplete'])
