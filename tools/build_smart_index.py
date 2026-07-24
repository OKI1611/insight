# -*- coding: utf-8 -*-
"""통합 스마트 검색 인덱스 빌드 → content/smart-index.json
영상(강의노트 내용 흡수)·성경사전·주제별·칼럼을 한 파일로 모아 브라우저가 가볍게 교차검색."""
import json, os, re, glob

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def J(p):
    with open(os.path.join(BASE, p), encoding='utf-8-sig') as f: return json.load(f)

def yid(u):
    u = (u or '').strip()
    m = re.search(r'(?:v=|youtu\.be/|embed/|shorts/)([\w-]{11})', u)
    return m.group(1) if m else (u if len(u) == 11 else '')

def clip(s, n):
    s = re.sub(r'\s+', ' ', str(s or '')).strip()
    return s[:n]

items = []

# 1) 영상 강의 — course.json + notes 내용 흡수
course = J('content/course.json')
note_cache = {}
for lv in course['levels']:
    for le in lv.get('lessons', []):
        vid = yid(le.get('youtube', ''))
        if not vid: continue
        title = le.get('title', '')
        tags = ' '.join(le.get('tags', []) or [])
        summary = le.get('summary', '')
        kw_parts = [title, tags, summary, lv.get('name', '')]
        np = os.path.join(BASE, 'content', 'notes', vid + '.json')
        if os.path.exists(np):
            try:
                n = json.load(open(np, encoding='utf-8'))
                kw_parts.append(n.get('thesis', ''))
                kw_parts += [s.get('heading', '') for s in (n.get('sections') or [])]
                kw_parts += [t.get('term', '') for t in (n.get('terms') or [])]
                kw_parts += [s.get('ref', '') for s in (n.get('scriptures') or [])]
                kw_parts += (n.get('takeaways') or [])[:5]
            except Exception: pass
        items.append({
            't': 'video', 'ti': title,
            'sn': clip(summary or (note_cache.get(vid) or ''), 90),
            'kw': clip(' '.join(kw_parts), 900).lower(),
            'u': 'watch?v=' + vid,
            'free': bool(le.get('free'))
        })

# 2) 성경사전
for e in J('dictionary/entries.json'):
    term = e.get('term', '')
    kw = ' '.join([term, e.get('en', ''), e.get('category', ''),
                   ' '.join(e.get('related', []) or []),
                   ' '.join(s if isinstance(s, str) else s.get('ref', '') for s in (e.get('scriptures') or []))])
    items.append({
        't': 'dict', 'ti': term, 'sn': clip(e.get('def', ''), 90),
        'kw': clip(kw, 300).lower(), 'u': 'dictionary?q=' + term
    })

# 3) 주제별 성경
try:
    for t in J('content/themes.json').get('themes', []):
        items.append({
            't': 'theme', 'ti': t.get('title', ''),
            'sn': clip(t.get('intro', ''), 90),
            'kw': clip(' '.join([t.get('title', ''), t.get('en', ''), t.get('intro', '')]), 300).lower(),
            'u': 'themes#' + (t.get('id', ''))
        })
except Exception: pass

# 4) 칼럼·글 (posts.json: dict 안의 리스트 자동 탐색)
try:
    pj = J('content/posts.json')
    posts = pj if isinstance(pj, list) else next((v for v in pj.values() if isinstance(v, list)), [])
    for p in posts:
        if not isinstance(p, dict): continue
        title = p.get('title') or p.get('subject') or ''
        body = p.get('summary') or p.get('excerpt') or p.get('content') or p.get('body') or ''
        pid = p.get('id') or p.get('slug') or ''
        items.append({
            't': 'post', 'ti': title, 'sn': clip(body, 90),
            'kw': clip(title + ' ' + body, 400).lower(),
            'u': 'column' + (('?id=' + str(pid)) if pid else '')
        })
except Exception: pass

# 5) 성경 번역 이야기 (translation-notes.json)
try:
    tn = J('content/translation-notes.json')
    for n in tn.get('notes', []):
        if not isinstance(n, dict): continue
        title = n.get('title') or ''
        body = (n.get('summary') or '') + ' ' + (n.get('verse') or '') + ' ' + ' '.join(n.get('tags') or [])
        items.append({
            't': 'post', 'ti': '[번역 이야기] ' + title, 'sn': clip(n.get('summary') or '', 90),
            'kw': clip(title + ' ' + body, 400).lower(),
            'u': 'translation-notes?id=' + str(n.get('id') or '')
        })
except Exception: pass

out = {'count': len(items), 'items': items}
op = os.path.join(BASE, 'content', 'smart-index.json')
json.dump(out, open(op, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
size = os.path.getsize(op)
by = {}
for it in items: by[it['t']] = by.get(it['t'], 0) + 1
print(f'smart-index.json 생성: {len(items)}건 ({by}) · {size//1024}KB')
