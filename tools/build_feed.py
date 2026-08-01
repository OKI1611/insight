# -*- coding: utf-8 -*-
"""feed.xml (RSS 2.0) 생성기 — 홈페이지 최신 글 피드.

  네이버 웹마스터도구·구글 서치콘솔에 제출하면 새 글을 훨씬 빨리 수집해 간다.
  담는 글: ① 오늘의 말씀 묵상(content/daily/*.json — 실제 날짜 있음)
           ② 성경 번역 이야기(content/translation-notes.json)
  실행: python tools/build_feed.py
"""
import os, io, re, sys, json, glob, datetime, email.utils

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

BASE  = "https://biblynote.com"
TITLE = "BIBLY 바이블 인사이트 — 오광일의 인사이트 브리핑"
DESC  = "천년왕국·종말론·성경적 세계관을 본문과 검증된 신학으로 배우는 온라인 성경 아카데미의 최신 글."
MAX   = 30


def load(path):
    try:
        return json.loads(io.open(path, encoding="utf-8-sig").read())
    except Exception:
        return None


def rfc822(d):
    """YYYY-MM-DD → RFC822(RSS pubDate). 시각은 09:00 KST 로 고정."""
    try:
        y, m, dd = [int(x) for x in str(d).split("-")[:3]]
        return email.utils.format_datetime(
            datetime.datetime(y, m, dd, 9, 0, tzinfo=datetime.timezone(datetime.timedelta(hours=9))))
    except Exception:
        return email.utils.format_datetime(datetime.datetime.now(datetime.timezone.utc))


def plain(s, n=300):
    s = re.sub(r"(?s)<[^>]+>", " ", str(s or ""))
    s = re.sub(r"\s+", " ", s).strip()
    return s[:n] + ("…" if len(s) > n else "")


def cdata(s):
    return "<![CDATA[" + str(s or "").replace("]]>", "]]&gt;") + "]]>"


def collect():
    today = datetime.date.today().isoformat()
    out = []

    # ① 오늘의 말씀 묵상 — 오늘까지 공개된 것만(미래 예약분 제외)
    for p in sorted(glob.glob(os.path.join("content", "daily", "2*.json")), reverse=True):
        d = load(p)
        if not d or not d.get("date") or d["date"] > today:
            continue
        body = " ".join([(s.get("p") or "") for s in (d.get("sections") or [])])
        out.append({
            "title": "[오늘의 말씀] %s" % (d.get("title") or d.get("ref") or d["date"]),
            "link":  "%s/daily?d=%s" % (BASE, d["date"]),
            "date":  d["date"],
            "cat":   "오늘의 말씀 묵상",
            "desc":  plain(d.get("verse_kr") or body),
        })

    # ② 성경 번역 이야기 — 날짜 필드가 없으므로 원본 JSON의 갱신일을 발행일로 쓴다
    tn_path = os.path.join("content", "translation-notes.json")
    tn = load(tn_path)
    if tn is not None:
        stamp = datetime.date.fromtimestamp(os.path.getmtime(tn_path)).isoformat()
        notes = (tn.get("notes") if isinstance(tn, dict) else tn) or []
        for n in notes:
            if not n.get("id"):
                continue
            out.append({
                "title": "[성경 번역 이야기] %s" % n.get("title", ""),
                "link":  "%s/translation-notes?id=%s" % (BASE, n["id"]),
                "date":  n.get("date") or stamp,
                "cat":   "성경 번역 이야기",
                "desc":  plain(n.get("summary") or n.get("verse") or ""),
            })

    out.sort(key=lambda x: x["date"], reverse=True)
    return out[:MAX]


def main():
    items = collect()
    if not items:
        print("생성할 글이 없습니다.", file=sys.stderr)
        return 1

    now = email.utils.format_datetime(datetime.datetime.now(datetime.timezone.utc))
    L = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">',
         "  <channel>",
         "    <title>%s</title>" % TITLE,
         "    <link>%s/</link>" % BASE,
         "    <description>%s</description>" % DESC,
         "    <language>ko</language>",
         "    <lastBuildDate>%s</lastBuildDate>" % now,
         '    <atom:link href="%s/feed.xml" rel="self" type="application/rss+xml"/>' % BASE]
    for it in items:
        L += ["    <item>",
              "      <title>%s</title>" % cdata(it["title"]),
              "      <link>%s</link>" % it["link"].replace("&", "&amp;"),
              "      <guid isPermaLink=\"true\">%s</guid>" % it["link"].replace("&", "&amp;"),
              "      <category>%s</category>" % cdata(it["cat"]),
              "      <pubDate>%s</pubDate>" % rfc822(it["date"]),
              "      <description>%s</description>" % cdata(it["desc"]),
              "    </item>"]
    L += ["  </channel>", "</rss>"]

    io.open("feed.xml", "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("feed.xml: %d건 (최신 %s)" % (len(items), items[0]["date"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
