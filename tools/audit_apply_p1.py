# -*- coding: utf-8 -*-
"""audit_apply_p1.py — P1 집합적 단수 정비: 원문 KJV thou/ye에 맞춰 절별 정밀 수정.

입력: tools/_audit/p1_fixes.json  [{book,ch,v,old,new,note}]
절 '전문' 치환(unique 보장)으로 kr + en(ko필드) 동기. raw 치환으로 CRLF·포맷 보존.

사용: python tools/audit_apply_p1.py --dry-run  /  python tools/audit_apply_p1.py
"""
import json, os, sys, io, argparse, tempfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIBLE = os.path.join(ROOT, 'bible')
AUD = os.path.join(ROOT, 'tools', '_audit')

def raw_replace_atomic(path, old, new):
    with open(path, 'r', encoding='utf-8', newline='') as f:
        text = f.read()
    old_j = json.dumps(old, ensure_ascii=False)[1:-1]
    new_j = json.dumps(new, ensure_ascii=False)[1:-1]
    cnt = text.count(old_j)
    if cnt != 1:
        return cnt, False
    text = text.replace(old_j, new_j)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='') as f:
            f.write(text)
        os.replace(tmp, path)
    except Exception:
        try: os.remove(tmp)
        except OSError: pass
        raise
    return cnt, True

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    fixes = json.load(open(os.path.join(AUD, 'p1_fixes.json'), encoding='utf-8'))
    log, ok, skip, ensync = [], 0, 0, 0
    for fx in fixes:
        bf, ch, v = fx['book'], fx['ch'], fx['v']
        ref = f'{bf} {ch}:{v}'
        kr_path = os.path.join(BIBLE, 'kr', f'{bf}-{ch}.json')
        en_path = os.path.join(BIBLE, 'en', f'{bf}-{ch}.json')
        kr = json.load(open(kr_path, encoding='utf-8'))
        cur = kr[v - 1] if v - 1 < len(kr) else ''
        if cur != fx['old']:
            log.append((ref, 'SKIP', '현행 절이 old와 불일치(이미 수정?) '))
            skip += 1; continue
        en_has = False
        if os.path.exists(en_path):
            en_txt = open(en_path, encoding='utf-8', newline='').read()
            en_has = en_txt.count(json.dumps(fx['old'], ensure_ascii=False)[1:-1]) == 1
        if args.dry_run:
            log.append((ref, 'DRY', f"{fx['note']} | kr{'+en' if en_has else '(kr만)'}"))
            ok += 1; ensync += en_has
        else:
            c1, d1 = raw_replace_atomic(kr_path, fx['old'], fx['new'])
            if not d1:
                log.append((ref, 'SKIP', f'kr {c1}회')); skip += 1; continue
            e_d = False
            if en_has:
                _, e_d = raw_replace_atomic(en_path, fx['old'], fx['new'])
            log.append((ref, 'APPLY', f"kr{'+en' if e_d else '(kr만)'}"))
            ok += 1; ensync += e_d
    with open(os.path.join(AUD, 'apply_log.tsv'), 'a', encoding='utf-8') as f:
        for r in log:
            f.write('P1\t' + '\t'.join(r) + '\n')
    print(f"[{'DRY' if args.dry_run else '적용'}] {len(fixes)}건 → 처리 {ok} 스킵 {skip} (en동기 {ensync})")
    for r in log:
        print('  ', ' | '.join(r))
    if args.dry_run:
        print('\n--- 수정 전후 비교 ---')
        for fx in fixes:
            print(f"[{fx['book']} {fx['ch']}:{fx['v']}]")
            print('  전:', fx['old'][:96])
            print('  후:', fx['new'][:96])

if __name__ == '__main__':
    main()
