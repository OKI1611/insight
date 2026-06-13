# -*- coding: utf-8 -*-
"""
유튜브 채널 실적(구독자·누적 조회수·영상 수)을 자동으로 가져와 content/site.json 의
youtube.stats 를 갱신한다. GitHub Actions 가 매일 실행 → 커밋 → Cloudflare 자동 배포.
실패하면(파싱 불가 등) 기존 값을 그대로 두고 종료한다(graceful).
무료 강의 편수(free_lectures)는 content/course.json 에서 직접 계산한다.
사용: python tools/update_yt_stats.py
"""
import urllib.request, re, io, json, os, sys

CHANNEL_ID = "UC82IOMnZud8NNt3BYzAxTMg"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def fetch(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
        "Accept-Language": "ko-KR,ko",
        "Cookie": "CONSENT=YES+cb",   # EU 동의 벽 우회
    })
    return urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "ignore")

def parse_subs(text):
    # "구독자 7.35천명" / "구독자 1.2만명" / "구독자 980명"
    m = re.search(r"구독자\s*([\d\.]+)\s*(천|만)?\s*명", text)
    if not m: return None
    v = float(m.group(1)); unit = m.group(2)
    if unit == "만": v *= 10000
    elif unit == "천": v *= 1000
    return int(v)

def fmt_plus(n, step):           # n 을 step 단위로 내림 + "+"
    return "{:,}+".format((n // step) * step)

def fmt_man(n):                  # 1,423,869 -> "142만+"
    if n >= 10000:
        return "{}만+".format(n // 10000)
    return fmt_plus(n, 100)

def free_lectures():
    try:
        raw = io.open(os.path.join(ROOT, "content", "course.json"), encoding="utf-8-sig").read()
        d = json.loads(raw)
        seen = set()
        for lv in d.get("levels", []):
            for les in lv.get("lessons", []):
                vid = (les.get("youtube", "") or "").split("/")[-1].split("=")[-1]
                if vid: seen.add(vid)
        return "{}편".format(len(seen)) if seen else None
    except Exception:
        return None

def main():
    html = fetch("https://www.youtube.com/channel/%s/about" % CHANNEL_ID)
    subs_n = parse_subs(html)
    mv = re.search(r'"viewCountText":"조회수 ([\d,]+)회"', html) or re.search(r"조회수 ([\d,]+)회", html)
    md = re.search(r'"videoCountText":"동영상 ([\d,]+)개"', html)
    views_n = int(mv.group(1).replace(",", "")) if mv else None
    videos_n = int(md.group(1).replace(",", "")) if md else None

    new = {}
    if subs_n:   new["subscribers"] = fmt_plus(subs_n, 100)
    if views_n:  new["views"] = fmt_man(views_n)
    if videos_n: new["videos"] = fmt_plus(videos_n, 10)
    fl = free_lectures()
    if fl: new["free_lectures"] = fl

    if not new:
        print("no stats parsed — keep existing"); return 0

    path = os.path.join(ROOT, "content", "site.json")
    site = json.loads(io.open(path, encoding="utf-8-sig").read())
    site.setdefault("youtube", {}).setdefault("stats", {})
    before = dict(site["youtube"]["stats"])
    site["youtube"]["stats"].update(new)
    if site["youtube"]["stats"] == before:
        print("unchanged:", before); return 0
    io.open(path, "w", encoding="utf-8").write(json.dumps(site, ensure_ascii=False, indent=2) + "\n")
    print("updated:", json.dumps(new, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    sys.exit(main())
