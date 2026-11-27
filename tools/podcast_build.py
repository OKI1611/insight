"""팟캐스트 「오광일의 출퇴근 성경공부」 회차 오디오 자동 편집

기존 강의 영상(또는 음성) → 음성 추출 → 불필요 구간 삭제 → 앞뒤 무음 제거
→ [콜드오픈] + 인트로 + 본편 + 아웃트로 이어 붙이기 → 음량 평준화(-16 LUFS, 2회 측정)
→ mp3(모노 128kbps, 제목·작가·회차 태그) + 에피소드 설명(쇼노트) 텍스트

사용법 (Python 은 PATH 미등록 — 전체 경로로 실행):
  python tools/podcast_build.py --init "%USERPROFILE%\\Desktop\\팟캐스트_출퇴근성경공부"
      → 작업 폴더(원본/·공통/·출력/)와 시즌 1 설정 파일(season1.json)을 만든다. 이미 있으면 건드리지 않는다.
  python tools/podcast_build.py <폴더>\\season1.json                 → 원본 파일이 있는 회차 모두 제작
  python tools/podcast_build.py <폴더>\\season1.json --only 1,2      → 1·2회만
  python tools/podcast_build.py <폴더>\\season1.json --notes-only    → 쇼노트만 다시 생성
  python tools/podcast_build.py <폴더>\\season1.json --check         → 무엇이 빠졌는지 점검만

시간 표기는 "12:30", "1:02:15", "750"(초) 모두 가능.
필요: ffmpeg(PATH), dictionary/qa-topic.json(쇼노트용 — 이 스크립트 기준 상위 폴더의 저장소).
"""
import argparse, json, os, re, shutil, subprocess, sys, tempfile, urllib.parse
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
QA_PATH = REPO / 'dictionary' / 'qa-topic.json'
SR = 44100
GAP = 0.6  # 조각 사이 무음(초)

SEASON1 = [
    (1, '나는 정말 구원받았을까', 'https://youtu.be/TWvBp5HxOi0', '구원의 확신은 어떻게 가질 수 있나요?', '구원의 확신'),
    (2, '또 같은 죄를 지었을 때', 'https://youtu.be/0ACBbRhsk8E', '같은 죄를 자꾸 반복하는데 저는 구원받은 게 맞나요?', '같은 죄'),
    (3, '은혜로 구원이면 막 살아도 될까', 'https://youtu.be/k4ivttCG6ys', '은혜로 구원받는다면 마음대로 살아도 되나요?', '마음대로 살아도'),
    (4, '기도했는데 응답이 없을 때', 'https://youtu.be/0Z1pi1KVqvw', '기도하면 모두 응답되나요? 응답이 없을 때는 왜인가요?', '응답이 없을 때'),
    (5, '걱정으로 잠 못 드는 밤에', 'https://youtu.be/suW4_QPBuD0', '밤마다 걱정에 잠 못 이룹니다. 불면과 염려를 신앙으로 어떻게 다스리나요?', '불면'),
    (6, '지금 이 고난, 하나님의 벌일까', 'https://youtu.be/OTZAYoMMVEQ', '내가 겪는 고난은 하나님이 내리시는 벌인가요?', '하나님이 내리시는 벌'),
    (7, '회사에서 무시당할 때', 'https://youtu.be/O2CdFl2bG8U', '직장 상사가 부당하게 대할 때 그리스도인은 어떻게 반응해야 하나요?', '직장 상사'),
    (8, '남의 성공이 배 아플 때', 'https://youtu.be/jcNtSVSMN5U', '다른 사람과 비교하며 열등감이나 시기심이 들 때 어떻게 해야 하나요?', '시기심'),
    (9, '교회 가는 기쁨이 사라졌다면', 'https://youtu.be/VCocJoBEBk0', '교회는 꼭 나가야 하나요? 혼자 믿으면 안 되나요?', '혼자 믿으면'),
    (10, '교회를 떠난 사람들의 이야기', 'https://youtu.be/UiHRAAbZQy8', "교회에 상처받고 어디에도 소속되지 못한 '가나안 성도'로 지냅니다. 이대로 괜찮을까요?", '가나안 성도'),
    (11, '열심히 섬길수록 지칠 때', 'https://youtu.be/pKsfKBCTv0Q', '교회 봉사를 열심히 하다가 지쳐서 번아웃이 왔습니다. 어떻게 해야 하나요?', '봉사를 열심히'),
    (12, '사랑하는 사람을 먼저 보냈을 때', 'https://youtu.be/UdQygsGQa8A', '사별의 슬픔이 너무 커서 헤어나올 수가 없습니다. 어떻게 견디나요?', '사별의 슬픔'),
]

MEDIA_EXT = ('.mp4', '.mov', '.mkv', '.webm', '.m4a', '.mp3', '.wav', '.aac', '.flac')


# ---------------- 공통 ----------------
def t2s(v):
    """'1:02:15' / '12:30' / 750 → 초"""
    if v is None or v == '':
        return None
    if isinstance(v, (int, float)):
        return float(v)
    parts = [float(p) for p in str(v).strip().split(':')]
    s = 0.0
    for p in parts:
        s = s * 60 + p
    return s


def fmt(sec):
    sec = int(round(sec))
    h, m, s = sec // 3600, sec % 3600 // 60, sec % 60
    return f'{h}:{m:02d}:{s:02d}' if h else f'{m}:{s:02d}'


def run(cmd, capture=False):
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if r.returncode != 0:
        err = r.stderr.decode('utf-8', 'replace')[-1500:]
        raise RuntimeError('ffmpeg 실패:\n' + err)
    return r.stderr.decode('utf-8', 'replace') if capture else None


def duration(path):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                        '-of', 'default=nw=1:nk=1', str(path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        return float(r.stdout.decode().strip())
    except ValueError:
        raise RuntimeError(f'길이를 읽을 수 없는 파일: {path}')


def to_wav(src, dst, filt=None, ss=None, to=None):
    cmd = ['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error']
    if ss is not None:
        cmd += ['-ss', str(ss)]
    if to is not None:
        cmd += ['-to', str(to)]
    cmd += ['-i', str(src), '-vn', '-ac', '1', '-ar', str(SR)]
    if filt:
        cmd += ['-af', filt]
    cmd += ['-c:a', 'pcm_s16le', str(dst)]
    run(cmd)


# 앞뒤 무음 제거. 봉우리(peak) 기준 -50dB — 작게 녹음된 강의가 통째로 '무음'으로 잘리지 않게 보수적으로.
TRIM_SIL = ('silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.2:detection=peak,'
            'areverse,silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.4:detection=peak,areverse')


def to_wav_trimmed(src, dst, pre=None, ss=None, to=None):
    """무음 제거까지 한 wav. 결과가 비었거나 절반 이하로 줄면 무음 제거 없이 다시 만든다(안전장치)."""
    plain = ','.join(f for f in (pre,) if f) or None
    to_wav(src, dst, ','.join(f for f in (pre, TRIM_SIL) if f), ss=ss, to=to)
    try:
        got = duration(dst)
    except RuntimeError:
        got = 0
    to_wav(src, str(dst) + '.raw.wav', plain, ss=ss, to=to)
    full = duration(str(dst) + '.raw.wav')
    if got < full * 0.5:
        print(f'   ! 무음 제거 결과가 너무 짧음({fmt(got)} / {fmt(full)}) → 무음 제거 없이 사용 (녹음 음량 확인 권장)')
        os.replace(str(dst) + '.raw.wav', dst)
    else:
        os.remove(str(dst) + '.raw.wav')


def ep_name(ep):
    return '%02d_%s' % (int(ep['no']), re.sub(r'[\\/:*?"<>|]', '', ep['title']))


def resolve(base, p):
    if not p:
        return None
    q = Path(p)
    return q if q.is_absolute() else (base / q)


def per_episode_file(base, key, ep):
    word = {'intro': '인트로', 'outro': '아웃트로'}[key]
    d = base / '공통'
    if d.exists():
        for f in sorted(d.iterdir()):
            if f.suffix.lower() in MEDIA_EXT and f.stem == '%s_%02d' % (word, int(ep['no'])):
                return f
    return None


def find_source(base, ep):
    """설정의 source 가 비어 있으면 원본/ 에서 'ep01' 또는 '01_' 로 시작하는 파일을 찾는다."""
    p = resolve(base, ep.get('source'))
    if p:
        return p if p.exists() else None
    d = base / '원본'
    if not d.exists():
        return None
    n = int(ep['no'])
    for f in sorted(d.iterdir()):
        if f.suffix.lower() in MEDIA_EXT and re.match(rf'^(ep)?0*{n}([_\-. ]|$)', f.stem, re.I):
            return f
    return None


# ---------------- 쇼노트 ----------------
def load_qa():
    try:
        return {e['term']: e for e in json.loads(QA_PATH.read_text(encoding='utf-8'))}
    except FileNotFoundError:
        return {}


def shownotes(show, ep, qa):
    site = show.get('site', 'https://www.biblynote.com').rstrip('/')
    e = qa.get(ep.get('qa', ''), {})
    one = re.sub(r'^한마디로\s*—\s*', '', e.get('def', '')).strip()
    verses = ', '.join((e.get('scriptures') or [])[:3])
    link = f"{site}/dictionary.html?q={urllib.parse.quote(ep.get('search', ''))}&src=pod"
    lines = [f"[{ep['no']}회] {ep['title']}", '']
    if ep.get('qa'):
        lines.append(f"오늘의 질문: {ep['qa']}")
    if one:
        lines.append(f'한마디 답: {one}')
    if verses:
        lines.append(f'함께 읽은 말씀: {verses}')
    lines += ['', f'▶ 글로 읽기: {link}']
    if ep.get('youtube'):
        lines.append(f"▶ 영상으로 보기: {ep['youtube']}")
    lines.append(f'▶ 질문 보내기: {site}')
    lines += ['', show.get('footer', '궁금한 질문을 보내 주시면 목요일 「성경이 답합니다」에서 답해 드립니다.')]
    if ep.get('qa') and not e:
        lines += ['', f"※ 확인 필요: 사이트 질문 데이터에서 '{ep['qa']}' 를 찾지 못했습니다."]
    return '\n'.join(lines) + '\n'


# ---------------- 제작 ----------------
def build_episode(base, show, common, ep, out_dir, qa):
    src = find_source(base, ep)
    if not src:
        raise RuntimeError('원본 파일 없음 (원본/ 폴더에 ep%02d_… 로 넣거나 source 칸에 경로 입력)' % int(ep['no']))
    tmp = Path(tempfile.mkdtemp(prefix='pod_'))
    try:
        total = duration(src)
        # 1) 본편: 삭제 구간 제외 + 앞뒤 무음 제거
        cuts = [(t2s(a), t2s(b)) for a, b in (ep.get('cut') or [])]
        start, end = t2s(ep.get('start')), t2s(ep.get('end'))
        filt = []
        if cuts:
            cond = '+'.join(f'between(t,{a},{b})' for a, b in cuts)
            filt.append(f"aselect='not({cond})',asetpts=N/SR/TB")
        body = tmp / 'body.wav'
        to_wav_trimmed(src, body, ','.join(filt) or None, ss=start, to=end)
        # 2) 콜드오픈
        pieces = []
        cold = ep.get('cold')
        if cold:
            a, b = t2s(cold[0]), t2s(cold[1])
            if not (0 <= a < b <= total):
                raise RuntimeError(f'콜드오픈 구간이 원본 길이({fmt(total)})를 벗어남')
            cw = tmp / 'cold.wav'
            to_wav(src, cw, f'afade=t=in:d=0.15,afade=t=out:st={max(b - a - 0.4, 0)}:d=0.4', ss=a, to=b)
            pieces.append(cw)
        # 3) 인트로·아웃트로 (회차별 파일이 있으면 그것, 없으면 공통)
        for key in ('intro', 'body', 'outro'):
            if key == 'body':
                pieces.append(body)
                continue
            # 우선순위: 설정 칸 → 공통/인트로_01.* (회차별 녹음) → 공통 파일
            p = resolve(base, ep.get(key)) or per_episode_file(base, key, ep) or resolve(base, common.get(key))
            if p and p.exists():
                w = tmp / f'{key}.wav'
                to_wav_trimmed(p, w)
                pieces.append(w)
            elif p:
                print(f'   ! {key} 파일 없음 → 건너뜀: {p}')
        # 4) 이어 붙이기 (사이 무음 0.6초)
        gap = tmp / 'gap.wav'
        run(['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error', '-f', 'lavfi', '-i',
             f'anullsrc=r={SR}:cl=mono', '-t', str(GAP), '-c:a', 'pcm_s16le', str(gap)])
        lst = tmp / 'list.txt'
        seq = []
        for i, p in enumerate(pieces):
            if i:
                seq.append(gap)
            seq.append(p)
        lst.write_text(''.join(f"file '{p.as_posix()}'\n" for p in seq), encoding='utf-8')
        joined = tmp / 'joined.wav'
        run(['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error', '-f', 'concat', '-safe', '0',
             '-i', str(lst), '-c:a', 'pcm_s16le', str(joined)])
        # 5) 음량 평준화 2회(측정 → 적용)
        target = show.get('lufs', -16)
        log = run(['ffmpeg', '-hide_banner', '-i', str(joined), '-af',
                   f'loudnorm=I={target}:TP=-1.5:LRA=11:print_format=json', '-f', 'null', '-'], capture=True)
        m = json.loads(log[log.rindex('{'):log.rindex('}') + 1])
        ln = (f"loudnorm=I={target}:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
              f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
        name = ep_name(ep)
        mp3 = out_dir / f'{name}.mp3'
        run(['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error', '-i', str(joined), '-af', ln,
             '-ar', str(SR), '-ac', '1', '-c:a', 'libmp3lame', '-b:a', show.get('bitrate', '128k'),
             '-id3v2_version', '3',
             '-metadata', f"title={int(ep['no'])}. {ep['title']}",
             '-metadata', f"artist={show.get('artist', '오광일')}",
             '-metadata', f"album={show.get('title', '')}",
             '-metadata', f"track={int(ep['no'])}",
             '-metadata', 'genre=Podcast', str(mp3)])
        (out_dir / f'{name}_쇼노트.txt').write_text(shownotes(show, ep, qa), encoding='utf-8')
        return mp3, total, duration(mp3)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ---------------- 작업 폴더 만들기 ----------------
def init(folder):
    base = Path(folder)
    for d in ('원본', '공통', '출력'):
        (base / d).mkdir(parents=True, exist_ok=True)
    cfg = base / 'season1.json'
    if cfg.exists():
        print(f'이미 있음(덮어쓰지 않음): {cfg}')
        return
    data = {
        'show': {'title': '오광일의 출퇴근 성경공부', 'artist': '오광일', 'site': 'https://www.biblynote.com',
                 'lufs': -16, 'bitrate': '128k'},
        'common': {'intro': '공통/인트로.wav', 'outro': '공통/아웃트로.wav'},
        'episodes': [{'no': n, 'title': t, 'youtube': y, 'qa': q, 'search': s,
                      'source': '', 'start': '', 'end': '', 'cold': [], 'cut': [],
                      'intro': '', 'outro': ''} for n, t, y, q, s in SEASON1],
    }
    cfg.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'작업 폴더 준비 완료: {base}\n설정 파일: {cfg}')


def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    ap = argparse.ArgumentParser(description='팟캐스트 회차 오디오 자동 편집')
    ap.add_argument('config', nargs='?')
    ap.add_argument('--init', metavar='폴더')
    ap.add_argument('--only', help='예: 1,2,5')
    ap.add_argument('--notes-only', action='store_true')
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--clean-source', action='store_true',
                    help='완성 뒤 원본 영상(원본/ 폴더)을 지워 PC 용량을 아낀다 — 원본은 유튜브 스튜디오에서 다시 받을 수 있다')
    a = ap.parse_args()
    if a.init:
        return init(a.init)
    if not a.config:
        ap.error('설정 파일(season1.json) 경로가 필요합니다')
    if not shutil.which('ffmpeg'):
        sys.exit('ffmpeg 를 찾을 수 없습니다(PATH 확인).')
    cfgp = Path(a.config).resolve()
    base = cfgp.parent
    cfg = json.loads(cfgp.read_text(encoding='utf-8'))
    show, common = cfg.get('show', {}), cfg.get('common', {})
    out_dir = base / '출력'
    out_dir.mkdir(exist_ok=True)
    qa = load_qa()
    only = {int(x) for x in a.only.split(',')} if a.only else None
    eps = [e for e in cfg['episodes'] if not only or int(e['no']) in only]

    if a.check:
        for k in ('intro', 'outro'):
            p = resolve(base, common.get(k))
            print(f"공통 {k}: {'있음' if p and p.exists() else '없음'} ({p})")
        for e in eps:
            src = find_source(base, e)
            miss = [k for k in ('cold',) if not e.get(k)]
            qa_ok = e.get('qa') in qa
            print(f"{int(e['no']):>2}회 {e['title']}: 원본 {'있음' if src else '없음'}"
                  f"{'' if qa_ok else ' / 질문 데이터 못 찾음'}{' / 콜드오픈 미지정' if miss else ''}")
        return

    ok = fail = skip = 0
    for e in eps:
        tag = f"{int(e['no']):02d}회 {e['title']}"
        if a.notes_only:
            name = ep_name(e)
            (out_dir / f'{name}_쇼노트.txt').write_text(shownotes(show, e, qa), encoding='utf-8')
            print(f'✓ {tag} 쇼노트')
            ok += 1
            continue
        if not find_source(base, e):
            print(f'- {tag}: 원본 없음 → 건너뜀')
            skip += 1
            continue
        try:
            mp3, src_len, out_len = build_episode(base, show, common, e, out_dir, qa)
            print(f'✓ {tag}: 원본 {fmt(src_len)} → 완성 {fmt(out_len)}  ({mp3.name})')
            ok += 1
            src = find_source(base, e)
            if a.clean_source and src and src.is_relative_to(base / '원본'):
                mb = src.stat().st_size / 1048576
                src.unlink()
                print(f'   원본 삭제({mb:.0f}MB 확보): {src.name}')
        except Exception as ex:
            print(f'✗ {tag}: {ex}')
            fail += 1
    print(f'\n완료 {ok} · 실패 {fail} · 건너뜀 {skip}  → {out_dir}')
    if fail:
        sys.exit(1)


if __name__ == '__main__':
    main()
