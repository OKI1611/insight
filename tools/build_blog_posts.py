# -*- coding: utf-8 -*-
"""네이버 블로그 글 생성기 — 요약노트를 블로그용 초고로 바꾼다.

사용법 (저장소 루트에서):
  python tools/build_blog_posts.py              → 최근 추가 강의 5편 생성
  python tools/build_blog_posts.py --n 10       → 최근 10편
  python tools/build_blog_posts.py --vid pksQMMzBEQ8   → 특정 강의 1편

출력: tools/blog_out/<날짜>_<유튜브ID>.txt  (복사해서 블로그에 붙여넣는 초고)
 - 글 구성: 제목 후보 3개 → 서론(문제 제기) → 핵심 3가지 → 마무리 + CTA 링크(utm 포함)
 - 노트 전문은 싣지 않는다 — '전체 정리는 사이트에서'로 유입을 만드는 것이 목적.
"""
import io, json, os, re, sys, argparse

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = 'https://www.biblynote.com'

def yt_id(u):
    u = str(u or '').strip()
    m = re.search(r'(?:v=|youtu\.be/|embed/|shorts/)([\w-]{11})', u)
    return m.group(1) if m else (u if re.fullmatch(r'[\w-]{11}', u) else '')

def load(p):
    with io.open(os.path.join(ROOT, p), encoding='utf-8') as f:
        return json.load(f)

def pick_lessons(course, n, vid=None):
    out = []
    for lv in course.get('levels', []):
        for l in lv.get('lessons', []):
            v = yt_id(l.get('youtube'))
            if not v: continue
            if vid and v != vid: continue
            out.append((lv.get('name', ''), l, v))
    if vid: return out[:1]
    out.sort(key=lambda x: str(x[1].get('added', '')), reverse=True)
    return out[:n]

def build_post(track, lesson, vid):
    note = None
    np = os.path.join(ROOT, 'content', 'notes', vid + '.json')
    if os.path.exists(np):
        note = load(os.path.join('content', 'notes', vid + '.json'))
    title = lesson.get('title', '')
    summary = str(lesson.get('summary', '')).strip()
    utm = 'utm_source=blog&utm_medium=naver&utm_content=' + vid
    watch = f'{SITE}/watch?v={vid}&src=blog'
    seminar = f'{SITE}/seminar.html?src=blog&{utm}'
    start = f'{SITE}/start.html?{utm}'

    # 제목 후보 — 본제목·질문형·궁금증형
    short = re.sub(r'^.*?·\s*', '', title).strip() or title
    titles = [
        short,
        short.rstrip('.?!') + ' — 성경은 뭐라고 답할까?',
        '[성경 바로 읽기] ' + short,
    ]

    # 핵심 3가지 — 노트의 thesis + 섹션 heading 에서 추림
    points = []
    if note:
        secs = note.get('sections') or []
        for s in secs:
            h = str(s.get('heading', '')).strip()
            if h: points.append(h)
        take = note.get('takeaways') or []
        if len(points) < 3:
            points += [str(t).strip() for t in take]
    points = [p for p in points if p][:3]
    intro = (note and str(note.get('overview', '')).strip()[:300]) or summary[:300]
    thesis = (note and str(note.get('thesis', '')).strip()) or ''

    L = []
    L.append('━' * 30)
    L.append('[제목 후보 — 하나 골라 쓰세요]')
    for i, t in enumerate(titles, 1): L.append(f'{i}. {t}')
    L.append('━' * 30)
    L.append('')
    L.append('(서론 — 문제 제기)')
    L.append(intro)
    L.append('')
    if thesis:
        L.append('(한 줄 결론)')
        L.append(thesis.split('.')[0] + '.')
        L.append('')
    if points:
        L.append('(본문 — 이 강의의 핵심 ' + str(len(points)) + '가지)')
        for i, p in enumerate(points, 1):
            L.append(f'{i}. {p}')
        L.append('')
        L.append('※ 각 항목 아래에 본인의 말로 2~3문장씩 살을 붙이면 완성됩니다.')
        L.append('   (전문을 그대로 옮기지 말고, 궁금증이 남게 요점만)')
        L.append('')
    L.append('(마무리 + 링크)')
    L.append('이 내용의 전체 강의(영상 + 요약노트 + 확인학습)는 바이블 인사이트에서 무료로 보실 수 있습니다.')
    L.append('')
    L.append('▶ 강의 바로 보기: ' + watch)
    L.append('▶ 50분 무료 특강(종말 예언 한눈에): ' + seminar)
    L.append('▶ 무료 PDF 자료 받기: ' + start)
    L.append('')
    L.append('#성경공부 #' + track.replace(' ', '').replace('·', '') + ' #바이블인사이트 #성경 #기독교')
    return '\n'.join(L)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--n', type=int, default=5)
    ap.add_argument('--vid', default=None)
    a = ap.parse_args()
    course = load('content/course.json')
    outdir = os.path.join(ROOT, 'tools', 'blog_out')
    os.makedirs(outdir, exist_ok=True)
    picked = pick_lessons(course, a.n, a.vid)
    if not picked:
        print('대상 강의가 없습니다'); return
    for track, lesson, vid in picked:
        added = str(lesson.get('added', '')) or 'nodate'
        path = os.path.join(outdir, f'{added}_{vid}.txt')
        with io.open(path, 'w', encoding='utf-8') as f:
            f.write(build_post(track, lesson, vid))
        print('생성:', os.path.relpath(path, ROOT), '—', lesson.get('title', '')[:50])

if __name__ == '__main__':
    main()
