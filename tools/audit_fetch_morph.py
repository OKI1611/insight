# -*- coding: utf-8 -*-
"""audit_fetch_morph.py — KJV 새번역 감수 2단계: STEPBible 원어 형태소 도입.

데이터: STEPBible-Data (CC BY 4.0, https://github.com/STEPBible/STEPBible-Data)
  - TAHOT (히브리어 구약, 형태소 태깅)  - TAGNT (헬라어 신약, TR 이문 포함)
원천 파일은 tools/_audit/sources/ 에만 저장(gitignore — 저장소에 커밋하지 않음).
보고서에 출처 표기 필수: "STEPBible.org TAHOT/TAGNT, CC BY 4.0".

절별 캐시 산출: tools/_audit/morph/<KJV책파일명>.json
  {"ch:v": {"stems": ["qal","niphal",...],      # 히브리어 동사 어간
             "voices": ["A","P","M",...],        # 헬라어 동사 태(A능동 M중간 P수동)
             "p2": ["s"|"p", ...],               # 2인칭 요소의 수(단/복)
             "lex": ["H3068", ...] }}            # 신명 관련 렉심(H3068 여호와 등)

사용: python tools/audit_fetch_morph.py            # 다운로드(캐시) + 파싱
      python tools/audit_fetch_morph.py --no-dl    # 파싱만
"""
import json, os, re, sys, io, argparse, urllib.request
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUD = os.path.join(ROOT, 'tools', '_audit')
SRC = os.path.join(AUD, 'sources')
MORPH = os.path.join(AUD, 'morph')
os.makedirs(SRC, exist_ok=True)
os.makedirs(MORPH, exist_ok=True)

BASE = ('https://raw.githubusercontent.com/STEPBible/STEPBible-Data/master/'
        'Translators%20Amalgamated%20OT%2BNT/')
FILES = [
    'TAHOT Gen-Deu - Translators Amalgamated Hebrew OT - STEPBible.org CC BY.txt',
    'TAHOT Jos-Est - Translators Amalgamated Hebrew OT - STEPBible.org CC BY.txt',
    'TAHOT Job-Sng - Translators Amalgamated Hebrew OT - STEPBible.org CC BY.txt',
    'TAHOT Isa-Mal - Translators Amalgamated Hebrew OT - STEPBible.org CC BY.txt',
    'TAGNT Mat-Jhn - Translators Amalgamated Greek NT - STEPBible.org CC-BY.txt',
    'TAGNT Act-Rev - Translators Amalgamated Greek NT - STEPBible.org CC-BY.txt',
]

# STEPBible 책 약어 → 저장소 bible/books.json file 명
STEP2FILE = {
    'Gen':'Genesis','Exo':'Exodus','Lev':'Leviticus','Num':'Numbers','Deu':'Deuteronomy',
    'Jos':'Joshua','Jdg':'Judges','Rut':'Ruth','1Sa':'1Samuel','2Sa':'2Samuel',
    '1Ki':'1Kings','2Ki':'2Kings','1Ch':'1Chronicles','2Ch':'2Chronicles',
    'Ezr':'Ezra','Neh':'Nehemiah','Est':'Esther','Job':'Job','Psa':'Psalms',
    'Pro':'Proverbs','Ecc':'Ecclesiastes','Sng':'SongofSolomon','Isa':'Isaiah',
    'Jer':'Jeremiah','Lam':'Lamentations','Ezk':'Ezekiel','Dan':'Daniel',
    'Hos':'Hosea','Jol':'Joel','Amo':'Amos','Oba':'Obadiah','Jon':'Jonah',
    'Mic':'Micah','Nam':'Nahum','Hab':'Habakkuk','Zep':'Zephaniah','Hag':'Haggai',
    'Zec':'Zechariah','Mal':'Malachi',
    'Mat':'Matthew','Mrk':'Mark','Luk':'Luke','Jhn':'John','Act':'Acts',
    'Rom':'Romans','1Co':'1Corinthians','2Co':'2Corinthians','Gal':'Galatians',
    'Eph':'Ephesians','Php':'Philippians','Col':'Colossians','1Th':'1Thessalonians',
    '2Th':'2Thessalonians','1Ti':'1Timothy','2Ti':'2Timothy','Tit':'Titus',
    'Phm':'Philemon','Heb':'Hebrews','Jas':'James','1Pe':'1Peter','2Pe':'2Peter',
    '1Jn':'1John','2Jn':'2John','3Jn':'3John','Jud':'Jude','Rev':'Revelation',
}

HEB_STEM = {'q':'qal','N':'niphal','p':'piel','P':'pual','h':'hiphil',
            'H':'hophal','t':'hithpael'}
DIVINE_LEX = {'H3068','H3069','H0136','H0430','H0410','H3050'}  # 여호와/아도나이/엘로힘/엘/야

def download():
    for fn in FILES:
        dst = os.path.join(SRC, fn)
        if os.path.exists(dst) and os.path.getsize(dst) > 1_000_000:
            print(f'  캐시 있음: {fn[:36]}...')
            continue
        url = BASE + urllib.request.quote(fn)
        print(f'  다운로드: {fn[:52]}...')
        urllib.request.urlretrieve(url, dst)
    print('다운로드 완료')

REF_RE = re.compile(r'^([1-3]?[A-Za-z]{2,3})\.(\d+)\.(\d+)')
PAREN_REF_RE = re.compile(r'\((?:([1-3]?[A-Za-z]{2,3})\.)?(\d+)\.(\d+)')

def parse_hebrew_grammar(g, out):
    """TAHOT 문법 예: HVqp3ms / HNcmsa / HPp2ms ...  (H=히브리어, A=아람어)"""
    # 동사 어간
    m = re.match(r'^[HA]V(.)', g)
    if m and m.group(1) in HEB_STEM:
        out['stems'].add(HEB_STEM[m.group(1)])
    # 2인칭 수: 문법 문자열 내 '2ms/2fs(단)' '2mp/2fp(복)'
    for m2 in re.finditer(r'2(m|f|c)?(s|p)', g):
        out['p2'].add('s' if m2.group(2) == 's' else 'p')

def parse_greek_grammar(g, out):
    """TAGNT 문법(Robinson) 예: V-API-3P(수동 직설) / V-APP-NSM(수동 분사) / P-2GS(2인칭 대명사).
    V- 뒤 [선택적 숫자]+시제+태+법: 태 = A능동 M중간 P수동 E중수동."""
    if g.startswith('V-'):
        core = re.sub(r'^\d', '', g[2:])
        if len(core) >= 2 and core[0] in 'PIFARLX' and core[1] in 'AMPED':
            out['voices'].add(core[1])
    # 2인칭 수: -2S/-2P(동사 어미), -2GS/-2DP(대명사 격+수)
    for m in re.finditer(r'-2[A-Z]{0,2}([SP])(?=$|-)', g):
        out['p2'].add('s' if m.group(1) == 'S' else 'p')

EDITION_NAMES = {'TR', 'Byz', 'NA28', 'NA27', 'SBL', 'WH', 'Treg', 'Tyn'}

def word_in_tr(cols):
    """TAGNT 판본 컬럼에서 이 단어가 TR(KJV 기저 본문)에 있는지 판정.
    예: 'NA28+NA27+Tyn+SBL+WH+Treg+TR+Byz' → True, 'NA28+SBL+WH' → False."""
    for c in cols:
        toks = {t.split('»')[0].strip() for t in c.strip().split('+')}
        if toks and toks & EDITION_NAMES:
            return 'TR' in toks
    return True   # 판본 컬럼이 없으면 보수적으로 포함

def parse_file(path, is_greek):
    per = defaultdict(lambda: {'stems': set(), 'voices': set(), 'p2': set(), 'lex': set()})
    with open(path, encoding='utf-8', errors='replace') as f:
        for line in f:
            if '\t' not in line:
                continue
            cols = line.rstrip('\n').split('\t')
            ref = cols[0].strip()
            m = REF_RE.match(ref)
            if not m:
                continue
            include_main = True
            tr_variant_grammars = []
            if is_greek:
                include_main = word_in_tr(cols[1:])
                # 이문 노트: 'ὑμῶν ... G5216=P-2GP in: TR+Byz' — TR 측 이문 문법 추출
                for vm in re.finditer(r'([HG]\d{4}[A-Za-z]?)=([A-Za-z0-9-]+)\s+in:\s*([A-Za-z0-9+»() ]*)',
                                      line):
                    eds = {t.split('»')[0].strip(' ()') for t in vm.group(3).split('+')}
                    if 'TR' in eds:
                        tr_variant_grammars.append((vm.group(1), vm.group(2)))
            ab, ch, v = m.group(1), int(m.group(2)), int(m.group(3))
            bf = STEP2FILE.get(ab)
            if not bf:
                continue
            keys = {(bf, ch, v)}
            pm = PAREN_REF_RE.search(ref)
            if pm:
                ab2 = STEP2FILE.get(pm.group(1) or ab, bf)
                keys.add((ab2, int(pm.group(2)), int(pm.group(3))))
            # 렉심(dStrongs)과 문법 컬럼 탐색 — 'G0907=V-APP-NSM' 처럼 결합된 형식 지원
            strongs = []
            grammar = None
            for c in cols[1:]:
                cs = c.strip()
                if '=' in cs:
                    left, right = cs.split('=', 1)
                    lm = re.fullmatch(r'[HG]\d{4}[A-Za-z]?(?:\+[HG]?\d{0,4}[A-Za-z]?)*', left)
                    if lm:
                        strongs.append(left)
                        if right and not grammar:
                            grammar = right
                        continue
                if re.fullmatch(r'[HG]\d{4}[A-Za-z]?(?:[+/\\][HG]?\d{0,4}[A-Za-z]?)*',
                                cs.replace('{', '').replace('}', '')):
                    strongs.append(cs)
                if not is_greek and re.match(r'^[HA][VNPCRDTIJXS]', cs):
                    grammar = cs
                if is_greek and re.match(r'^(V-|N-|P-|A-|D-|C-|T-|R[PDIQRX]?-|ADV|CONJ|PRT|PREP|INJ)', cs):
                    grammar = cs
            for key in keys:
                o = per[key]
                if include_main:
                    for s in strongs:
                        for m4 in re.finditer(r'[HG]\d{4}', s):
                            code = m4.group(0)
                            if code in DIVINE_LEX:
                                o['lex'].add(code)
                    if grammar:
                        if is_greek:
                            parse_greek_grammar(grammar, o)
                        else:
                            parse_hebrew_grammar(grammar, o)
                for v_strong, v_gram in tr_variant_grammars:
                    if v_strong in DIVINE_LEX:
                        o['lex'].add(v_strong)
                    parse_greek_grammar(v_gram, o)
    return per

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--no-dl', action='store_true')
    args = ap.parse_args()
    if not args.no_dl:
        download()
    books_data = defaultdict(dict)
    for fn in FILES:
        path = os.path.join(SRC, fn)
        if not os.path.exists(path):
            print(f'!! 없음: {fn}'); continue
        is_greek = fn.startswith('TAGNT')
        print(f'  파싱: {fn[:40]}...')
        per = parse_file(path, is_greek)
        for (bf, ch, v), o in per.items():
            books_data[bf][f'{ch}:{v}'] = {
                'stems': sorted(o['stems']), 'voices': sorted(o['voices']),
                'p2': sorted(o['p2']), 'lex': sorted(o['lex']),
            }
    n_verse = 0
    for bf, data in books_data.items():
        n_verse += len(data)
        with open(os.path.join(MORPH, bf + '.json'), 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
    print(f'캐시 완료: {len(books_data)}권 {n_verse}절 → tools/_audit/morph/')

if __name__ == '__main__':
    main()
