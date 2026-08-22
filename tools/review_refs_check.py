# -*- coding: utf-8 -*-
"""review_refs_check.py — 적용된 변경 절의 '옛 본문'이 다른 자산에 인용돼 있는지 확인.

대상: bible/wordstudy.json · bible/footnotes.json · content/**/*.json · 루트 *.html · bible/번역지침.md
(kr·en·search-index 는 제외 — 그것들은 apply/재빌드로 갱신됨)

입력: tools/_review/apply_log.tsv 가 아니라 approved JSON(적용한 그 파일) — old 본문의 12자 이상 조각으로 검색.
사용: python tools/review_refs_check.py tools/_review/approved-Romans.json
"""
import json, os, sys, io, glob, re

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def targets():
    t = [os.path.join(ROOT, 'bible', 'wordstudy.json'), os.path.join(ROOT, 'bible', 'footnotes.json'), os.path.join(ROOT, 'bible', '번역지침.md')]
    t += glob.glob(os.path.join(ROOT, 'content', '**', '*.json'), recursive=True)
    t += glob.glob(os.path.join(ROOT, '*.html'))
    return [p for p in t if os.path.exists(p) and 'smart-index' not in p]

def main():
    if len(sys.argv) < 2: print('사용: review_refs_check.py approved.json'); sys.exit(1)
    items = json.load(open(sys.argv[1], encoding='utf-8'))
    files = [(p, open(p, encoding='utf-8', errors='replace').read()) for p in targets()]
    hits = 0
    for it in items:
        old = (it.get('old') or '').strip()
        if len(old) < 12: continue
        # 앞·뒤 따옴표/구두점 제거한 12~40자 조각 몇 개
        core = re.sub(r'^[\"“‘\'\s]+|[\"”’\'\s.,!?]+$', '', old)
        frags = {core[:24], core[-24:], core[len(core)//2 - 12: len(core)//2 + 12]}
        frags = {f for f in frags if len(f) >= 12}
        for p, txt in files:
            for f in frags:
                if f in txt:
                    hits += 1
                    print(f"{it['ref']}  ←  {os.path.relpath(p, ROOT)}   조각: {f}")
                    break
    print(f'완료: 인용 흔적 {hits}건' + (' — 위 파일의 문구를 새 본문에 맞게 손봐야 함' if hits else ''))

if __name__ == '__main__':
    main()
