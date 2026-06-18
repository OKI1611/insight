# -*- coding: utf-8 -*-
"""누락 퀴즈 출제용 — 배치별로 영상 제목 + 노트 핵심(thesis/오해/용어/핵심/성구)을 digest로 덤프."""
import json, io, os, re, sys
start = int(sys.argv[1]); n = int(sys.argv[2])
miss = [x for x in io.open('_missing_quiz.txt', encoding='utf-8').read().split('\n') if x.strip()]
batch = miss[start:start+n]
course = json.load(io.open('content/course.json', encoding='utf-8-sig'))
meta = {}
for lv in course.get('levels', []):
    for l in lv.get('lessons', []):
        y = (l.get('youtube') or '')
        m = re.search(r'[A-Za-z0-9_-]{11}', y)
        if m and m.group(0) not in meta:
            meta[m.group(0)] = (l.get('title', ''), lv.get('name', ''))
out = []
for vid in batch:
    title, lvl = meta.get(vid, ('?', '?'))
    out.append('### VID %s | TRACK %s' % (vid, lvl))
    out.append('TITLE: %s' % title)
    p = 'content/notes/%s.json' % vid
    note = None
    if os.path.exists(p):
        try: note = json.load(io.open(p, encoding='utf-8'))
        except: note = None
    if note:
        if note.get('thesis'): out.append('THESIS: ' + str(note['thesis']))
        for mc in (note.get('misconceptions') or [])[:4]:
            out.append('OHAE wrong=[%s] right=[%s]' % (mc.get('wrong', ''), mc.get('right', '')))
        for t in (note.get('terms') or [])[:6]:
            out.append('TERM %s = %s' % (t.get('term', ''), t.get('def', '')))
        for k in (note.get('takeaways') or [])[:5]:
            out.append('KEY: ' + (k if isinstance(k, str) else str(k)))
        for s in (note.get('scriptures') or [])[:3]:
            out.append('SCR %s — %s' % (s.get('ref', ''), s.get('note', '')))
    else:
        out.append('(노트 없음 — 제목+도메인지식으로 출제)')
    out.append('')
io.open('_qdigest.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('batch %d-%d of %d (count=%d)' % (start, start+n, len(miss), len(batch)))
