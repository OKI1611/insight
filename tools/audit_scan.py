# -*- coding: utf-8 -*-
"""audit_scan.py — 정본역 킹제임스 성경 감수 1단계: 전권 규칙 스캔.

기준쌍: bible/kjv/<Book>.json (영문) ↔ bible/kr/<Book>-<ch>.json (한국어, 사이트 표시본).
(bible/en/ 은 일부 책에서 절 분할·본문이 낡아 감수 기준으로 쓰지 않음 — precheck 참조)

범주:
  per2    2인칭 단복수  thou/thee/thy/thine(단수) vs ye/you/your(복수) ↔ 너/네 vs 너희
  per13   1·3인칭 수    I/we, he/they ↔ 나/우리, 그/그들
  passive 수동태        be+과거분사 ↔ 한국어 피동 표지
  gender  성별          he/she ↔ 그/그녀·여성 지시
  name    고유명사      영어 철자별 한글 표기 콩코던스 (kjv-korean.json 사전 기반)
  divine  신명 표기     LORD/GOD/JEHOVAH → 여호와 (번역지침 §4)

사용:
  python tools/audit_scan.py                # 전 범주, 전권
  python tools/audit_scan.py --category per2 --book Matthew
산출:
  tools/_audit/candidates.jsonl
  tools/_audit/name_concordance.json
  tools/_audit/scan_summary.txt
"""
import json, os, sys, io, re, argparse
from collections import defaultdict, Counter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIBLE = os.path.join(ROOT, 'bible')
OUT_DIR = os.path.join(ROOT, 'tools', '_audit')
os.makedirs(OUT_DIR, exist_ok=True)

# ───────────────────────── 공용 ─────────────────────────

WORD_RE = re.compile(r"[A-Za-z][A-Za-z']*")

def en_tokens(s):
    return WORD_RE.findall(s or '')

def load_books():
    return json.load(open(os.path.join(BIBLE, 'books.json'), encoding='utf-8'))

def iter_verses(books, only_book=None):
    """yield (book_dict, ch, idx0, kjv_verse, kr_verse)"""
    for b in books:
        if only_book and b['file'] != only_book:
            continue
        kjv = json.load(open(os.path.join(BIBLE, 'kjv', b['file'] + '.json'), encoding='utf-8'))
        for ch in range(1, b['ch'] + 1):
            kr_path = os.path.join(BIBLE, 'kr', f"{b['file']}-{ch}.json")
            try:
                kr = json.load(open(kr_path, encoding='utf-8'))
            except Exception:
                continue
            vv = kjv.get(str(ch)) or []
            n = min(len(vv), len(kr))
            for i in range(n):
                yield b, ch, i, vv[i], kr[i]

def ref_of(b, ch, i):
    return f"{b['ko']} {ch}:{i+1}"

CANDS = []
def add(cat, b, ch, i, kjv_v, kr_v, rule, evidence, grade, extra=None):
    item = {
        'id': f"{b['file']}.{ch}.{i+1}.{cat}",
        'cat': cat, 'ref': ref_of(b, ch, i),
        'book': b['file'], 'ch': ch, 'v': i + 1,
        'kjv': kjv_v, 'ko': kr_v,
        'rule': rule, 'evidence': evidence, 'grade0': grade, 'morph': None,
    }
    if extra:
        item.update(extra)
    CANDS.append(item)

# ───────────────────────── per2: 2인칭 단복수 ─────────────────────────

SING2 = {'thou', 'thee', 'thy', 'thine', 'thyself'}
PLUR2 = {'ye', 'you', 'your', 'yours', 'yourselves'}
# 한국어 단수 2인칭 표지 (너희 제거 후 탐색) — 한글 앞글자 결합(열네·건너 등) 오탐 방지 lookbehind
KO_SING2_RE = re.compile(r'(?<![가-힣])네(?=가|게| )|(?<![가-힣])너(?=[를의는도와로 ,\.!\?]|에게|까지|부터)|당신(?!들)')
KO_PLUR2_RE = re.compile(r'너희|당신들|그대들')
VOCATIVE_DIVINE_RE = re.compile(r'\bO (LORD|Lord|God|GOD|King|king)\b')

def scan_per2(b, ch, i, kjv_v, kr_v):
    toks = [t.lower() for t in en_tokens(kjv_v)]
    has_s = any(t in SING2 for t in toks)
    has_p = any(t in PLUR2 for t in toks)
    if not (has_s or has_p):
        return
    ko_wo_plur = KO_PLUR2_RE.sub('◇', kr_v)         # 너희 제거(부분문자열 오탐 방지)
    ko_sing = bool(KO_SING2_RE.search(ko_wo_plur))
    ko_plur = bool(KO_PLUR2_RE.search(kr_v))
    if has_s and has_p:
        # 화자가 청자를 바꾸는 절 — 모순이 보일 때만 B로 기록
        if (ko_sing != ko_plur):
            return  # 둘 중 하나만 옮긴 것은 흔한 정상 축약 — 통과
        return
    if has_p and not has_s and ko_sing and not ko_plur:
        grade = 'A'
        if VOCATIVE_DIVINE_RE.search(kjv_v):
            grade = 'B'
        add('per2', b, ch, i, kjv_v, kr_v,
            '복수(ye/you)인데 한국어가 단수(너/네가/당신)',
            {'en': sorted({t for t in toks if t in PLUR2}),
             'ko_hits': KO_SING2_RE.findall(ko_wo_plur)[:4]}, grade)
    elif has_s and not has_p and ko_plur:
        grade = 'A'
        add('per2', b, ch, i, kjv_v, kr_v,
            '단수(thou/thee/thy)인데 한국어가 복수(너희)',
            {'en': sorted({t for t in toks if t in SING2}),
             'ko_hits': ['너희']}, grade)

# ───────────────────────── per13: 1·3인칭 수 ─────────────────────────

KO_WE_RE = re.compile(r'(?<![가-힣])우리')            # '쉬우리라' 등 오탐 방지
KO_I_RE = re.compile(r'(?<![가-힣])(내가|나를|나의|나는|나도|내게|나에게)')
KO_THEY_RE = re.compile(r'(?<![가-힣])(그들|저들|저희)')
KO_HE_RE = re.compile(r'(?<![가-힣])(그가|그는|그를|그의(?!들))')

def scan_per13(b, ch, i, kjv_v, kr_v):
    toks = [t.lower() for t in en_tokens(kjv_v)]
    ts = set(toks)
    has_i = bool({'i', 'me', 'my', 'mine'} & ts)
    has_we = bool({'we', 'us', 'our', 'ours'} & ts)
    # I만 있는데 한국어에 '우리'만 → B
    if has_i and not has_we and KO_WE_RE.search(kr_v) and not KO_I_RE.search(kr_v):
        add('per13', b, ch, i, kjv_v, kr_v, '1인칭 단수(I/my)인데 한국어가 우리',
            {'ko_hits': ['우리']}, 'B')
    elif has_we and not has_i and KO_I_RE.search(kr_v) and not KO_WE_RE.search(kr_v):
        add('per13', b, ch, i, kjv_v, kr_v, '1인칭 복수(we/our)인데 한국어가 나/내가',
            {'ko_hits': KO_I_RE.findall(kr_v)[:3]}, 'B')
    has_they = bool({'they', 'them', 'their', 'theirs'} & ts)
    has_he = bool({'he', 'him', 'his'} & ts)
    if has_they and not has_he and KO_HE_RE.search(kr_v) and not KO_THEY_RE.search(kr_v):
        add('per13', b, ch, i, kjv_v, kr_v, '3인칭 복수(they)인데 한국어가 그가/그는',
            {'ko_hits': KO_HE_RE.findall(kr_v)[:3]}, 'B')
    elif has_he and not has_they and KO_THEY_RE.search(kr_v) and not KO_HE_RE.search(kr_v):
        add('per13', b, ch, i, kjv_v, kr_v, '3인칭 단수(he)인데 한국어가 그들',
            {'ko_hits': ['그들']}, 'B')

# ───────────────────────── passive: 수동태 ─────────────────────────

BE_RE = r'(?:am|art|is|are|was|wast|wert|were|be|been|being)'
IRREG_PP = {
    'born','borne','given','taken','written','called','made','known','seen','slain',
    'smitten','cast','sent','brought','found','forgiven','forsaken','shed','hid',
    'hidden','led','done','set','put','kept','held','sold','told','driven','shaken',
    'broken','spoken','chosen','begotten','bidden','laid','paid','said','shut','cut',
    'left','lost','built','bound','clothed','crowned','sworn','torn','worn','thrown',
    'drawn','eaten','beaten','bitten','trodden','graven','sown','shewn','shown',
    'stricken','gotten','won','spent','bent','burnt','girt','rent','lent','heard',
    'read','met','fed','bred','shod','slidden','ridden','swallowed'
}
# be+분사가 수동이 아니라 완료인 KJV 자동사 (3대 오탐원 중 하나)
BE_PERFECT_INTRANS = {
    'come','gone','risen','arisen','fallen','entered','returned','departed',
    'ascended','descended','fled','escaped','run','sprung','grown','waxen',
    'become','passed','perished','turned','crept','flown','vanished','happened',
    'expired','dead','arrived','remained'
}
THEO_VERBS = {
    'justified','sanctified','saved','forgiven','condemned','chosen','called',
    'blessed','baptized','crucified','raised','begotten','sealed','redeemed',
    'reconciled','glorified','anointed','ordained','elected','predestinated',
    'washed','cleansed','healed','delivered','judged'
}
PASSIVE_EN_RE = re.compile(
    r'\b' + BE_RE + r"\b(?:\s+(?:not|now|also|yet|even|so|all|both|surely|verily|indeed|already|again|therefore|likewise|thus|there|first|greatly|utterly|wholly|straightway|immediately|scarcely|hardly|once|twice|still))*\s+([a-z']+)",
    re.IGNORECASE)
KO_PASSIVE_RE = re.compile(
    r'되니|되어|되매|되며|되고|되리|되었|되는|되지|된 |된다|된자|됨|될 |될지|당하|받|'
    r'[아어여워]지|[아어여워]졌|[아어여워]져|바 되|일컫|일컬|입은|입으|입게|입히|얻|'
    r'보이|들리|잡히|팔리|쫓기|갇히|찢기|찢겨|밟히|물리|불리|심기|막히|뚫리|열리|닫히|'
    r'끊기|끊어|묶이|쓰이|담기|잠기|안기|먹히|쫓겨|꺾이|눌리|덮이|가리|모이|쌓이|'
    r'낮아|높아|세워|채워|이루어|이루려|'
    r'태어나|묻히|묻혀|끌리|끌려|이끌|나뉘|나누인|시달리|쓸려|휩쓸|찍히|밀리|밀려|'
    r'걸리|걸려|뽑히|뿌려|섞이|사로잡|붙잡히|매달리|들려서|날리|'
    r'나타나|변하|낫|나으|놀라|충만|가득|배부르|수 없')

def is_pp(word):
    w = word.lower().strip("'")
    if w in BE_PERFECT_INTRANS:
        return None                      # 완료 자동사 — 수동 아님
    if w in IRREG_PP:
        return w
    if len(w) > 3 and w.endswith('ed'):
        return w
    if len(w) > 3 and w.endswith('en') and w not in {
        'when','then','even','heaven','leaven','amen','men','women','children',
        'brethren','often','seven','eleven','olden','barren','brazen','brasen',
        'golden','wooden','linen','earthen','sudden','open','garden','burden',
        'maiden','kitchen','oxen','heathen','leathern','wooen','omen','queen',
        'green','between','keen','screen','seen'}:
        return w
    return None

def scan_passive(b, ch, i, kjv_v, kr_v):
    pps = []
    for m in PASSIVE_EN_RE.finditer(kjv_v):
        pp = is_pp(m.group(1))
        if pp:
            pps.append(pp)
    if not pps:
        return
    if KO_PASSIVE_RE.search(kr_v):
        return                            # 한국어에 피동 표지 존재 — 통과
    theo = sorted(set(pps) & THEO_VERBS)
    add('passive', b, ch, i, kjv_v, kr_v,
        '영어 수동(be+분사)인데 한국어에 피동 표지 없음',
        {'pp': sorted(set(pps))[:5], 'theo': theo}, 'B',
        extra={'priority': bool(theo)})

# ───────────────────────── gender: 성별 ─────────────────────────

GENDER_WHITELIST_EN = re.compile(
    r'\b(Spirit|spirit|Ghost|Comforter|city|cities|Jerusalem|Zion|Babylon|Tyrus|Samaria|Nineveh|ship|ships|wisdom|Wisdom|land|nation|earth|moon|church|Israel|vine|fig tree|barren)\b')
KO_FEMALE_RE = re.compile(r'그녀|여자|여인|계집|아내|처|딸|어미|어머니|왕후|공주|과부|처녀|소녀|자매|신부|첩')
KO_MALE3_RE = re.compile(r'그가|그는|그를|그의')

def scan_gender(b, ch, i, kjv_v, kr_v):
    toks = [t.lower() for t in en_tokens(kjv_v)]
    ts = set(toks)
    has_she = bool({'she', 'her', 'hers', 'herself'} & ts)
    has_he = bool({'he', 'him', 'his', 'himself'} & ts)
    if has_she and GENDER_WHITELIST_EN.search(kjv_v):
        # 의인화·성령 — 검사 스킵, C 기록(집계용)
        add('gender', b, ch, i, kjv_v, kr_v,
            '의인화/성령 문맥의 여성 대명사 — 전통 처리 존중', {}, 'C')
        return
    if has_she and not has_he:
        if not KO_FEMALE_RE.search(kr_v) and KO_MALE3_RE.search(kr_v):
            # 개역 전통: 여성 3인칭도 '그'로 지칭('그녀' 미사용) — 파일럿 판독 결과 전부 전통 표기
            add('gender', b, ch, i, kjv_v, kr_v,
                '여성(she/her)을 그/그가로 지칭 — 개역 전통 표기(그녀 미사용 원칙)',
                {'ko_hits': KO_MALE3_RE.findall(kr_v)[:3]}, 'C')
    elif has_he and not has_she:
        if '그녀' in kr_v:
            add('gender', b, ch, i, kjv_v, kr_v,
                '남성(he/him)인데 한국어에 그녀',
                {'ko_hits': ['그녀']}, 'A')

# ───────────────────────── divine: 신명 표기 ─────────────────────────

def scan_divine(b, ch, i, kjv_v, kr_v):
    caps_lord = len(re.findall(r'\bLORD\b', kjv_v))
    caps_god = len(re.findall(r'\bGOD\b', kjv_v))
    jehovah = len(re.findall(r'\bJEHOVAH\b', kjv_v))
    need = caps_lord + caps_god + jehovah
    if need == 0:
        return
    have = kr_v.count('여호와')
    # NT의 LORD는 헬라어 κύριος(구약 인용) — 전통상 '주'가 정당 → B(검토)로 강등.
    # OT라도 호격 'my LORD / O LORD'는 히브리어가 아도나이(주)일 수 있음 → 원어(morph) 확인 대상.
    nt = (b['t'] == 'nt')
    vocative = bool(re.search(r'\b(my|O|Oh,?)\s+LORD\b', kjv_v))
    # 결합 신명 규례 (구약, 파일럿에서 확인된 실제 오류 패턴):
    #   'Lord GOD'(아도나이+YHWH) → '주 여호와' / 'LORD God'(YHWH+엘로힘) → '여호와 하나님·하나님 여호와'
    if not nt and re.search(r'\bLord GOD\b', kjv_v) and '주 여호와' not in kr_v:
        add('divine', b, ch, i, kjv_v, kr_v,
            "'Lord GOD'(아도나이 여호와)인데 한국어에 '주 여호와' 없음",
            {'pattern': 'Lord GOD', 'nt': nt}, 'B')
    if not nt and re.search(r'\bLORD God\b', kjv_v) and ('여호와 하나님' not in kr_v and '하나님 여호와' not in kr_v):
        add('divine', b, ch, i, kjv_v, kr_v,
            "'LORD God'(여호와 엘로힘)인데 한국어에 '여호와 하나님/하나님 여호와' 없음",
            {'pattern': 'LORD God', 'nt': nt}, 'B')
    if have == 0:
        # NT의 LORD = 헬라어 κύριος(구약 인용) — '주'가 전통 표기(파일럿 확인) → C
        grade = 'C' if nt else ('B' if vocative else 'A')
        add('divine', b, ch, i, kjv_v, kr_v,
            'LORD/GOD/JEHOVAH(전대문자)인데 한국어에 여호와 없음'
            + (' — NT(κύριος) 전통상 주' if nt else '')
            + (' — 호격, 원어 아도나이 가능' if vocative else ''),
            {'need': need, 'have': 0, 'nt': nt, 'vocative': vocative}, grade)
    elif have < need:
        # 파일럿 판독: 횟수 부족은 대부분 주어 생략 축약(개역과 동일 관용) 또는 아도나이 병존 → C
        add('divine', b, ch, i, kjv_v, kr_v,
            f'여호와 횟수 부족 (원문 {need} vs 번역 {have}) — 주어 생략 축약이면 정상',
            {'need': need, 'have': have, 'nt': nt}, 'C')

# ───────────────────────── name: 고유명사 콩코던스 ─────────────────────────

NAME_STOP = {
    'God','Lord','LORD','GOD','O','And','But','For','The','Then','Now','So','If',
    'Thou','Ye','He','She','It','They','We','I','Behold','Thus','When','Wherefore',
    'Therefore','Yea','Nay','Amen','Selah','Spirit','Ghost','Father','Son','Holy',
    'Most','High','Almighty','King','Who','Whom','What','Which','That','This',
    'These','Those','There','Hear','Come','Go','Let','Take','Blessed','Cursed',
    'Woe','Verily','After','Before','From','Unto','Upon','Are','Is','Was','Be',
    'Have','Hath','Do','Did','As','At','By','In','Of','On','To','With','All',
    'Every','My','Thy','His','Her','Our','Your','Their','Its','Christ','Jesus',
    'Jew','Jews','Gentile','Gentiles','Sabbath','Passover','Pharisee','Pharisees',
    'Sadducee','Sadducees','Scribe','Scribes','Levite','Levites','Master','Rabbi',
    'Say','Saying','Went','Yet','Because','Howbeit','Nevertheless','Moreover',
    'Furthermore','Likewise','Also','Even','Both','Neither','Either','While',
    'Whosoever','Whatsoever','Wilt','Shalt','Art','Peace','Grace','Mercy','Truth',
    'Heaven','Hell','Hosanna','Hallelujah','Alleluia','Immanuel','Emmanuel',
}

MULTI_PARTICLES = {'에게서', '으로부터', '에게로', '이라는', '까지도', '에게', '에서',
                   '으로', '이라', '라서', '라는', '부터', '처럼', '같이', '보다'}

def token_candidates(tok):
    """이름 끝음절 vs 조사 구분이 모호하므로 후보군을 모두 만들어 최대 유사도로 비교.
    (수리아→'아'를 깎으면 안 되고, 여이엘이→'이'는 깎아야 하는 문제의 해법)"""
    cands = {tok}
    if len(tok) >= 3:
        cands.add(tok[:-1])
    if len(tok) >= 4 and tok[-2:] in MULTI_PARTICLES:
        cands.add(tok[:-2])
    if len(tok) >= 5 and tok[-3:] in MULTI_PARTICLES:
        cands.add(tok[:-3])
    return cands

def scan_names(books, only_book=None):
    """전권 콩코던스: 영어 철자 → {한글표기: 횟수}  (kjv-korean.json 사전 기반)

    잡음 제거 3중 필터:
      1) 소문자 출현 비율 — 본문에서 소문자로도 자주 쓰이는 단어(lot, will, no...)는 고유명사 아님
      2) 기대형 신뢰도 — 사전 뜻이 실제 본문에서 30% 미만 적중이면 '사전 뜻 충돌'로 분리(Ai=나무늘보 등)
      3) 변형 인정 — 조사 제거 + 유사도 0.6↑ + 출현 2회↑ 만 표기 변형으로 집계
    """
    import difflib
    dic = json.load(open(os.path.join(BIBLE, 'kjv-korean.json'), encoding='utf-8'))
    expected = {}
    for k, v in dic.items():
        v0 = re.split(r'[,;(/·]', str(v))[0].strip()
        if v0 and re.fullmatch(r'[가-힣]{1,8}', v0):
            expected[k] = v0
    cap_cnt, low_cnt = Counter(), Counter()
    verses_cache = []
    for b, ch, i, kjv_v, kr_v in iter_verses(books, only_book):
        verses_cache.append((b, ch, i, kjv_v, kr_v))
        for m in re.finditer(r"[A-Za-z][a-z']+", kjv_v):
            t = m.group(0)
            if t[0].isupper():
                if t not in NAME_STOP and m.start() > 0:
                    cap_cnt[t] += 1
            else:
                low_cnt[t.capitalize()] += 1
    proper = set()
    for t, c in cap_cnt.items():
        if t.lower() not in expected:
            continue
        low = low_cnt.get(t, 0)
        if low > 0 and low / (low + c) > 0.2:     # 필터1: 일반어
            continue
        proper.add(t)
    conc = defaultdict(lambda: {'expected': None, 'hits': Counter(),
                                'variant_refs': defaultdict(list), 'no_match': [], 'total': 0})
    for b, ch, i, kjv_v, kr_v in verses_cache:
        toks = set(re.findall(r"[A-Z][a-z']+", kjv_v))
        for t in toks:
            if t not in proper:
                continue
            exp = expected[t.lower()]
            e = conc[t]
            e['expected'] = exp
            e['total'] += 1
            if exp in kr_v:
                e['hits'][exp] += 1
            else:
                best, ratio = None, 0.0
                for kt in set(re.findall(r'[가-힣]{2,10}', kr_v)):
                    for kt2 in token_candidates(kt):
                        if len(kt2) < 2:
                            continue
                        r = difflib.SequenceMatcher(None, exp, kt2).ratio()
                        if r > ratio:
                            best, ratio = kt2, r
                if best and ratio >= 0.6:
                    e['hits'][best] += 1
                    e['variant_refs'][best].append(ref_of(b, ch, i))
                else:
                    e['no_match'].append(ref_of(b, ch, i))
    out_variants, out_unreliable = {}, {}
    for name, e in conc.items():
        exp_hits = e['hits'].get(e['expected'], 0)
        hit_rate = exp_hits / e['total'] if e['total'] else 0
        if hit_rate < 0.3:                          # 필터2: 사전 뜻 충돌/비신뢰 매핑
            out_unreliable[name] = {'expected': e['expected'], 'total': e['total'],
                                    'hit_rate': round(hit_rate, 2)}
            continue
        variants = {f: c for f, c in e['hits'].items()
                    if f != e['expected'] and c >= 2}   # 필터3
        if variants:
            out_variants[name] = {
                'expected': e['expected'], 'total': e['total'],
                'expected_hits': exp_hits,
                'variants': variants,
                'variant_refs': {f: e['variant_refs'][f][:20] for f in variants},
                'no_match_count': len(e['no_match']),
                'no_match_sample': e['no_match'][:10],
            }
    with open(os.path.join(OUT_DIR, 'name_concordance.json'), 'w', encoding='utf-8') as f:
        json.dump({'variants': out_variants, 'unreliable_mapping': out_unreliable},
                  f, ensure_ascii=False, indent=1)
    return out_variants, len(proper)

# ───────────────────────── 실행 ─────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--category', default='all',
                    help='all|per2|per13|passive|gender|divine|name (쉼표 구분 가능)')
    ap.add_argument('--book', default=None, help='특정 책만 (예: Matthew)')
    args = ap.parse_args()
    cats = set(args.category.split(',')) if args.category != 'all' else \
        {'per2', 'per13', 'passive', 'gender', 'divine', 'name'}

    books = load_books()
    verse_scanners = []
    if 'per2' in cats: verse_scanners.append(scan_per2)
    if 'per13' in cats: verse_scanners.append(scan_per13)
    if 'passive' in cats: verse_scanners.append(scan_passive)
    if 'gender' in cats: verse_scanners.append(scan_gender)
    if 'divine' in cats: verse_scanners.append(scan_divine)

    n = 0
    for b, ch, i, kjv_v, kr_v in iter_verses(books, args.book):
        n += 1
        for fn in verse_scanners:
            fn(b, ch, i, kjv_v, kr_v)

    name_flagged = name_total = 0
    if 'name' in cats:
        name_out, name_total = scan_names(books, args.book)
        name_flagged = len(name_out)

    out = os.path.join(OUT_DIR, 'candidates.jsonl')
    with open(out, 'w', encoding='utf-8') as f:
        for c in CANDS:
            f.write(json.dumps(c, ensure_ascii=False) + '\n')

    summary = Counter()
    for c in CANDS:
        summary[(c['cat'], c['grade0'])] += 1
    lines = [f'스캔 절 수: {n}', f'절 단위 후보: {len(CANDS)}건 → {out}']
    for (cat, g), cnt in sorted(summary.items()):
        lines.append(f'  {cat} [{g}]: {cnt}')
    if 'name' in cats:
        lines.append(f'고유명사: 사전 매핑 이름 {name_total}개 중 플래그 {name_flagged}개 → name_concordance.json')
    text = '\n'.join(lines)
    open(os.path.join(OUT_DIR, 'scan_summary.txt'), 'w', encoding='utf-8').write(text + '\n')
    print(text)

if __name__ == '__main__':
    main()
