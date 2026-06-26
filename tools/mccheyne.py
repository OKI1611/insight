# -*- coding: utf-8 -*-
"""맥체인(McCheyne) 성경읽기표 — 날짜→본문 계산 (bible-plan.html의 streamDay 로직 재현).
구약1독·신약2독·시편2독을 365일에 균등 분배. 「매일 말씀과 함께」 본문 선정에 사용.
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DAYS = 365

def _load():
    books = json.load(open(os.path.join(ROOT, 'bible/books.json'), encoding='utf-8'))
    chap = {}
    for b in books:
        p = os.path.join(ROOT, f"bible/kjv/{b['file']}.json")
        try:
            chap[b['file']] = len(json.load(open(p, encoding='utf-8-sig')))
        except Exception:
            chap[b['file']] = b.get('ch', 0)
    return books, chap

def build_streams():
    books, chap = _load()
    ko = {b['file']: b['ko'] for b in books}
    OT_NOPS, NT_L, PS_L = [], [], []
    for b in books:
        f = b['file']
        for c in range(1, chap[f] + 1):
            entry = (f, ko[f], c)
            if f == 'Psalms':
                PS_L.append(entry)
            elif b['t'] == 'ot':
                OT_NOPS.append(entry)
            else:
                NT_L.append(entry)
    return OT_NOPS, NT_L, PS_L

def stream_day(lst, reps, day0):
    seq = len(lst) * reps
    a = (day0 * seq) // DAYS
    z = ((day0 + 1) * seq) // DAYS
    return [lst[i % len(lst)] for i in range(a, z)]

_OT, _NT, _PS = build_streams()

def mc_day(day0):
    """day0: 0-based day index (0..364). returns {ot,nt,ps} lists of (file,ko,ch)."""
    return {
        'ot': stream_day(_OT, 1, day0),
        'nt': stream_day(_NT, 2, day0),
        'ps': stream_day(_PS, 2, day0),
    }

def focus_passage(day0):
    """묵상 중심 본문: 신약 우선 → 시편 → 구약. (file, ko, ch) 반환."""
    r = mc_day(day0)
    if r['nt']:
        return r['nt'][0], r
    if r['ps']:
        return r['ps'][0], r
    if r['ot']:
        return r['ot'][0], r
    return None, r

def reading_label(parts):
    """[(file,ko,ch),...] → '요한복음 3장' 또는 '요한복음 3~4장'."""
    if not parts:
        return ''
    ko = parts[0][1]
    chs = [p[2] for p in parts]
    if len(chs) == 1:
        return f"{ko} {chs[0]}장"
    # 연속이면 범위, 아니면 콤마
    if chs == list(range(chs[0], chs[-1] + 1)) and parts[0][0] == parts[-1][0]:
        return f"{ko} {chs[0]}~{chs[-1]}장"
    return ' · '.join(f"{p[1]} {p[2]}장" for p in parts)

if __name__ == '__main__':
    import datetime, sys
    # 인자 없으면 오늘 기준 며칠치 미리보기
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    base = datetime.date(2026, 1, 1)
    today = datetime.date(2026, 6, 26)
    start_doy = (today - base).days  # 0-based day-of-year
    for i in range(n):
        d0 = (start_doy + i) % DAYS
        (f, ko, ch), r = focus_passage(d0)
        print(f"DOY{d0+1}: 묵상={ko} {ch}장 | 신약={reading_label(r['nt'])} · 시편={reading_label(r['ps'])} · 구약={reading_label(r['ot'])}")
