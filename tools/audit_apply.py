# -*- coding: utf-8 -*-
"""audit_apply.py — 감수 5단계: 승인 항목을 bible/kr(+en 동기) 에 적용.

가드:
  - kr[i] 안에 old 조각이 정확히 1회 존재해야 치환 (아니면 스킵+로그)
  - en[i].ko 가 치환 전 kr[i] 와 동일할 때만 en 도 함께 갱신 (en 낡은 절은 kr만)
  - 장 파일 쌍을 임시파일 → os.replace 로 원자적 기록, 원본 포맷(들여쓰기) 유지

사용: python tools/audit_apply.py --dry-run   /   python tools/audit_apply.py
산출: tools/_audit/apply_log.tsv
"""
import json, os, sys, io, argparse, tempfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIBLE = os.path.join(ROOT, 'bible')
AUD = os.path.join(ROOT, 'tools', '_audit')

# 승인 반영 목록 — 확정 오류 10건 (2026-07-24 사용자 승인)
# (id, book, ch, v, [(old, new), ...])
APPROVED = [
    ('Matthew.6.21.per2', 'Matthew', 6, 21,
     [('네 보물이 있는 그곳에 네 마음도', '너희 보물이 있는 그곳에 너희 마음도')]),
    ('1Timothy.6.21.per2', '1Timothy', 6, 21,
     [('은혜가 너희와 함께', '은혜가 너와 함께')]),
    ('3John.1.12.per2', '3John', 1, 12,
     [('너는 우리의 증언이 참된 줄을', '너희는 우리의 증언이 참된 줄을')]),
    ('2Samuel.17.21.per2', '2Samuel', 17, 21,
     [('아히도벨이 당신을 해하려', '아히도벨이 당신들을 해하려')]),
    ('Exodus.34.12.per2', 'Exodus', 34, 12,
     [('그것이 너희 가운데 올무가', '그것이 네 가운데 올무가')]),
    ('Isaiah.58.9.per2', 'Isaiah', 58, 9,
     [('네가 너희 가운데서 멍에와', '네가 네 가운데서 멍에와')]),
    ('Genesis.6.3.per13', 'Genesis', 6, 3,
     [('그들의 날은 백이십 년', '그의 날은 백이십 년')]),
    ('1Chronicles.29.1.divine', '1Chronicles', 29, 1,
     [('주 하나님을 위함이니라', '여호와 하나님을 위함이니라')]),
    ('Psalms.76.11.divine', 'Psalms', 76, 11,
     [('주 너희 하나님께 서원하고', '여호와 너희 하나님께 서원하고')]),
    ('Isaiah.49.22.divine', 'Isaiah', 49, 22,
     [('주 하나님께서 이같이 이르시되', '주 여호와께서 이같이 이르시되')]),
]

def raw_replace_atomic(path, old, new):
    """원본 바이트(줄바꿈·들여쓰기·끝개행)를 그대로 두고 대상 구절만 치환.
    old 가 파일 내 정확히 1회 나타날 때만 치환하고 (횟수, 성공여부) 반환."""
    with open(path, 'r', encoding='utf-8', newline='') as f:
        text = f.read()
    old_j = json.dumps(old, ensure_ascii=False)[1:-1]   # JSON 이스케이프 형태(따옴표 제외)
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

    log = []
    # 장별로 묶어 파일 IO 최소화
    by_ch = {}
    for cid, bf, ch, v, reps in APPROVED:
        by_ch.setdefault((bf, ch), []).append((cid, v, reps))

    applied = skipped = en_synced = en_stale = 0
    for (bf, ch), items in sorted(by_ch.items()):
        kr_path = os.path.join(BIBLE, 'kr', f'{bf}-{ch}.json')
        en_path = os.path.join(BIBLE, 'en', f'{bf}-{ch}.json')
        kr = json.load(open(kr_path, encoding='utf-8'))
        for cid, v, reps in items:
            i = v - 1
            if i >= len(kr):
                log.append((cid, 'SKIP', 'kr 절 범위 밖')); skipped += 1; continue
            old_verse = kr[i]
            new_verse = old_verse
            ok = True
            for old, new in reps:
                if new_verse.count(old) != 1:
                    log.append((cid, 'SKIP', f'조각 미일치({new_verse.count(old)}회): {old[:30]}'))
                    ok = False; break
                new_verse = new_verse.replace(old, new)
            if not ok:
                skipped += 1; continue
            # kr 은 절 전문이 파일 내 유일해야 안전 (raw 치환)
            if not args.dry_run:
                cnt, done = raw_replace_atomic(kr_path, old_verse, new_verse)
                if not done:
                    log.append((cid, 'SKIP', f'kr 원문 {cnt}회(≠1) — 미적용')); skipped += 1; continue
                # en 동기: en 파일에 같은 old 구절이 정확히 1회 있으면 함께(=최신), 없으면 kr만(낡음)
                encnt, endone = (0, False)
                if os.path.exists(en_path):
                    encnt, endone = raw_replace_atomic(en_path, old_verse, new_verse)
                log.append((cid, 'APPLY',
                            f'kr{"+en" if endone else "(en 낡음/불일치→kr만)"} | {old_verse[:40]} → {new_verse[:40]}'))
                applied += 1
                en_synced += 1 if endone else 0
                en_stale += 0 if endone else 1
            else:
                # dry-run: en 존재 여부만 사전 확인
                en_has = False
                if os.path.exists(en_path):
                    raw = open(en_path, 'r', encoding='utf-8', newline='').read()
                    en_has = raw.count(json.dumps(old_verse, ensure_ascii=False)[1:-1]) == 1
                log.append((cid, 'DRY',
                            f'kr{"+en" if en_has else "(en 낡음/불일치→kr만)"} | {old_verse[:40]} → {new_verse[:40]}'))
                applied += 1
                en_synced += 1 if en_has else 0
                en_stale += 0 if en_has else 1

    os.makedirs(AUD, exist_ok=True)
    with open(os.path.join(AUD, 'apply_log.tsv'), 'a', encoding='utf-8') as f:
        for r in log:
            f.write('\t'.join(r) + '\n')

    mode = 'DRY-RUN' if args.dry_run else '적용'
    print(f'[{mode}] 대상 {len(APPROVED)}건 → 처리 {applied} / 스킵 {skipped} (en 동기 {en_synced}, kr만 {en_stale})')
    for r in log:
        print('  ', ' | '.join(r))

if __name__ == '__main__':
    main()
