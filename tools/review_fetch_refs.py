# -*- coding: utf-8 -*-
"""review_fetch_refs.py — 정본역 전수 검토 0단계: 타 역본 본문을 로컬 분석용으로 수집.

⚠️ 저작권 본문이다. 산출물은 tools/_review/sources/ (gitignore) 에만 두고
   저장소·노문·검수표 본문·커밋 메시지 어디에도 인용하지 않는다. 유사도 계산 전용.

역본 (온라인 공개 리더에서 장 단위로 받음, 장당 0.4초 간격):
  krv   개역한글     keepbible.com  (흠정역 대조 화면에 함께 실림)
  hkjv  흠정역       keepbible.com
  nkrv  개역개정     bskorea.or.kr (대한성서공회)
  kkjv  한글킹제임스 biblemaster.co.kr (말씀보존학회)
  skjv  표준킹제임스 kingjamesbiblekorea.com

사용:  python tools/review_fetch_refs.py --src keepbible|bskorea|biblemaster|kjbk [--book Romans] [--force]
산출:  tools/_review/sources/<ver>.json   {"Romans-11-29": "…", …}   (중간 저장·재개 가능)
       tools/_review/sources/_fetch_log.txt
"""
import json, os, re, sys, io, time, argparse, urllib.request, html

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIBLE = os.path.join(ROOT, 'bible')
OUT = os.path.join(ROOT, 'tools', '_review', 'sources')
os.makedirs(OUT, exist_ok=True)
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36'
DELAY = 0.4

BOOKS = json.load(open(os.path.join(BIBLE, 'books.json'), encoding='utf-8'))   # [{file,en,ko,ch,t}]

# 대한성서공회 책 코드 — 확실치 않은 것은 후보를 여러 개 두고 절이 나오는 것을 쓴다
BSK = {
  'Genesis':['gen'],'Exodus':['exo'],'Leviticus':['lev'],'Numbers':['num'],'Deuteronomy':['deu'],
  'Joshua':['jos'],'Judges':['jdg'],'Ruth':['rut'],'1Samuel':['1sa'],'2Samuel':['2sa'],'1Kings':['1ki'],'2Kings':['2ki'],
  '1Chronicles':['1ch'],'2Chronicles':['2ch'],'Ezra':['ezr'],'Nehemiah':['neh'],'Esther':['est'],'Job':['job'],
  'Psalms':['psa'],'Proverbs':['pro'],'Ecclesiastes':['ecc'],'SongofSolomon':['sng','sol','sos'],'Isaiah':['isa'],
  'Jeremiah':['jer'],'Lamentations':['lam'],'Ezekiel':['ezk','eze'],'Daniel':['dan'],'Hosea':['hos'],'Joel':['jol','joe'],
  'Amos':['amo'],'Obadiah':['oba'],'Jonah':['jon','jnh'],'Micah':['mic'],'Nahum':['nah','nam'],'Habakkuk':['hab'],
  'Zephaniah':['zep'],'Haggai':['hag'],'Zechariah':['zec'],'Malachi':['mal'],
  'Matthew':['mat'],'Mark':['mrk','mar'],'Luke':['luk'],'John':['jhn','joh'],'Acts':['act'],'Romans':['rom'],
  '1Corinthians':['1co'],'2Corinthians':['2co'],'Galatians':['gal'],'Ephesians':['eph'],'Philippians':['php','phi'],
  'Colossians':['col'],'1Thessalonians':['1th'],'2Thessalonians':['2th'],'1Timothy':['1ti'],'2Timothy':['2ti'],
  'Titus':['tit'],'Philemon':['phm'],'Hebrews':['heb'],'James':['jas'],'1Peter':['1pe'],'2Peter':['2pe'],
  '1John':['1jn'],'2John':['2jn'],'3John':['3jn'],'Jude':['jud'],'Revelation':['rev'],
}
# 표준킹제임스 슬러그 (1-Samuel 형식)
def kjbk_slug(bf):
    m = re.match(r'^([123])(\w+)$', bf)
    if m: return f'{m.group(1)}-{m.group(2)}'
    if bf == 'SongofSolomon': return 'Song-of-Solomon'
    return bf

def get(url, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read().decode('utf-8', errors='replace')
        except Exception as e:
            time.sleep(1.5 * (i + 1))
    return ''

def clean(s):
    s = re.sub(r"<div id='D_[\s\S]*?</div>", '', s)        # 성서공회 각주 팝업
    s = re.sub(r'<[^>]+>', '', s)
    s = html.unescape(s).replace('\xa0', ' ')
    s = re.sub(r'\b\d{1,2}\)', '', s)                        # 각주 번호 "1)"
    s = re.sub(r'\s+', ' ', s).strip()
    return s

# ───────── 역본별 장 파서: (book, ch) → {ver: {v: text}} ─────────
def parse_keepbible(bf, bi, ch):
    h = get(f'https://keepbible.com/Bible/Book?book={bi}&r_bn=hkjv&r_bn2=hrv&cn={ch}')
    out = {'hkjv': {}, 'krv': {}}
    if not h: return out
    ol = re.search(r'<ol class="bible_txt">([\s\S]*?)</ol>', h)
    if not ol: return out
    for li in re.findall(r'<li>([\s\S]*?)</li>', ol.group(1)):
        ps = re.findall(r'<p>\s*<span class="num">(\d+)</span>([\s\S]*?)</p>', li)
        if not ps: continue
        v = int(ps[0][0])
        out['hkjv'][v] = clean(ps[0][1])
        if len(ps) > 1: out['krv'][v] = clean(ps[1][1])
    return out

def parse_bskorea(bf, bi, ch):
    out = {'nkrv': {}}
    for code in BSK.get(bf, []):
        h = get(f'https://www.bskorea.or.kr/bible/korbibReadpage.php?version=GAE&book={code}&chap={ch}')
        if not h: continue
        body = h.split('class="chapNum"')[-1]
        body = body.split('성경 단어 검색')[0]
        vs = re.findall(r'<span class="number">(\d+)&nbsp;[^<]*</span>([\s\S]*?)(?=<span class="number">|$)', body)
        if len(vs) >= 1:
            for v, t in vs:
                out['nkrv'][int(v)] = clean(t)
            BSK[bf] = [code]          # 성공한 코드로 고정
            return out
    return out

def parse_biblemaster(bf, bi, ch):
    out = {'kkjv': {}}
    h = get(f'https://www.biblemaster.co.kr/bible/kjv.php?mode=viewbible&book={bi}&start={ch}&mod=text')
    if not h: return out
    for v, t in re.findall(r'<p class="bible_cv">(\d+)</p>\s*<p class="bible_text[^"]*">([\s\S]*?)</p>', h):
        out['kkjv'][int(v)] = clean(t)
    return out

def parse_kjbk(bf, bi, ch):
    out = {'skjv': {}}
    h = get(f'https://kingjamesbiblekorea.com/e/{kjbk_slug(bf)}/{ch}')
    if not h: return out
    for v, t in re.findall(r'<p class="mb-2[^"]*"><span class="number mr-2">(\d+)</span>([\s\S]*?)</p>', h):
        if int(v) not in out['skjv']:          # 영문 <p class="en …">은 패턴이 달라 제외됨
            out['skjv'][int(v)] = clean(t)
    return out

PARSERS = {'keepbible': parse_keepbible, 'bskorea': parse_bskorea, 'biblemaster': parse_biblemaster, 'kjbk': parse_kjbk}

def load(ver):
    p = os.path.join(OUT, ver + '.json')
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else {}

def save(ver, d):
    p = os.path.join(OUT, ver + '.json'); tmp = p + '.tmp'
    json.dump(d, open(tmp, 'w', encoding='utf-8'), ensure_ascii=False)
    os.replace(tmp, p)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', required=True, choices=list(PARSERS))
    ap.add_argument('--book')
    ap.add_argument('--force', action='store_true')
    a = ap.parse_args()
    parser = PARSERS[a.src]
    data = {}
    log = open(os.path.join(OUT, '_fetch_log.txt'), 'a', encoding='utf-8')
    books = [b for b in BOOKS if not a.book or b['file'] == a.book]
    total_ch = sum(b['ch'] for b in books); done = 0; empty = []
    for bi, b in enumerate(BOOKS, start=1):
        if b not in books: continue
        bf = b['file']
        for ch in range(1, b['ch'] + 1):
            done += 1
            # 재개: 해당 장이 이미 있으면 건너뜀
            vers_needed = None
            res = None
            probe_key = f'{bf}-{ch}-1'
            need = False
            for ver in ([ 'hkjv','krv'] if a.src=='keepbible' else ['nkrv'] if a.src=='bskorea' else ['kkjv'] if a.src=='biblemaster' else ['skjv']):
                if ver not in data: data[ver] = load(ver)
                if a.force or probe_key not in data[ver]: need = True
            if not need: continue
            res = parser(bf, bi, ch)
            time.sleep(DELAY)
            for ver, vv in res.items():
                if not vv: empty.append(f'{ver}:{bf}-{ch}'); continue
                for v, t in vv.items():
                    data[ver][f'{bf}-{ch}-{v}'] = t
            if done % 25 == 0:
                for ver in data: save(ver, data[ver])
                print(f'[{a.src}] {done}/{total_ch}장 … {bf} {ch}', flush=True)
    for ver in data: save(ver, data[ver])
    for ver in data:
        msg = f'[{a.src}] {ver}: {len(data[ver]):,}절 저장'
        print(msg); log.write(msg + '\n')
    if empty:
        log.write(f'[{a.src}] 빈 장 {len(empty)}개: ' + ' '.join(empty[:200]) + '\n')
        print(f'  빈 장 {len(empty)}개 (로그 참조)')
    log.close()

if __name__ == '__main__':
    main()
