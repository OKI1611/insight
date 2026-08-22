# -*- coding: utf-8 -*-
"""review_apply.py — 정본역 전수 검토: 승인된 수정안을 bible/kr + bible/en 에 적용.

원칙
  - 파일 재직렬화로 포맷이 흔들리는 것을 막기 위해 **원문 바이트 안에서 JSON 인코딩된 절 문자열만 바꾼다**
    (kr: 해당 절 문자열이 파일 안에 정확히 1회일 때. en: "ko": "<절>" 형태가 정확히 1회일 때).
    1회가 아니면 인덱스 기반(파싱→교체→원본 스타일로 재직렬화, 라운드트립이 바이트 동일로 증명된 파일만) 으로 적용,
    그것도 안 되면 SKIP 하고 로그에 남긴다.
  - en.ko 가 kr 과 달랐던(낡은) 절도 새 kr 로 덮어쓴다(로그 'en-stale-overwritten'). 장 길이가 다르면 en 은 SKIP.
  - 적용 전 현행 kr 절이 승인 시점 본문(approved.json 의 old)과 같은지 확인한다(달라졌으면 SKIP).
  - 임시파일 → os.replace 로 원자적 기록. 모든 결과를 tools/_review/apply_log.tsv 에 남긴다.

입력 approved.json (list):
  {"ref":"Romans-11-29","old":"<현행 절 전문>","new":"<수정 절 전문>",
   "en":{"note":"<새 note 전문(선택)>","voc":[["old","new"],…],"idi":[["old","new"],…]}}

사용
  python tools/review_apply.py --selftest                 # 1,189×2 파일 라운드트립 검사(변경 없음)
  python tools/review_apply.py --approved tools/_review/approved-Romans.json --dry-run
  python tools/review_apply.py --approved tools/_review/approved-Romans.json
  python tools/review_apply.py --mechanical tools/_review/mechanical-Romans.json [--dry-run]   # 같은 형식
"""
import json, os, sys, io, argparse, tempfile, re, hashlib

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIBLE = os.path.join(ROOT, 'bible')
REV = os.path.join(ROOT, 'tools', '_review')
os.makedirs(REV, exist_ok=True)
LOG = os.path.join(REV, 'apply_log.tsv')
BOOKS = json.load(open(os.path.join(BIBLE, 'books.json'), encoding='utf-8'))

def read_bytes(p):
    return open(p, 'rb').read()

def jstr(s):
    """JSON 문자열 리터럴 본문(따옴표 제외). ensure_ascii=False 기준."""
    return json.dumps(s, ensure_ascii=False)[1:-1]

# ── 스타일 감지·재직렬화 (라운드트립 검증용) ──
def detect_style(raw, obj):
    text = raw.decode('utf-8')
    eol = '\r\n' if '\r\n' in text else '\n'
    trailing = text.endswith('\n')
    cands = [
        dict(indent=None, separators=(',', ':')),
        dict(indent=None, separators=(', ', ': ')),
        dict(indent=1, separators=(',', ': ')),
        dict(indent=2, separators=(',', ': ')),
        dict(indent=4, separators=(',', ': ')),
    ]
    for c in cands:
        s = json.dumps(obj, ensure_ascii=False, **c)
        if eol != '\n': s = s.replace('\n', eol)
        if trailing: s += eol
        if s.encode('utf-8') == raw:
            return {'eol': eol, 'trailing': trailing, **c}
    return None

def serialize(obj, st):
    s = json.dumps(obj, ensure_ascii=False, indent=st['indent'], separators=st['separators'])
    if st['eol'] != '\n': s = s.replace('\n', st['eol'])
    if st['trailing']: s += st['eol']
    return s.encode('utf-8')

def atomic_write(p, data):
    d = os.path.dirname(p)
    fd, tmp = tempfile.mkstemp(dir=d, prefix='.tmp-', suffix='.json')
    with os.fdopen(fd, 'wb') as f: f.write(data)
    os.replace(tmp, p)

def selftest():
    bad = []; n = 0; styles = {}
    for b in BOOKS:
        for ch in range(1, b['ch'] + 1):
            for kind in ('kr', 'en'):
                p = os.path.join(BIBLE, kind, f"{b['file']}-{ch}.json")
                if not os.path.exists(p): bad.append((p, 'missing')); continue
                raw = read_bytes(p)
                try: obj = json.loads(raw.decode('utf-8'))
                except Exception as e: bad.append((p, 'parse ' + str(e)[:40])); continue
                st = detect_style(raw, obj); n += 1
                if not st: bad.append((p, 'no-roundtrip'))
                else: styles[(kind, st['indent'], st['separators'], st['eol'], st['trailing'])] = styles.get((kind, st['indent'], st['separators'], st['eol'], st['trailing']), 0) + 1
    print(f'라운드트립 검사: {n}개 파일 중 바이트 동일 재직렬화 가능 {n - len(bad)}개, 불가 {len(bad)}개')
    for k, v in sorted(styles.items(), key=lambda x: -x[1])[:8]: print('  스타일', k, v)
    if bad:
        print('  불가 예:', bad[:5])
    return len(bad) == 0

# ── 적용 ──
def apply_items(items, dry):
    log = open(LOG, 'a', encoding='utf-8')
    res = {'applied': 0, 'skipped': 0, 'en_updated': 0, 'en_stale': 0, 'en_skipped': 0}
    # 파일별로 묶어서 한 번에 쓴다
    by_file = {}
    for it in items:
        m = re.match(r'^([A-Za-z0-9]+)-(\d+)-(\d+)$', it['ref'])
        if not m: log.write(f"{it.get('ref')}\tSKIP\tbad-ref\n"); res['skipped'] += 1; continue
        by_file.setdefault((m.group(1), int(m.group(2))), []).append((int(m.group(3)), it))
    for (bf, ch), lst in sorted(by_file.items()):
        krp = os.path.join(BIBLE, 'kr', f'{bf}-{ch}.json'); enp = os.path.join(BIBLE, 'en', f'{bf}-{ch}.json')
        kr_raw = read_bytes(krp); kr = json.loads(kr_raw.decode('utf-8'))
        en_raw = read_bytes(enp) if os.path.exists(enp) else None
        en = json.loads(en_raw.decode('utf-8')) if en_raw else None
        kr_text = kr_raw.decode('utf-8'); en_text = en_raw.decode('utf-8') if en_raw else None
        kr_changed = en_changed = False
        en_need_reserialize = False
        for v, it in sorted(lst):
            ref = it['ref']; i = v - 1
            if i >= len(kr): log.write(f'{ref}\tSKIP\tno-such-verse\n'); res['skipped'] += 1; continue
            cur = kr[i]; old = it.get('old'); new = it.get('new')
            if not new or new == cur: log.write(f'{ref}\tSKIP\tno-change\n'); res['skipped'] += 1; continue
            if old is not None and cur != old:
                log.write(f'{ref}\tSKIP\tkr-changed-since-approval\n'); res['skipped'] += 1; continue
            # kr: 원문 바이트 치환(정확히 1회) → 아니면 인덱스 교체
            tok = '"' + jstr(cur) + '"'
            if kr_text.count(tok) == 1:
                kr_text = kr_text.replace(tok, '"' + jstr(new) + '"')
            else:
                kr_text = None   # 재직렬화 경로로
            kr[i] = new; kr_changed = True
            log.write(f'{ref}\tAPPLY\tkr\t{len(cur)}->{len(new)}\n'); res['applied'] += 1
            # en
            if en is None: log.write(f'{ref}\tEN-SKIP\tno-en-file\n'); res['en_skipped'] += 1; continue
            if len(en) != len(kr): log.write(f'{ref}\tEN-SKIP\tlen-mismatch {len(en)} vs {len(kr)}\n'); res['en_skipped'] += 1; continue
            e = en[i]
            if isinstance(e, dict):
                if e.get('ko') != cur:
                    log.write(f'{ref}\tEN-STALE\toverwritten\n'); res['en_stale'] += 1
                e['ko'] = new
                eu = it.get('en') or {}
                if eu.get('note'): e['note'] = eu['note']
                for key in ('voc', 'idi', 'gra'):
                    for pair in eu.get(key, []) or []:
                        if not isinstance(pair, list) or len(pair) != 2: continue
                        o, nw = pair
                        for ent in e.get(key, []) or []:
                            for k2 in range(len(ent)):
                                if isinstance(ent[k2], str) and ent[k2] == o: ent[k2] = nw
                en_changed = True; en_need_reserialize = True; res['en_updated'] += 1
        if dry: continue
        if kr_changed:
            if kr_text is not None:
                atomic_write(krp, kr_text.encode('utf-8'))
            else:
                st = detect_style(kr_raw, json.loads(kr_raw.decode('utf-8')))
                if not st: log.write(f'{bf}-{ch}\tFILE-SKIP\tkr no-roundtrip and duplicate verse text\n'); continue
                atomic_write(krp, serialize(kr, st))
        if en_changed:
            st = detect_style(en_raw, json.loads(en_raw.decode('utf-8')))
            if st: atomic_write(enp, serialize(en, st))
            else:
                # 라운드트립 불가 → "ko": 값만 원문 치환(1회 보장될 때)
                ok = True; txt = en_text
                for v, it in sorted(lst):
                    i = v - 1
                    if i >= len(en) or not it.get('new'): continue
                    # 원래 ko(파일 기준) 찾기
                    orig = json.loads(en_raw.decode('utf-8'))[i].get('ko')
                    tk = '"ko": "' + jstr(orig) + '"'; tk2 = '"ko":"' + jstr(orig) + '"'
                    if txt.count(tk) == 1: txt = txt.replace(tk, '"ko": "' + jstr(it['new']) + '"')
                    elif txt.count(tk2) == 1: txt = txt.replace(tk2, '"ko":"' + jstr(it['new']) + '"')
                    else: ok = False
                if ok: atomic_write(enp, txt.encode('utf-8'))
                else: log.write(f'{bf}-{ch}\tEN-FILE-SKIP\tno-roundtrip and ko not unique\n')
    log.close()
    return res

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--selftest', action='store_true')
    ap.add_argument('--approved'); ap.add_argument('--mechanical')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()
    if a.selftest:
        ok = selftest(); sys.exit(0 if ok else 1)
    src = a.approved or a.mechanical
    if not src: ap.error('--selftest | --approved FILE | --mechanical FILE')
    items = json.load(open(src, encoding='utf-8'))
    res = apply_items(items, a.dry_run)
    print(('[DRY-RUN] ' if a.dry_run else '') + f"적용 {res['applied']} · 건너뜀 {res['skipped']} · en 갱신 {res['en_updated']}(낡은 절 덮어씀 {res['en_stale']}, en 건너뜀 {res['en_skipped']}) → {LOG}")

if __name__ == '__main__':
    main()
