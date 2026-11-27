# -*- coding: utf-8 -*-
"""휴거와 재림 Q&A 번역본 구조 검사 — ko.json 과 섹션·블록 종류·순서·id·구절·각주 위치가 같은지 본다.

사용: python tools/rapture_struct_check.py [en es ja zh]
"""
import json, re, sys, os
try: sys.stdout.reconfigure(encoding='utf-8')
except Exception: pass
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def sig(o, path='', out=None):
    """블록마다 (경로, 종류, id, ids, 구절, 각주 번호들) 서명을 만든다."""
    if out is None: out = []
    if isinstance(o, dict):
        kind = next((k for k in ('p', 'h3', 'note', 'v', 'ul', 'table', 'qa', 'q') if k in o), None)
        if kind:
            txt = json.dumps(o, ensure_ascii=False)
            fns = tuple(re.findall(r'\[\^(\d+)\]', txt)) if kind in ('p', 'note', 'ul', 'table', 'h3') else ()
            out.append((path, kind, o.get('id'), tuple(o.get('ids', [])), o.get('v') if kind == 'v' else None, fns))
        for k, v in o.items():
            if k in ('sections', 'body', 'qa', 'a'): sig(v, path + '/' + k, out)
    elif isinstance(o, list):
        for i, v in enumerate(o): sig(v, f'{path}[{i}]', out)
    return out

def main():
    ko = json.load(open(f'{ROOT}/tools/rapture/ko.json', encoding='utf-8'))
    base = sig(ko)
    langs = sys.argv[1:] or ['en', 'es', 'ja', 'zh']
    bad = 0
    for L in langs:
        p = f'{ROOT}/tools/rapture/{L}.json'
        if not os.path.exists(p): print(L, '— 파일 없음'); bad += 1; continue
        d = json.load(open(p, encoding='utf-8'))
        s = sig(d); probs = []
        if [x['id'] for x in d['sections']] != [x['id'] for x in ko['sections']]: probs.append('섹션 id/순서 다름')
        if len(d['notes']) != len(ko['notes']): probs.append(f"각주 수 {len(d['notes'])} ≠ {len(ko['notes'])}")
        if len(s) != len(base): probs.append(f'블록 수 {len(s)} ≠ {len(base)}')
        for a, b in zip(base, s):
            if a != b: probs.append(f'첫 차이: {a} ↔ {b}'); break
        if re.search('[가-힣]', json.dumps(d, ensure_ascii=False).replace(json.dumps(d.get('lang')), '')):
            ko_left = re.findall(r'[^"]{0,20}[가-힣]+[^"]{0,20}', json.dumps(d, ensure_ascii=False))
            probs.append(f'한글 남음 {len(ko_left)}곳: {ko_left[:2]}')
        print(L, '통과' if not probs else '문제:', *probs, sep='\n  ' if probs else ' ')
        bad += bool(probs)
    sys.exit(1 if bad else 0)

if __name__ == '__main__':
    main()
