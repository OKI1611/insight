# -*- coding: utf-8 -*-
"""audit_apply2.py — 감수: 고유명사(Beelzebub·Baptist) + Lord GOD '주 하나님' 반영.

절 전문(raw) 치환으로 원본 CRLF·포맷 보존. kr + en(최신본) 동기.
사용: python tools/audit_apply2.py --dry-run  /  python tools/audit_apply2.py
"""
import json, os, sys, io, argparse, tempfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIBLE = os.path.join(ROOT, 'bible')
AUD = os.path.join(ROOT, 'tools', '_audit')

# 고유명사 부분치환: (book, ch, v, old_fragment, new_fragment)
NAME_FIXES = [
    # Beelzebub 바알세붑 → 바알세불 (신약 헬라 베엘제불, 마태·개역과 통일)
    ('Luke', 11, 15, '바알세붑', '바알세불'),
    ('Luke', 11, 18, '바알세붑', '바알세불'),
    ('Luke', 11, 19, '바알세붑', '바알세불'),
    # Baptist '침례 요한' → '침례자 요한' (다수 표기와 일관)
    ('Matthew', 16, 14, '침례 요한', '침례자 요한'),
    ('Matthew', 17, 13, '침례 요한', '침례자 요한'),
    ('Mark', 8, 28, '침례 요한', '침례자 요한'),
    ('Luke', 9, 19, '침례 요한', '침례자 요한'),
]

# Lord GOD '주 하나님' → '주 여호와' (아도나이+YHWH, 번역지침 §4). 이미 '주 만군의 여호와'인 절은 제외.
LORDGOD_FIXES = [
    ('Deuteronomy', 9, 26, '오 주 하나님이여', '오 주 여호와여'),
    ('Amos', 1, 8, '주 하나님께서', '주 여호와께서'),
    ('Amos', 3, 7, '주 하나님께서는', '주 여호와께서는'),
    ('Amos', 3, 8, '주 하나님께서', '주 여호와께서'),
    ('Amos', 3, 11, '주 하나님께서', '주 여호와께서'),
    ('Amos', 4, 2, '주 하나님께서', '주 여호와께서'),
    ('Amos', 4, 5, '주 하나님께서', '주 여호와께서'),
    ('Amos', 5, 3, '주 하나님께서', '주 여호와께서'),
]

ALL = [('name', *x) for x in NAME_FIXES] + [('lordgod', *x) for x in LORDGOD_FIXES]

def raw_replace_atomic(path, old, new):
    with open(path, 'r', encoding='utf-8', newline='') as f:
        text = f.read()
    old_j = json.dumps(old, ensure_ascii=False)[1:-1]
    new_j = json.dumps(new, ensure_ascii=False)[1:-1]
    cnt = text.count(old_j)
    if cnt != 1:
        return cnt, False
    text = text.replace(old_j, new_j)
    d = os.path.dirname(path)
    fd, tmp = tempfile.mkstemp(dir=d, suffix='.tmp')
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
    log, applied, skipped, ensync, enstale = [], 0, 0, 0, 0
    for cat, bf, ch, v, old, new in ALL:
        kr_path = os.path.join(BIBLE, 'kr', f'{bf}-{ch}.json')
        en_path = os.path.join(BIBLE, 'en', f'{bf}-{ch}.json')
        kr = json.load(open(kr_path, encoding='utf-8'))
        i = v - 1
        verse = kr[i] if i < len(kr) else ''
        if verse.count(old) != 1:
            log.append((cat, f'{bf} {ch}:{v}', 'SKIP', f'조각 {verse.count(old)}회≠1: {old}'))
            skipped += 1; continue
        old_v, new_v = verse, verse.replace(old, new)
        if args.dry_run:
            en_has = os.path.exists(en_path) and open(en_path, encoding='utf-8', newline='').read().count(
                json.dumps(old_v, ensure_ascii=False)[1:-1]) == 1
            log.append((cat, f'{bf} {ch}:{v}', 'DRY', f"{old}→{new} | kr{'+en' if en_has else '(kr만)'}"))
            applied += 1; ensync += en_has; enstale += (not en_has)
        else:
            c1, d1 = raw_replace_atomic(kr_path, old_v, new_v)
            if not d1:
                log.append((cat, f'{bf} {ch}:{v}', 'SKIP', f'kr {c1}회')); skipped += 1; continue
            e_c, e_d = (0, False)
            if os.path.exists(en_path):
                e_c, e_d = raw_replace_atomic(en_path, old_v, new_v)
            log.append((cat, f'{bf} {ch}:{v}', 'APPLY', f"{old}→{new} | kr{'+en' if e_d else '(kr만)'}"))
            applied += 1; ensync += e_d; enstale += (not e_d)
    os.makedirs(AUD, exist_ok=True)
    with open(os.path.join(AUD, 'apply_log.tsv'), 'a', encoding='utf-8') as f:
        for r in log:
            f.write('\t'.join(r) + '\n')
    print(f"[{'DRY' if args.dry_run else '적용'}] {len(ALL)}건 → 처리 {applied} 스킵 {skipped} (en동기 {ensync}, kr만 {enstale})")
    for r in log:
        print('  ', ' | '.join(r))

if __name__ == '__main__':
    main()
