# -*- coding: utf-8 -*-
"""review_fetch_lex.py — 정본역 전수 검토 0단계: STEPBible 원어 렉심·글로스 절별 캐시.

audit_fetch_morph.py(형태소 요약)와 같은 원천(TAHOT/TAGNT, CC BY 4.0)을 읽되,
절마다 **단어 단위 목록**을 남긴다 — KJV 핵심어와 원어를 맞춰 보고, 검토 에이전트에
'이 절의 원어는 무엇인가'를 넘겨 주기 위해서다.

산출: tools/_audit/lex/<Book>.json   (gitignore)
  {"11:32": [ {"s":"G4788","w":"συνέκλεισεν","l":"συγκλείω","g":"to confine","e":"Has bound up","m":"V-AAI-3S","tr":true}, … ]}
  s=스트롱  w=본문 단어  l=사전형  g=사전 뜻  e=문맥 영어 글로스  m=문법  tr=TR(KJV 기저본)에 있는 단어인가

절 번호 키는 **KJV 기준**: TAGNT는 'Rom.1.10[1.9]' 처럼 대괄호가 KJV 절 → 대괄호 절을 키로 쓴다.
TAHOT는 'Psa.3.0(3.1)' 처럼 괄호가 히브리 절 → 영어(앞) 절을 키로 쓴다. 0절(시편 표제)은 1절에 합친다.

사용: python tools/review_fetch_lex.py          (원천 파일은 tools/_audit/sources/ 에 있어야 함 — audit_fetch_morph.py 가 내려받음)
"""
import json, os, re, sys, io
from collections import defaultdict

# (stdout 래핑은 audit_fetch_morph import 시 1회만 — 이중 래핑 금지)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from audit_fetch_morph import STEP2FILE, FILES, SRC, word_in_tr   # noqa: E402

OUT = os.path.join(ROOT, 'tools', '_audit', 'lex')
os.makedirs(OUT, exist_ok=True)

REF_RE = re.compile(r'^([1-3]?[A-Za-z]{2,3})\.(\d+)\.(\d+)(?:\[(?:([1-3]?[A-Za-z]{2,3})\.)?(\d+)\.(\d+)\])?(?:\((?:([1-3]?[A-Za-z]{2,3})\.)?(\d+)\.(\d+)\))?')
LEMMA_RE = re.compile(r'([HG]\d{4}[A-Za-z]?)=([^=\s{}/]+)=([^{}»\t]*)')   # H1254A=בָּרָא=to create / G4788 (TAGNT 는 별도 컬럼)

def key_of(ref, is_greek):
    m = REF_RE.match(ref)
    if not m: return None
    ab, ch, v = m.group(1), int(m.group(2)), int(m.group(3))
    bf = STEP2FILE.get(ab)
    if not bf: return None
    if is_greek and m.group(5):                      # [KJV 절]
        bf = STEP2FILE.get(m.group(4) or ab, bf); ch = int(m.group(5)); v = int(m.group(6))
    if v == 0: v = 1                                  # 시편 표제 → 1절에 합침
    return (bf, ch, v)

def parse_greek(path):
    per = defaultdict(list)
    with open(path, encoding='utf-8', errors='replace') as f:
        for line in f:
            if '\t' not in line or not line[0].isalpha() and not line[0].isdigit(): continue
            cols = line.rstrip('\n').split('\t')
            k = key_of(cols[0].strip(), True)
            if not k or len(cols) < 5: continue
            word = cols[1].split('(')[0].strip()
            eng = cols[2].strip()
            sg = cols[3].strip()                       # G4788=V-AAI-3S
            strong, gram = (sg.split('=', 1) + [''])[:2]
            lemma, gloss = (cols[4].strip().split('=', 1) + [''])[:2]
            tr = word_in_tr(cols[5:6]) if len(cols) > 5 else True
            strong = re.sub(r'[A-Za-z]$', '', strong)  # G2424G → G2424 (접미 제거)
            if not re.match(r'^G\d{4}$', strong): continue
            per[k].append({'s': strong, 'w': word, 'l': lemma, 'g': gloss, 'e': eng, 'm': gram, 'tr': tr})
    return per

def parse_hebrew(path):
    per = defaultdict(list)
    with open(path, encoding='utf-8', errors='replace') as f:
        for line in f:
            if '\t' not in line: continue
            cols = line.rstrip('\n').split('\t')
            k = key_of(cols[0].strip(), False)
            if not k or len(cols) < 6: continue
            word = cols[1].strip()
            eng = cols[3].strip()
            gram = cols[5].strip()
            # 렉심=사전형=뜻 조각들 (접두 H9003=ב=in 처럼 기능어도 포함되나 검토엔 도움)
            lem_col = ''
            for c in cols[6:]:
                if '=' in c and re.search(r'[HG]\d{4}', c): lem_col = c; break
            found = LEMMA_RE.findall(lem_col)
            if not found:
                for s in re.findall(r'[HG]\d{4}', cols[4]):
                    per[k].append({'s': s, 'w': word, 'l': '', 'g': '', 'e': eng, 'm': gram, 'tr': True})
                continue
            for s, lem, gl in found:
                s = re.sub(r'[A-Za-z]$', '', s)
                per[k].append({'s': s, 'w': word, 'l': lem, 'g': gl.strip(), 'e': eng, 'm': gram, 'tr': True})
    return per

def main():
    books = defaultdict(dict)
    for fn in FILES:
        p = os.path.join(SRC, fn)
        if not os.path.exists(p): print('!! 없음:', fn[:40]); continue
        g = fn.startswith('TAGNT')
        print('  파싱:', fn[:38], '…', flush=True)
        per = parse_greek(p) if g else parse_hebrew(p)
        for (bf, ch, v), words in per.items():
            books[bf][f'{ch}:{v}'] = words
    n = 0
    for bf, d in books.items():
        n += len(d)
        json.dump(d, open(os.path.join(OUT, bf + '.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    print(f'렉심 캐시: {len(books)}권 {n:,}절 → tools/_audit/lex/')
    # 자가 점검 — 롬 11:32 / 창 1:1
    r = json.load(open(os.path.join(OUT, 'Romans.json'), encoding='utf-8'))
    print('롬 11:32:', ' | '.join(f"{w['s']} {w['l']}={w['g']}" for w in r['11:32'] if w['tr']))
    gn = json.load(open(os.path.join(OUT, 'Genesis.json'), encoding='utf-8'))
    print('창 1:1 :', ' | '.join(f"{w['s']} {w['l']}={w['g']}" for w in gn['1:1']))

if __name__ == '__main__':
    main()
