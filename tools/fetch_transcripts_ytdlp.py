# -*- coding: utf-8 -*-
"""course.json의 모든 강의 유튜브 한국어 자막을 yt-dlp로 받아 content/transcripts/<videoId>.txt 저장.
자동자막(automatic_captions) ko 우선, 수동자막 있으면 우선. 롤링 중복 제거해 평문화.
사용: python tools/fetch_transcripts_ytdlp.py [limit]
"""
import os, sys, re, json, io, urllib.request

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import yt_dlp

OUT = 'content/transcripts'
os.makedirs(OUT, exist_ok=True)
LOG = 'tools/_transcript_log.txt'

def vid_of(url):
    if not url: return None
    m = re.search(r'(?:youtu\.be/|v=|/embed/|/shorts/)([A-Za-z0-9_-]{11})', url)
    return m.group(1) if m else None

def lessons():
    c = json.load(open('content/course.json', encoding='utf-8'))
    out = []
    for lv in c.get('levels', []):
        for ls in lv.get('lessons', []):
            v = vid_of(ls.get('youtube'))
            if v: out.append((v, ls.get('title', '')))
    # 중복 videoId 제거(순서 유지)
    seen = set(); uniq = []
    for v, t in out:
        if v in seen: continue
        seen.add(v); uniq.append((v, t))
    return uniq

def parse_json3(raw):
    """json3 자막 → 평문. 롤링 중복 제거."""
    try:
        data = json.loads(raw)
    except Exception:
        return None
    lines = []
    for ev in data.get('events', []):
        segs = ev.get('segs')
        if not segs: continue
        text = ''.join(s.get('utf8', '') for s in segs)
        text = text.replace('\n', ' ').strip()
        if not text: continue
        if lines and (text == lines[-1] or text in lines[-1]): continue
        lines.append(text)
    # 인접 중복/포함 관계 정리
    cleaned = []
    for t in lines:
        if cleaned and (t == cleaned[-1]): continue
        cleaned.append(t)
    return ' '.join(cleaned).strip()

def fetch_one(vid):
    url = 'https://www.youtube.com/watch?v=' + vid
    opts = {'skip_download': True, 'quiet': True, 'no_warnings': True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    title = info.get('title', '')
    subs = info.get('subtitles', {}) or {}
    auto = info.get('automatic_captions', {}) or {}
    track = None
    for langset in (subs, auto):
        for lang in ('ko', 'ko-KR', 'ko-orig'):
            if lang in langset:
                track = langset[lang]; break
        if track: break
    if not track:
        return title, None
    # json3 포맷 URL 선택
    fmt = None
    for f in track:
        if f.get('ext') == 'json3': fmt = f; break
    if not fmt: fmt = track[0]
    surl = fmt.get('url')
    if 'fmt=' not in surl: surl += ('&' if '?' in surl else '?') + 'fmt=json3'
    req = urllib.request.Request(surl, headers={'User-Agent': 'Mozilla/5.0'})
    raw = urllib.request.urlopen(req, timeout=30).read().decode('utf-8', 'replace')
    text = parse_json3(raw)
    return title, text

def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 100000
    ls = lessons()
    done = ok = skip = err = 0
    logf = open(LOG, 'a', encoding='utf-8')
    for vid, title in ls:
        if done >= limit: break
        done += 1
        path = os.path.join(OUT, vid + '.txt')
        if os.path.exists(path) and os.path.getsize(path) > 200:
            skip += 1; continue
        try:
            t, text = fetch_one(vid)
            if not text or len(text) < 100:
                err += 1; logf.write(f"NOSUB {vid} {title[:30]}\n"); logf.flush(); continue
            with open(path, 'w', encoding='utf-8') as f:
                f.write('# ' + (t or title) + '\n# videoId: ' + vid + '\n\n' + text)
            ok += 1
            if ok % 10 == 0:
                logf.write(f"progress ok={ok} skip={skip} err={err} ({done}/{len(ls)})\n"); logf.flush()
        except Exception as e:
            err += 1; logf.write(f"ERR {vid} {str(e)[:120]}\n"); logf.flush()
    msg = f"DONE ok={ok} skip={skip} err={err} total_seen={done}/{len(ls)}"
    logf.write(msg + '\n'); logf.close()
    print(msg)

if __name__ == '__main__':
    main()
