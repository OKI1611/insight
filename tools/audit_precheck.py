# -*- coding: utf-8 -*-
"""audit_precheck.py — KJV 새번역 감수 0단계: 3중 정합성 사전 점검.

bible/kjv/<Book>.json (영문 원본) · bible/en/<Book>-<ch>.json (ko 필드) ·
bible/kr/<Book>-<ch>.json (번역 사본) 세 데이터가 장·절 단위로 일치하는지 확인한다.
이 정합성이 이후 audit_apply.py 의 원자적 치환 가드의 전제가 된다.

사용: python tools/audit_precheck.py
산출: tools/_audit/precheck.tsv (불일치 목록), 콘솔 요약
"""
import json, os, sys, io, re

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIBLE = os.path.join(ROOT, 'bible')
OUT_DIR = os.path.join(ROOT, 'tools', '_audit')
os.makedirs(OUT_DIR, exist_ok=True)

def norm_ws(s):
    return re.sub(r'\s+', ' ', (s or '').strip())

def main():
    books = json.load(open(os.path.join(BIBLE, 'books.json'), encoding='utf-8'))
    issues = []          # (book, ch, kind, detail)
    n_ch = n_verse = 0
    for b in books:
        bf = b['file']
        kjv_path = os.path.join(BIBLE, 'kjv', bf + '.json')
        try:
            kjv = json.load(open(kjv_path, encoding='utf-8'))
        except Exception as e:
            issues.append((bf, 0, 'kjv-parse', str(e))); continue
        for ch in range(1, b['ch'] + 1):
            n_ch += 1
            en_path = os.path.join(BIBLE, 'en', f'{bf}-{ch}.json')
            kr_path = os.path.join(BIBLE, 'kr', f'{bf}-{ch}.json')
            kjv_vv = kjv.get(str(ch))
            if kjv_vv is None:
                issues.append((bf, ch, 'kjv-missing-ch', '')); continue
            try:
                en = json.load(open(en_path, encoding='utf-8'))
            except Exception as e:
                issues.append((bf, ch, 'en-parse', str(e))); continue
            try:
                kr = json.load(open(kr_path, encoding='utf-8'))
            except Exception as e:
                issues.append((bf, ch, 'kr-parse', str(e))); continue
            if not (len(kjv_vv) == len(en) == len(kr)):
                issues.append((bf, ch, 'len-mismatch',
                               f'kjv={len(kjv_vv)} en={len(en)} kr={len(kr)}'))
                continue
            n_verse += len(en)
            for i, item in enumerate(en):
                ko = item.get('ko', '')
                if ko != kr[i]:
                    issues.append((bf, ch, 'ko-vs-kr', f'v{i+1}'))
                if norm_ws(item.get('en', '')) != norm_ws(kjv_vv[i]):
                    issues.append((bf, ch, 'en-vs-kjv', f'v{i+1}'))

    out = os.path.join(OUT_DIR, 'precheck.tsv')
    with open(out, 'w', encoding='utf-8') as f:
        f.write('book\tchapter\tkind\tdetail\n')
        for r in issues:
            f.write('\t'.join(str(x) for x in r) + '\n')

    print(f'검사: {len(books)}권 {n_ch}장 {n_verse}절')
    print(f'불일치: {len(issues)}건 → {out}')
    if issues:
        from collections import Counter
        for kind, cnt in Counter(r[2] for r in issues).most_common():
            print(f'  - {kind}: {cnt}')
        sys.exit(1)
    print('정합성 OK — 3중 데이터 완전 일치')

if __name__ == '__main__':
    main()
