# -*- coding: utf-8 -*-
"""i18n_merge_en.py — 영어판 일괄 번역 결과를 사이트 사전에 합친다 (2026-11-27 영어판 완성 작업)

입력(작업 폴더 W, 기본 = 첫 인자):
  W/keypages.json          {한국어 키: [페이지 이름 ...]}  ('_common' = 공통 스크립트)
  W/batches/ui_*.json      [{k, type, pages}]           W/out/ui_*.en.json      {k: en}
  W/batches/course_*.json  [{k, field}]                 W/out/course_*.en.json  {k: en}
출력:
  i18n/common.json         — 3개 이상 페이지 또는 공통 스크립트 글자 + 성경 66권 이름·장절 표기(영어)
  i18n/pages/<page>.json   — 그 페이지에만 있는 글자 (기존 파일이면 en 만 보태고 다른 언어는 그대로)
  i18n/course.json         — 강의 목록(제목·요약·과목명·태그·챕터)
  i18n.js                  — PAGES 배열 갱신
사용: python -X utf8 tools/i18n_merge_en.py <작업 폴더>
"""
import json, glob, os, re, sys
sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = sys.argv[1]
KO = re.compile('[가-힣]')

def load(p): return json.load(open(p, encoding='utf-8'))
def save(p, obj):
    s = json.dumps(obj, ensure_ascii=False, indent=1)
    open(p, 'w', encoding='utf-8', newline='').write(s.replace('\n', '\r\n'))   # 기존 사전과 같은 모양(indent 1·CRLF·끝 줄바꿈 없음)

keypages = load(f'{W}/keypages.json')
ui, course = {}, {}
for f in glob.glob(f'{W}/out/ui_*.en.json'): ui.update(load(f))
for f in glob.glob(f'{W}/out/course_*.en.json'): course.update(load(f))
# 한글 잔존 검사는 태그 밖 글자만(코드가 값을 비교하는 <input value="실물제본"> 같은 속성은 그대로 둬야 한다)
ok = lambda v: isinstance(v, str) and v.strip() and not KO.search(re.sub(r'<[^>]+>', '', v))
# 표기 통일(기존 사전 기준)
FIX = [('Korean KJV (Jeongbon Edition)', 'King James Bible — Jeongbon Translation'),
       ('King James Bible Jeongbon Edition', 'King James Bible — Jeongbon Translation'),
       ('The One Who Knows the Ending', 'Those Who Know the Ending'),
       ('See You in the Kingdom', 'See You in That Kingdom')]
def fix(v):
    if not isinstance(v, str): return v
    for a, b in FIX: v = v.replace(a, b)
    return v
ui = {k: fix(v) for k, v in ui.items()}
course = {k: fix(v) for k, v in course.items()}

# ── 공통 / 페이지 나누기 ──
common = load(f'{ROOT}/i18n/common.json')
pages = {}
n_common = n_page = 0
MEMO = open(f'{ROOT}/content/memorize.json', encoding='utf-8').read()
for k, en in ui.items():
    if not ok(en): continue
    pg = keypages.get(k, [])
    # 암송 화면의 구절 조각(한국어 본문 속 빈칸·강조)은 영어로 바꾸면 한·영이 섞인다 → 뺀다
    if pg == ['memorize'] and k in MEMO: continue
    if '_common' in pg or len(pg) >= 3:
        e = common.setdefault(k, {});
        if not e.get('en'): e['en'] = en; n_common += 1
    else:
        for p in pg:
            pages.setdefault(p, {})[k] = en; n_page += 1

# ── 성경 66권 이름·장절 표기 ──
books = load(f'{ROOT}/bible/books.json')
for b in books:
    ko, en = b['ko'], b['en']
    for kk, vv in [(ko, en), (ko + ' {n}장', en + ' {n}'), (ko + ' {n}:{n}', en + ' {n}:{n}'),
                   (ko + ' {n}:{n}-{n}', en + ' {n}:{n}-{n}'), (ko + ' {n}장 {n}절', en + ' {n}:{n}')]:
        e = common.setdefault(kk, {})
        if not e.get('en'): e['en'] = vv
save(f'{ROOT}/i18n/common.json', common)

# ── 페이지 사전 ──
for p, d in pages.items():
    fp = f'{ROOT}/i18n/pages/{p}.json'
    cur = load(fp) if os.path.exists(fp) else {'_about': f'{p} 페이지 화면 글자(영어판 2026-11-27). 용어 기준 i18n/GLOSSARY.md'}
    for k, en in d.items():
        e = cur.setdefault(k, {})
        if not e.get('en'): e['en'] = en
    save(fp, cur)

# ── 강의 목록 ──
cd = {'_about': '강의 목록(content/course.json) 제목·요약·과목명·태그·챕터 영어판(2026-11-27). 새 강의를 넣으면 여기에도 영어를 보탠다.'}
for k, en in course.items():
    if ok(en): cd[k] = {'en': en}
save(f'{ROOT}/i18n/course.json', cd)

# ── i18n.js PAGES ──
names = sorted(os.path.basename(f)[:-5] for f in glob.glob(f'{ROOT}/i18n/pages/*.json'))
js = open(f'{ROOT}/i18n.js', encoding='utf-8', newline='').read()
js = re.sub(r"var PAGES = \[[^\]]*\];", "var PAGES = [" + ', '.join("'" + n + "'" for n in names) + "];", js, count=1)
open(f'{ROOT}/i18n.js', 'w', encoding='utf-8', newline='').write(js)
print(f'common +{n_common} · page entries +{n_page} ({len(pages)} pages) · course {len(cd)-1} · PAGES {len(names)}')
