# -*- coding: utf-8 -*-
"""sitemap.xml 생성기.
공개(인덱싱) 페이지 목록 + 기존 동적 URL(watch?l=N 등)을 보존하여 sitemap을 새로 쓴다.
실행: python tools/build_sitemap.py  (lastmod는 인자로 받음 — 없으면 기존 동적은 보존, 정적은 STAMP)
"""
import os, re, sys, io, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

BASE = 'https://biblynote.com'
STAMP = sys.argv[1] if len(sys.argv) > 1 else '2026-06-28'

# (clean-url, priority) — 공개 인덱싱 페이지
PAGES = [
    ('/', '1.0'),
    ('/welcome', '0.8'), ('/about', '0.8'),
    ('/bible', '0.9'), ('/dictionary', '0.9'), ('/memorize', '0.8'),
    ('/curriculum', '0.9'), ('/academy', '0.7'), ('/themes', '0.8'),
    ('/preachers', '0.8'), ('/booklet', '0.7'), ('/store-help', '0.4'),
    ('/community', '0.6'), ('/prayers', '0.7'), ('/column', '0.6'),
    ('/find', '0.6'), ('/counsel', '0.5'), ('/request', '0.5'),
    ('/resources', '0.6'), ('/notices', '0.6'), ('/event', '0.7'),
    ('/founding', '0.6'), ('/support', '0.5'), ('/mylearning', '0.4'),
    ('/bible-plan', '0.6'), ('/daily', '0.8'), ('/books', '0.7'),
    ('/terms', '0.3'), ('/privacy', '0.3'),
    ('/translation', '0.6'), ('/translation-notes', '0.7'),
]

# 개별 글 URL — 목록 페이지만 색인되면 본문이 검색에 안 잡히므로 낱개 주소도 넣는다.
def load(path):
    try:
        return json.loads(io.open(path, encoding='utf-8').read())
    except Exception:
        return None

articles = []
tn = load('content/translation-notes.json')
if tn is not None:
    for n in (tn.get('notes') if isinstance(tn, dict) else tn) or []:
        if n.get('id'):
            articles.append(('/translation-notes?id=%s' % n['id'], '0.6'))

import glob, datetime
today = datetime.date.today().isoformat()
for p in sorted(glob.glob('content/daily/2*.json')):
    d = os.path.basename(p)[:-5]
    if re.match(r'^\d{4}-\d{2}-\d{2}$', d) and d <= today:   # 미래 예약분은 제외
        articles.append(('/daily?d=%s' % d, '0.5'))

th = load('content/themes.json')
if th is not None:
    for t in (th.get('themes') if isinstance(th, dict) else th) or []:
        if t.get('id'):
            articles.append(('/themes?theme=%s' % t['id'], '0.6'))

# 기존 sitemap에서 동적 URL(watch?l=N 등) 보존
preserved = []
if os.path.exists('sitemap.xml'):
    old = open('sitemap.xml', encoding='utf-8').read()
    for m in re.finditer(r'<loc>(https://biblynote\.com/watch\?[^<]+)</loc>', old):
        preserved.append(m.group(1))

lines = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for path, pr in PAGES + articles:
    loc = f'{BASE}{path}'.replace('&', '&amp;')
    lines.append(f'  <url><loc>{loc}</loc><lastmod>{STAMP}</lastmod><priority>{pr}</priority></url>')
for loc in preserved:
    lines.append(f'  <url><loc>{loc}</loc><lastmod>{STAMP}</lastmod><priority>0.7</priority></url>')
lines.append('</urlset>')

open('sitemap.xml', 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
total = len(PAGES) + len(articles) + len(preserved)
print(f'sitemap.xml: 정적 {len(PAGES)}개 + 개별 글 {len(articles)}개 + 강의(watch) {len(preserved)}개 = {total} URL (lastmod {STAMP})')
