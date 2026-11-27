"""팟캐스트 트랙 B 「하루 5분, 성경이 답합니다」 — 대본 생성·검수표·조립 도구

목소리(2026-11-27 확정): 진행 Desmond(남) · 낭독 Lucy(여) — Higgsfield text2speech_v2 / elevenlabs.
Higgsfield 는 Claude 대화창(MCP)에서만 부를 수 있어서, 음성 생성 단계만 대화창에서 한다.

주간 흐름 (작업 폴더 W = 이 PC 바탕화면\\팟캐스트_출퇴근성경공부\\트랙B_하루5분, PODCAST_B_DIR 로 변경 가능)
  0) doctor   python tools/podcast_daily.py doctor                     → 새 PC 준비 상태 점검
  1) plan     python tools/podcast_daily.py plan  --count 5            → W\\<주차>\\batch.json (소재 5개 선정)
  2) write    python tools/podcast_daily.py write  <주차>              → 대본 생성(Claude MAX, API 키 없음) + 성경 본문 자동 삽입
                                                                          + W\\<주차>\\검수표_<주차>.docx
  3) (저자)   검수표에서 문장을 고치고, 편마다 「승인: [ O ]」 표시
  4) collect  python tools/podcast_daily.py collect <주차>             → 승인분만 W\\<주차>\\voice_jobs.json
  5) (대화창) "이번 주 팟캐스트 음성 만들어줘" → Claude 가 voice_jobs.json 대로 Higgsfield 생성 후
              W\\<주차>\\urls.json 작성 → python tools/podcast_daily.py fetch <주차>
  6) assemble python tools/podcast_daily.py assemble <주차>            → W\\출력\\B001_제목.mp3 + 쇼노트, 사용 기록 갱신

시험: 환경 변수 PODCAST_MOCK_AI=1 이면 AI 없이 사이트 답변으로 대본을 만든다(흐름 점검용).
"""
import argparse, datetime, glob, json, os, re, shutil, subprocess, sys, tempfile, time, urllib.parse, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(HERE))
from ko_numread import for_tts                                   # 장·절 숫자 → 한자어 읽기
from build_nanje import ABBR, KO                                  # 성경 약칭·한글 책 이름

def _desktop():
    """이 PC의 바탕화면(OneDrive 바탕화면이면 그쪽) — 다른 PC에서도 돌도록 사용자 이름을 박지 않는다."""
    h = Path.home()
    for d in (h / 'Desktop', h / 'OneDrive' / 'Desktop', h / 'OneDrive' / '바탕 화면'):
        if d.is_dir():
            return d
    return h / 'Desktop'


WORK = Path(os.environ.get('PODCAST_B_DIR') or (_desktop() / '팟캐스트_출퇴근성경공부' / '트랙B_하루5분'))
# 방송한 질문·다음 번호 기록은 저장소에 둔다 → git pull 하면 어느 PC에서든 같은 기록으로 이어 간다.
STATE = HERE / 'podcast' / 'track_b_used.json'
QA = REPO / 'dictionary' / 'qa-topic.json'
VOICE = {'Desmond': '563f728c-e249-5a85-97ab-8461e8c09da6', 'Lucy': '6acca956-f45a-55cb-8a6e-e34fa85a03b0'}
OPEN = '하루 5분, 성경이 답합니다.'
SITE = 'https://www.biblynote.com'
SR = 44100

# 트랙 B 에서 다루지 않는 민감 주제(저자 목소리 트랙 A 로만) — 원칙: 전략가이드 4장 7항
SENSITIVE = re.compile('자살|우울|낙태|안락사|존엄사|연명|동성애|성관계|음란|포르노|이혼|재혼|임종|사별|장례|도박|중독|난임|불임|시험관|피임|성형|학대|정신과|무너')
FORBID = re.compile('정본역|킹제임스|KJV|개역|역본|번역|인공지능|\\bAI\\b|에이아이')
TOPIC_ORDER = ['신앙생활', '윤리·관계·문화', '구원·믿음', '교회·예배·헌금', '하나님·예수·삼위일체', '성령·은사', '성경·창조', '죽음·종말·천국']

FULL = {v: k for k, v in KO.items()}            # '요한복음' → 'John'
for ab, f in ABBR.items():
    FULL.setdefault(ab, f)


# ───────────────────────── 공통 ─────────────────────────
def out(*a):
    print(*a, flush=True)


def load_qa():
    return {e['term']: e for e in json.loads(QA.read_text(encoding='utf-8'))}


def state():
    for p in (STATE, WORK / 'used.json'):          # 옛 위치(작업 폴더)도 읽어 준다
        if p.exists():
            return json.loads(p.read_text(encoding='utf-8'))
    return {'next': 1, 'used': []}


def save_state(s):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(s, ensure_ascii=False, indent=1), encoding='utf-8')
    out(f'   사용 기록 갱신: {STATE.relative_to(REPO)} (다른 PC와 맞추려면 커밋·푸시)')


def bdir(batch):
    d = WORK / batch
    if not d.exists():
        sys.exit(f'주차 폴더가 없습니다: {d}')
    return d


def parse_ref(ref):
    """'요한복음 11:6' / '요 11:6-7' / '시편 27:14' → (파일명, 장, 시작절, 끝절)"""
    m = re.match(r'^\s*([1-3]?\s*[가-힣]+)\s*(\d+)\s*[:장]\s*(\d+)(?:\s*절)?(?:\s*[-~]\s*(\d+))?\s*절?\s*$', ref)
    if not m:
        return None
    book = m.group(1).replace(' ', '')
    f = FULL.get(book)
    if not f:
        return None
    a = int(m.group(3))
    return f, int(m.group(2)), a, int(m.group(4) or a)


def verse_text(ref):
    p = parse_ref(ref)
    if not p:
        return None, None
    f, c, a, z = p
    fp = REPO / 'bible' / 'kr' / f'{f}-{c}.json'
    if not fp.exists():
        return None, None
    ch = json.loads(fp.read_text(encoding='utf-8'))
    if z > len(ch) or a < 1 or z < a:
        return None, None
    body = ' '.join(ch[v - 1].strip() for v in range(a, z + 1))
    body = re.sub(r'["“”‘’「」『』]', '', body)          # 낭독용 — 데이터 속 따옴표 제거
    label = f'{KO[f]} {c}:{a}' + (f'-{z}' if z != a else '')
    unit = '편' if f == 'Psalms' else '장'                 # 시편은 '편'
    spoken = f'{KO[f]} {c}{unit} {a}절' + (f'부터 {z}절까지' if z != a else '')
    return label, (spoken, body)


# ───────────────────────── 1) 소재 고르기 ─────────────────────────
def cmd_plan(a):
    qa = load_qa()
    st = state()
    used = set(st['used'])
    cand = [e for e in qa.values() if e.get('category') == '자주 묻는 질문' and len(e['term']) >= 10
            and e['term'] not in used and not SENSITIVE.search(e['term'] + ' ' + e.get('def', ''))
            and e.get('scriptures')]
    order = {t: i for i, t in enumerate(TOPIC_ORDER)}
    cand.sort(key=lambda e: order.get(e.get('faqTopic'), 99))
    # 같은 분야만 몰리지 않게 분야를 돌아가며 뽑는다
    pools = {}
    for e in cand:
        pools.setdefault(e.get('faqTopic'), []).append(e)
    pick, keys = [], [k for k in TOPIC_ORDER if k in pools] + [k for k in pools if k not in TOPIC_ORDER]
    while len(pick) < a.count and any(pools[k] for k in keys):
        for k in keys:
            if pools[k] and len(pick) < a.count:
                pick.append(pools[k].pop(0))
    batch = a.name or datetime.date.today().strftime('%Y-%m-%d')
    d = WORK / batch
    if (d / 'batch.json').exists() and not a.force:
        sys.exit(f'이미 있는 주차입니다: {d} (다시 만들려면 --force)')
    d.mkdir(parents=True, exist_ok=True)
    eps = []
    for e in pick:
        eps.append({'id': f"B{st['next']:03d}", 'qa': e['term'], 'topic': e.get('faqTopic')})
        st['next'] += 1
    (d / 'batch.json').write_text(json.dumps({'batch': batch, 'episodes': eps}, ensure_ascii=False, indent=1), encoding='utf-8')
    save_state(st)  # 번호만 미리 잡는다(사용 기록은 assemble 때 남긴다)
    for e in eps:
        out(f"{e['id']}  [{e['topic']}] {e['qa']}")
    out(f'\n→ {d}\\batch.json  (질문을 바꾸려면 이 파일의 qa 를 사이트 질문 원문으로 고친 뒤 write)')


# ───────────────────────── 2) 대본 쓰기 ─────────────────────────
PROMPT = """당신은 한국어 성경 오디오 프로그램 「하루 5분, 성경이 답합니다」의 대본 작가입니다.
아래 [사이트 답변] 하나만을 근거로, 귀로 듣는 5분 대본을 JSON 으로 씁니다.

[출연]
- Lucy(여, 낭독자): 오늘의 질문을 읽는다. 성경 구절은 도구가 Lucy 목소리로 자동 삽입한다.
- Desmond(남, 진행자): 답·설명·흔한 오해·오늘의 적용을 말한다.

[구성 — 이 순서]
1. Lucy: "오늘의 질문입니다." + 질문을 듣기 좋게 다듬은 한두 문장
2. Desmond: 한마디 답 (사이트의 '한마디로' 문장을 말로 풀어서)
3. 설명 2~3단락 (Desmond). 단락 사이에 성경 구절 2~3개를 {{"verse": "책이름 장:절"}} 로 넣는다.
   구절 앞 Desmond 문장은 구절로 자연스럽게 넘어가되 장절이나 구절 내용을 미리 말하지 않는다(장절은 도구가 읽는다).
4. Desmond: "흔한 오해" 한 단락
5. Desmond: 오늘의 적용 한 단락 — 듣는 사람이 오늘 할 수 있는 한 가지

[규칙]
- Desmond·Lucy 대사 합계 1,700~2,000자(구절 제외, 완성 길이 약 5분). 문장은 짧게, 존댓말(-ㅂ니다, -십시오).
- 사이트 답변에 없는 사실·사례·숫자·인용을 보태지 않는다. 혹시 보탰다면 그 문장을 "added" 에 그대로 적는다.
- 구절은 가능한 한 [사이트 답변]의 '성구' 목록에서 고른다. 책 이름은 '요한복음', '시편'처럼 한글 전체 이름.
- 역본·번역·'정본역'·AI 를 언급하지 않는다. 특정 교회·목회자 이름을 쓰지 않는다. 마크다운·괄호 지시문 금지.
- 숫자는 아라비아 숫자 그대로 써도 된다(도구가 읽는 법을 바꾼다).
- "search": 사이트 질문 원문 안에 실제로 들어 있는 2~8글자 검색어(예: '응답이 없을 때').
- "title": 25자 이내, 듣는 사람의 고민에서 출발하는 제목.

[출력 — JSON 하나만]
{{"title": "...", "search": "...", "segments": [{{"who": "Lucy", "text": "..."}}, {{"who": "Desmond", "text": "..."}}, {{"verse": "요한복음 11:6"}}, ...], "added": []}}

[사이트 답변]
질문: {term}
한마디로: {def_}
본문:
{deep}
마무리: {note}
성구: {sc}
"""


def claude_exe():
    p = os.environ.get('LC_CLAUDE_EXE')
    if p and os.path.exists(p):
        return p
    for n in ('claude', 'claude.exe'):
        w = shutil.which(n)
        if w:
            return w
    la = os.environ.get('LOCALAPPDATA', '')
    c = glob.glob(os.path.join(la, 'Claude-Data', '*', 'claude-code', '*', '*', 'claude.exe'))
    return max(c, key=os.path.getmtime) if c else None


def ask_claude(prompt, model):
    """MAX 요금제의 Claude Code 를 명령줄로 부른다(API 키 없음 — 온라인 LC 와 같은 방식)."""
    exe = claude_exe()
    if not exe:
        raise RuntimeError('Claude Code 실행 파일을 찾지 못했습니다.')
    env = {k: v for k, v in os.environ.items() if not (k.startswith('CLAUDE') or k in ('ANTHROPIC_BASE_URL', 'AI_AGENT'))}
    work = WORK / '_ai'
    work.mkdir(parents=True, exist_ok=True)
    args = [exe, '-p', '--output-format', 'json', '--model', model, '--tools', '', '--no-session-persistence',
            '--setting-sources', '', '--strict-mcp-config', '--disable-slash-commands', '--max-turns', '1', '--effort', 'high']
    r = subprocess.run(args, input=prompt, capture_output=True, text=True, encoding='utf-8', errors='replace',
                       timeout=900, env=env, cwd=str(work), creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    raw = (r.stdout or '').strip()
    try:
        j = json.loads(raw)
    except Exception:
        raise RuntimeError('Claude 응답을 읽지 못했습니다: ' + ((r.stderr or '') + raw)[-300:])
    if j.get('is_error'):
        raise RuntimeError('Claude 호출 실패: ' + str(j.get('result'))[:300])
    t = j.get('result') or ''
    m = re.search(r'```(?:json)?\s*(.*?)```', t, re.S)
    t = m.group(1) if m else t
    return json.loads(t[t.find('{'): t.rfind('}') + 1])


def mock_script(e):
    deep = e.get('deep') or []
    sc = e.get('scriptures') or []
    segs = [{'who': 'Lucy', 'text': '오늘의 질문입니다. ' + e['term']},
            {'who': 'Desmond', 'text': re.sub(r'^한마디로\s*—\s*', '', e.get('def', ''))}]
    for i, d in enumerate(deep[:2]):
        segs.append({'who': 'Desmond', 'text': re.sub(r"'[^']*'\s*\([^)]*\)", '', d['p'])[:400]})
        if i < len(sc):
            segs.append({'verse': sc[i]})
    myth = next((d for d in deep if '오해' in d.get('h', '')), None)
    if myth:
        segs.append({'who': 'Desmond', 'text': '흔한 오해가 하나 있습니다. ' + myth['p'][:300]})
    segs.append({'who': 'Desmond', 'text': e.get('note', '')})
    return {'title': e['term'][:25], 'search': e['term'][:6], 'segments': segs, 'added': ['(모의 모드 — AI 미사용)']}


def finalize(ep, e, sc):
    """성경 본문 삽입 + 점검. 반환: (segments, warnings)"""
    warn = []
    srcblob = e['term'] + e.get('def', '') + ' '.join(d.get('p', '') for d in e.get('deep') or []) + e.get('note', '')
    src_sc = set(re.sub(r'\s', '', x) for x in (e.get('scriptures') or []))
    segs = [{'who': 'Lucy', 'kind': 'open', 'text': OPEN}]
    nchar = 0
    for s in sc.get('segments', []):
        if 'verse' in s:
            label, v = verse_text(s['verse'])
            if not label:
                warn.append(f"구절 위치를 찾을 수 없음: {s['verse']} → 빼고 진행")
                continue
            if re.sub(r'\s', '', label) not in src_sc and not any(re.sub(r'\s', '', s['verse']).startswith(x.split(':')[0]) for x in src_sc):
                warn.append(f'사이트 답변 성구 목록에 없는 구절: {label} (확인 필요)')
            segs.append({'who': 'Lucy', 'kind': 'verse', 'ref': label, 'text': f'{v[0]}. {v[1]}'})
            continue
        who = s.get('who') if s.get('who') in VOICE else 'Desmond'
        t = (s.get('text') or '').strip()
        if not t:
            continue
        if FORBID.search(t):
            warn.append(f'금지어 포함: "{t[:40]}…"')
        for num in set(re.findall(r'\d+', t)):
            if num not in srcblob:
                warn.append(f'원문에 없는 숫자 {num}: "{t[:40]}…"')
        nchar += len(t)
        segs.append({'who': who, 'kind': 'talk', 'text': t})
    search = (sc.get('search') or '').strip()
    if not search or search not in e['term']:
        warn.append(f"검색어 '{search}' 가 질문 원문에 없어 질문 앞부분으로 바꿈")
        search = re.sub(r'[?？.]', '', e['term'])[:10].strip()
    segs.append({'who': 'Lucy', 'kind': 'close', 'text': f'더 자세한 답은 바이블노트 닷컴에서 {search}, 이렇게 검색해 보세요.'})
    if not 1500 <= nchar <= 2300:
        warn.append(f'대사 분량 {nchar}자 (권장 1,700~2,000자)')
    for x in sc.get('added') or []:
        warn.append(f'원문에 없는 내용(작가 표시): {x}')
    return segs, search, warn


def cmd_write(a):
    d = bdir(a.batch)
    b = json.loads((d / 'batch.json').read_text(encoding='utf-8'))
    qa = load_qa()
    mock = os.environ.get('PODCAST_MOCK_AI') == '1'
    for ep in b['episodes']:
        if a.only and ep['id'] not in a.only.split(','):
            continue
        e = qa.get(ep['qa'])
        if not e:
            out(f"✗ {ep['id']}: 사이트 질문 데이터에 없음 — {ep['qa']}")
            continue
        t0 = time.time()
        try:
            prompt = PROMPT.format(term=e['term'], def_=re.sub(r'^한마디로\s*—\s*', '', e.get('def', '')),
                                   deep='\n'.join(f"- {x.get('h')}: {x.get('p')}" for x in e.get('deep') or []),
                                   note=e.get('note', ''), sc=', '.join(e.get('scriptures') or []))
            sc = mock_script(e) if mock else ask_claude(prompt, a.model)
        except Exception as ex:
            out(f"✗ {ep['id']}: {ex}")
            continue
        segs, search, warn = finalize(ep, e, sc)
        ep.update(title=(sc.get('title') or e['term'])[:40], search=search, segments=segs, warnings=warn,
                  written=datetime.datetime.now().isoformat(timespec='seconds'), approved=False)
        out(f"✓ {ep['id']} {ep['title']}  ({int(time.time() - t0)}초, 경고 {len(warn)})")
    (d / 'batch.json').write_text(json.dumps(b, ensure_ascii=False, indent=1), encoding='utf-8')
    review_docx(d, b)


# ───────────────────────── 검수표(워드) ─────────────────────────
def review_docx(d, b):
    from docx import Document
    from docx.shared import Pt, Cm, RGBColor
    from docx.oxml.ns import qn
    F = '맑은 고딕'
    doc = Document()
    s = doc.sections[0]
    s.left_margin = s.right_margin = Cm(1.8)
    st = doc.styles['Normal']; st.font.name = F; st.element.rPr.rFonts.set(qn('w:eastAsia'), F); st.font.size = Pt(10.5)

    def para(text, size=10.5, bold=False, color=None):
        p = doc.add_paragraph(); r = p.add_run(text); r.font.size = Pt(size); r.bold = bold
        r.font.name = F; r._element.get_or_add_rPr().get_or_add_rFonts().set(qn('w:eastAsia'), F)
        if color:
            r.font.color.rgb = RGBColor.from_string(color)
        return p
    para(f"「하루 5분, 성경이 답합니다」 검수표 — {b['batch']}", 16, True, '1F2A44')
    para('고치는 법: ① 표의 「내용」 칸을 직접 고친다 ② 화자를 바꾸려면 Desmond/Lucy 로 적는다 '
         '③ 성경 칸은 「|」 앞의 장절만 고친다(본문은 자동) ④ 줄을 지우려면 내용을 비운다 '
         '⑤ 방송해도 되면 「승인: [ ]」 괄호 안에 O 를 적는다. 다 하면 저장하고 닫는다.', 9.5, False, '555555')
    for ep in b['episodes']:
        if 'segments' not in ep:
            continue
        para(f"{ep['id']} · 제목: {ep['title']}", 13, True, '8A6A1F')
        para(f"원 질문: {ep['qa']}", 9.5, False, '555555')
        para(f"검색어: {ep['search']}", 9.5)
        for w in ep.get('warnings') or []:
            para('⚠ ' + w, 9.5, False, 'B00020')
        para('승인: [   ]', 12, True)
        t = doc.add_table(rows=1, cols=3); t.style = 'Table Grid'
        for c, h in zip(t.rows[0].cells, ('순서', '화자', '내용')):
            c.text = h
        for i, sg in enumerate(ep['segments'], 1):
            row = t.add_row().cells
            row[0].text = str(i)
            if sg['kind'] == 'verse':
                row[1].text = 'Lucy(성경)'
                row[2].text = f"{sg['ref']} | {sg['text'].split('. ', 1)[-1]}"
            else:
                row[1].text = sg['who'] + ('(고정)' if sg['kind'] in ('open', 'close') else '')
                row[2].text = sg['text']
        for r in t.rows:
            r.cells[0].width = Cm(1.2); r.cells[1].width = Cm(2.6); r.cells[2].width = Cm(14)
        doc.add_paragraph()
    p = d / f"검수표_{b['batch']}.docx"
    doc.save(p)
    out(f'\n검수표 → {p}')


def read_review(d, b):
    """검수표를 읽어 batch 의 segments·title·search·approved 를 갱신한다."""
    from docx import Document
    from docx.table import Table
    from docx.text.paragraph import Paragraph
    p = d / f"검수표_{b['batch']}.docx"
    doc = Document(p)
    byid = {e['id']: e for e in b['episodes']}
    cur = None
    for el in doc.element.body.iterchildren():
        tag = el.tag.split('}')[1]
        if tag == 'p':
            t = Paragraph(el, doc).text.strip()
            m = re.match(r'^(B\d{3}) · 제목:\s*(.*)$', t)
            if m:
                cur = byid.get(m.group(1))
                if cur:
                    cur['title'] = m.group(2).strip(); cur['approved'] = False
                continue
            if cur and t.startswith('검색어:'):
                cur['search'] = t.split(':', 1)[1].strip()
            m = re.match(r'^승인\s*[:：]\s*\[(.*)\]', t)
            if cur and m:
                cur['approved'] = bool(m.group(1).strip())
        elif tag == 'tbl' and cur:
            segs = []
            for r in Table(el, doc).rows[1:]:
                who, text = r.cells[1].text.strip(), r.cells[2].text.strip()
                if not text:
                    continue
                if who.startswith('Lucy(성경)'):
                    ref = text.split('|')[0].strip()
                    label, v = verse_text(ref)
                    if not label:
                        raise SystemExit(f"{cur['id']}: 성경 장절을 읽을 수 없습니다 → '{ref}' (예: 요한복음 11:6)")
                    segs.append({'who': 'Lucy', 'kind': 'verse', 'ref': label, 'text': f'{v[0]}. {v[1]}'})
                else:
                    w = 'Lucy' if who.startswith('Lucy') else 'Desmond'
                    kind = 'open' if text == OPEN else ('close' if text.startswith('더 자세한 답은') else 'talk')
                    segs.append({'who': w, 'kind': kind, 'text': text})
            cur['segments'] = segs
    return b


# ───────────────────────── 4) 승인분 → 음성 작업 목록 ─────────────────────────
def cmd_collect(a):
    d = bdir(a.batch)
    b = json.loads((d / 'batch.json').read_text(encoding='utf-8'))
    b = read_review(d, b)
    (d / 'batch.json').write_text(json.dumps(b, ensure_ascii=False, indent=1), encoding='utf-8')
    jobs = []
    for ep in b['episodes']:
        if not ep.get('approved'):
            out(f"- {ep['id']} 미승인 → 건너뜀")
            continue
        jobs.append({'id': ep['id'], 'title': ep['title'],
                     'segments': [{'n': i, 'who': s['who'], 'voice_id': VOICE[s['who']], 'tts': for_tts(s['text'])}
                                  for i, s in enumerate(ep['segments'], 1)]})
        out(f"✓ {ep['id']} {ep['title']} — {len(ep['segments'])}조각")
    (d / 'voice_jobs.json').write_text(json.dumps({'batch': b['batch'], 'model': 'text2speech_v2', 'variant': 'elevenlabs',
                                                   'voice_type': 'preset', 'episodes': jobs}, ensure_ascii=False, indent=1), encoding='utf-8')
    n = sum(len(j['segments']) for j in jobs)
    out(f"\n→ {d}\\voice_jobs.json  ({len(jobs)}편, {n}조각, 예상 약 {n * 0.3:.0f}크레딧)")


# ───────────────────────── 5) 음성 내려받기 ─────────────────────────
def cmd_fetch(a):
    d = bdir(a.batch)
    urls = json.loads((d / 'urls.json').read_text(encoding='utf-8'))     # {"B001": {"1": "https://…mp3", …}, …}
    bad = 0
    for eid, m in urls.items():
        od = d / 'audio' / eid
        od.mkdir(parents=True, exist_ok=True)
        for n, u in m.items():
            f = od / f'{int(n):02d}.mp3'
            if f.exists() and f.stat().st_size > 1000:
                continue
            for _ in range(3):
                try:
                    with urllib.request.urlopen(u, timeout=40) as r:
                        f.write_bytes(r.read())
                    break
                except Exception:
                    time.sleep(2)
            else:
                bad += 1; out(f'✗ {eid} {n} 받기 실패')
    out(f'받기 완료 (실패 {bad})')


# ───────────────────────── 6) 조립 ─────────────────────────
def ff(args):
    r = subprocess.run(['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error'] + args, capture_output=True)
    if r.returncode:
        raise RuntimeError(r.stderr.decode('utf-8', 'replace')[-500:])


def dur(p):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(p)], capture_output=True, text=True)
    return float(r.stdout.strip() or 0)


def shownotes(ep, e):
    one = re.sub(r'^한마디로\s*—\s*', '', (e or {}).get('def', ''))
    refs = [s['ref'] for s in ep['segments'] if s['kind'] == 'verse']
    link = f"{SITE}/dictionary.html?q={urllib.parse.quote(ep['search'])}&src=pod"
    return '\n'.join([f"[{ep['id']}] {ep['title']}", '', f"오늘의 질문: {ep['qa']}", f'한마디 답: {one}',
                      f"함께 읽은 말씀: {', '.join(refs)}", '', f'▶ 글로 읽기: {link}', f'▶ 질문 보내기: {SITE}', '',
                      '궁금한 질문을 보내 주시면 이 방송에서 답해 드립니다.']) + '\n'


def cmd_assemble(a):
    d = bdir(a.batch)
    b = json.loads((d / 'batch.json').read_text(encoding='utf-8'))
    qa = load_qa()
    st = state()
    o = WORK / '출력'
    o.mkdir(exist_ok=True)
    for ep in b['episodes']:
        if not ep.get('approved'):
            continue
        ad = d / 'audio' / ep['id']
        files = [ad / f'{i:02d}.mp3' for i in range(1, len(ep['segments']) + 1)]
        miss = [f.name for f in files if not f.exists()]
        if miss:
            out(f"✗ {ep['id']}: 음성 조각 없음 {miss}")
            continue
        tmp = Path(tempfile.mkdtemp(prefix='podb_'))
        try:
            gaps = {}
            for g in (0.35, 0.7):
                gaps[g] = tmp / f'gap{g}.wav'
                ff(['-f', 'lavfi', '-i', f'anullsrc=r={SR}:cl=mono', '-t', str(g), str(gaps[g])])
            lines = []
            for i, (f, sg) in enumerate(zip(files, ep['segments'])):
                w = tmp / f'{i:02d}.wav'
                ff(['-i', str(f), '-af', 'loudnorm=I=-16:TP=-1.5', '-ar', str(SR), '-ac', '1', str(w)])
                if i:
                    prev = ep['segments'][i - 1]['kind']
                    lines.append(gaps[0.7] if 'verse' in (sg['kind'], prev) else gaps[0.35])
                lines.append(w)
            lst = tmp / 'l.txt'
            lst.write_text(''.join(f"file '{p.as_posix()}'\n" for p in lines), encoding='utf-8')
            name = f"{ep['id']}_{re.sub(r'[\\/:*?\"<>|]', '', ep['title'])}"
            mp3 = o / f'{name}.mp3'
            ff(['-f', 'concat', '-safe', '0', '-i', str(lst), '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11', '-ar', str(SR), '-ac', '1',
                '-c:a', 'libmp3lame', '-b:a', '128k', '-id3v2_version', '3', '-metadata', f"title={ep['title']}",
                '-metadata', 'artist=바이블 인사이트', '-metadata', 'album=하루 5분, 성경이 답합니다',
                '-metadata', f"track={int(ep['id'][1:])}", '-metadata', 'genre=Podcast', str(mp3)])
            (o / f'{name}_쇼노트.txt').write_text(shownotes(ep, qa.get(ep['qa'])), encoding='utf-8')
            if ep['qa'] not in st['used']:
                st['used'].append(ep['qa'])
            out(f"✓ {mp3.name}  {int(dur(mp3) // 60)}분 {int(dur(mp3) % 60)}초")
            shutil.rmtree(ad, ignore_errors=True)        # PC 용량 최소화 — 조각은 완성본에 들어갔으니 지운다
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    save_state(st)


# ───────────────────────── 7) 정리(드라이브 업로드 뒤) ─────────────────────────
def cmd_clean(a):
    """구글 드라이브에 올린 뒤 PC 에서 이 주차의 큰 파일(mp3·음성 조각·AI 임시)을 휴지통 없이 지운다.
    검수표·batch.json·쇼노트(작은 글 파일)는 기록용으로 남긴다."""
    d = bdir(a.batch)
    b = json.loads((d / 'batch.json').read_text(encoding='utf-8'))
    freed = 0
    for p in [d / 'audio', WORK / '_ai']:
        if p.exists():
            freed += sum(f.stat().st_size for f in p.rglob('*') if f.is_file())
            shutil.rmtree(p, ignore_errors=True)
    for ep in b['episodes']:
        for f in (WORK / '출력').glob(f"{ep['id']}_*.mp3"):
            freed += f.stat().st_size
            f.unlink()
    out(f'정리 완료 — {freed / 1048576:.1f}MB 확보 (검수표·쇼노트·batch.json 은 남김)')


def cmd_doctor(a):
    """새 PC 점검 — 이 도구에 필요한 것이 다 있는지 확인한다."""
    ok = True

    def chk(name, good, hint=''):
        nonlocal ok
        ok = ok and bool(good)
        out(f"  {'✔' if good else '✘'} {name}" + ('' if good else f'  → {hint}'))
    out(f'Python {sys.version.split()[0]} · 저장소 {REPO}')
    chk('ffmpeg', shutil.which('ffmpeg'), 'PowerShell 에서 winget install Gyan.FFmpeg (설치 후 창을 새로 연다)')
    try:
        import docx  # noqa: F401
        chk('python-docx', True)
    except ImportError:
        chk('python-docx', False, 'python -m pip install python-docx')
    chk('사이트 질문 자료(qa-topic.json)', QA.exists(), 'git pull 로 저장소를 최신으로')
    chk('Claude Code(대본 쓰기)', claude_exe(), 'Claude 데스크톱 앱 설치·로그인 후 Code 탭을 한 번 연다')
    out(f'  · 작업 폴더: {WORK}' + ('' if WORK.exists() else ' (없음 — plan 할 때 자동 생성)'))
    st = state()
    out(f"  · 사용 기록: 다음 번호 B{st['next']:03d}, 방송한 질문 {len(st['used'])}개 ({STATE.relative_to(REPO)})")
    out('준비 완료' if ok else '✘ 표시를 먼저 해결하세요.')


def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    ap = argparse.ArgumentParser(description='팟캐스트 트랙 B 도구')
    sp = ap.add_subparsers(dest='cmd', required=True)
    p = sp.add_parser('plan'); p.add_argument('--count', type=int, default=5); p.add_argument('--name'); p.add_argument('--force', action='store_true')
    p = sp.add_parser('write'); p.add_argument('batch'); p.add_argument('--only'); p.add_argument('--model', default='opus')
    sp.add_parser('doctor')
    for c in ('collect', 'fetch', 'assemble', 'clean'):
        sp.add_parser(c).add_argument('batch')
    a = ap.parse_args()
    {'plan': cmd_plan, 'write': cmd_write, 'collect': cmd_collect, 'fetch': cmd_fetch, 'assemble': cmd_assemble,
     'clean': cmd_clean, 'doctor': cmd_doctor}[a.cmd](a)


if __name__ == '__main__':
    main()
