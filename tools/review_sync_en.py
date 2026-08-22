# -*- coding: utf-8 -*-
"""review_sync_en.py — bible/en 의 ko(한국어 사본)를 정본 bible/kr 에 맞추고, 절 수가 어긋난 장을 재정렬한다.

배경: en.ko ≠ kr 인 절 3,298개 + 장 길이 불일치 62장(거의 구약·시편 표제장)이 있었다.
      bible.html 영어 패널과 EPUB 빌더가 en.ko 를 그대로 보여 주므로 이것은 이미 보이는 버그다.

동작
  (i)  장 길이가 같고 ko≠kr → kr 로 en.ko 덮어쓰기
  (ii) 장 길이가 다르면 → en[].en 을 kjv 절과 정규화 매칭(difflib)해 en 항목을 kjv 절 순서로 재배열.
       매칭 못 한 kjv 절은 {en: kjv절, ko: kr절} 최소 항목으로 채우고, 매칭 안 된 en 항목은 버린다(로그).
       한 장에서 매칭률이 70% 미만이면 손대지 않고 '수동' 목록에 남긴다.
  원자적 기록, 원본 스타일(review_apply.detect_style) 유지 — 라운드트립 불가 파일은 indent=1 로 쓴다.

사용: python tools/review_sync_en.py [--dry-run] [--book Psalms]
산출: tools/_review/sync_en_log.tsv
"""
import json, os, sys, io, re, argparse, difflib

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from review_apply import detect_style, serialize, atomic_write   # noqa: E402
BIBLE = os.path.join(ROOT, 'bible')
REV = os.path.join(ROOT, 'tools', '_review'); os.makedirs(REV, exist_ok=True)
BOOKS = json.load(open(os.path.join(BIBLE, 'books.json'), encoding='utf-8'))

def norm(s): return re.sub(r'[^a-z0-9]', '', (s or '').lower())

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--dry-run', action='store_true'); ap.add_argument('--book')
    a = ap.parse_args()
    log = open(os.path.join(REV, 'sync_en_log.tsv'), 'a', encoding='utf-8')
    n_ko = n_realign = n_manual = 0
    for b in BOOKS:
        if a.book and b['file'] != a.book: continue
        bf = b['file']
        kjv = json.load(open(os.path.join(BIBLE, 'kjv', bf + '.json'), encoding='utf-8'))
        for ch in range(1, b['ch'] + 1):
            krp = os.path.join(BIBLE, 'kr', f'{bf}-{ch}.json'); enp = os.path.join(BIBLE, 'en', f'{bf}-{ch}.json')
            if not (os.path.exists(krp) and os.path.exists(enp)): continue
            kr = json.load(open(krp, encoding='utf-8')); en_raw = open(enp, 'rb').read(); en = json.loads(en_raw.decode('utf-8'))
            kv = kjv.get(str(ch), [])
            changed = False
            if len(en) == len(kr):
                for i in range(len(kr)):
                    if isinstance(en[i], dict) and en[i].get('ko') != kr[i]:
                        en[i]['ko'] = kr[i]; changed = True; n_ko += 1
                        log.write(f'{bf}-{ch}-{i+1}\tko-sync\n')
            else:
                # 재정렬
                en_n = [norm(e.get('en', '')) if isinstance(e, dict) else '' for e in en]
                used = set(); new_en = []; matched = 0
                for i, kjv_v in enumerate(kv):
                    target = norm(kjv_v); best = None; best_r = 0
                    for j, s in enumerate(en_n):
                        if j in used or not s: continue
                        r = difflib.SequenceMatcher(None, target, s).ratio()
                        if r > best_r: best_r = r; best = j
                    if best is not None and best_r >= 0.85:
                        e = dict(en[best]); used.add(best); matched += 1
                    else:
                        e = {'en': kjv_v, 'ko': '', 'note': ''}
                    e['ko'] = kr[i] if i < len(kr) else e.get('ko', '')
                    new_en.append(e)
                rate = matched / max(1, len(kv))
                if rate < 0.7:
                    n_manual += 1; log.write(f'{bf}-{ch}\tMANUAL\tmatch {matched}/{len(kv)} en={len(en)} kr={len(kr)}\n'); continue
                en = new_en; changed = True; n_realign += 1
                log.write(f'{bf}-{ch}\tREALIGN\tmatch {matched}/{len(kv)} dropped {len(en_n) - len(used)}\n')
            if changed and not a.dry_run:
                st = detect_style(en_raw, json.loads(en_raw.decode('utf-8'))) or {'indent': 1, 'separators': (',', ': '), 'eol': '\r\n' if b'\r\n' in en_raw else '\n', 'trailing': en_raw.endswith(b'\n')}
                atomic_write(enp, serialize(en, st))
    log.close()
    print(('[DRY-RUN] ' if a.dry_run else '') + f'ko 동기 {n_ko}절 · 재정렬 {n_realign}장 · 수동 필요 {n_manual}장 → tools/_review/sync_en_log.tsv')

if __name__ == '__main__':
    main()
