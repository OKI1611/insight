# -*- coding: utf-8 -*-
"""노트가 실제 강의 자막과 얼마나 일치하는지 저비용 지표로 전수 채점.
지표 = 노트의 '특징 용어'(thesis+sections 본문의 빈출 2~5자 한글어) 중 자막에 등장하는 비율.
자막 기반으로 쓴 노트일수록 높고, 제목만으로 지어낸 노트일수록 낮게 나온다.
출력: tools/_align_scores.tsv (score\tvideoId\ttitle), 낮은 순 정렬 + 분포 요약.
"""
import os, sys, re, json, glob, collections
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

HANGUL = re.compile(r'[가-힣]{2,6}')
STOP = set('그리고 그러나 그래서 하지만 우리 그것 이것 저것 여기 거기 지금 오늘 사람 하나 정말 진짜 때문 통해 위해 대해 우리가 그런 어떤 모든 매우 아주 그의 그는 그런데 그리하여 이런 저런 것을 수는 있는 없는 하는 되는 이라는 라는 하고 에서 으로 처럼 만큼 까지 부터 께서 입니다 습니다 합니다 됩니다 이다 한다 된다 같은 같이 위한'.split())

def note_terms(note):
    parts = [str(note.get('thesis', '')), str(note.get('overview', ''))]
    for sec in (note.get('sections') or []):
        parts.append(str(sec.get('heading', '')))
        parts.append(str(sec.get('body', '')))
        for p in (sec.get('points') or []):
            parts.append(str(p))
    text = ' '.join(parts)
    words = [w for w in HANGUL.findall(text) if w not in STOP]
    freq = collections.Counter(words)
    # 특징 용어: 2회 이상 등장하거나 4자 이상(고유 개념어)인 상위 어휘
    terms = [w for w, c in freq.most_common(60) if (c >= 2 or len(w) >= 4)]
    return terms[:40]

def score(note, transcript):
    terms = note_terms(note)
    if not terms:
        return None, 0
    hit = sum(1 for t in terms if t in transcript)
    return round(hit / len(terms), 3), len(terms)

def main():
    rows = []
    tfiles = glob.glob('content/transcripts/*.txt')
    for tf in tfiles:
        vid = os.path.basename(tf)[:-4]
        nf = 'content/notes/%s.json' % vid
        if not os.path.exists(nf):
            continue
        try:
            note = json.load(open(nf, encoding='utf-8'))
            tr = open(tf, encoding='utf-8').read()
        except Exception:
            continue
        title = tr.split('\n', 1)[0].lstrip('# ').strip()[:50]
        sc, n = score(note, tr)
        if sc is None:
            continue
        rows.append((sc, vid, title))
    rows.sort()
    with open('tools/_align_scores.tsv', 'w', encoding='utf-8') as f:
        for sc, vid, title in rows:
            f.write('%.3f\t%s\t%s\n' % (sc, vid, title))
    # 분포
    import statistics
    scs = [r[0] for r in rows]
    print('대상 노트쌍:', len(rows))
    if scs:
        print('정합 지표 — 중앙값 %.3f · 평균 %.3f · 최소 %.3f' % (statistics.median(scs), statistics.mean(scs), min(scs)))
        for thr in (0.3, 0.4, 0.5, 0.6):
            print('  < %.1f : %d개' % (thr, sum(1 for x in scs if x < thr)))
    print('--- 가장 낮은 15개(의심) ---')
    for sc, vid, title in rows[:15]:
        print('%.3f  %s  %s' % (sc, vid, title))

if __name__ == '__main__':
    main()
