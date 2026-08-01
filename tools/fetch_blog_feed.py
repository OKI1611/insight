# -*- coding: utf-8 -*-
"""네이버 블로그 RSS → content/blog-feed.json

  https://rss.blog.naver.com/gaonview.xml 를 읽어 홈페이지 '블로그 최신글' 카드용
  JSON 으로 정리한다. GitHub Actions(update-blog-feed.yml)가 6시간마다 실행 →
  변경분만 커밋 → Cloudflare 자동 배포.

  · 네이버 글쓰기 API는 2020-05 폐지되어 홈→블로그 자동발행은 불가(관리자 원고 도우미로 대체).
    블로그→홈 방향만 RSS 로 완전 자동화한다.
  · 성경·신학 브랜드 정체성 유지를 위해 정치·연예 카테고리 글은 제외한다.
"""
import json, io, os, re, sys, datetime
import urllib.request
import xml.etree.ElementTree as ET

try:  # 윈도우 cp949 콘솔에서도 한글·기호 로그가 깨지지 않도록
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(ROOT, "content", "blog-feed.json")
SITE = os.path.join(ROOT, "content", "site.json")

DEFAULT_RSS  = "https://rss.blog.naver.com/gaonview.xml"
DEFAULT_HOME = "https://blog.naver.com/gaonview"
MAX_ITEMS    = 8          # 홈에 보관할 최신 글 수
SUMMARY_LEN  = 110        # 카드 요약 글자수

# 홈에 노출할 카테고리 판별 — 블랙리스트가 아니라 '성경·신학 화이트리스트'.
#   네이버 RSS 의 <category> 는 블로그 카테고리명 그대로 오는데('최신 이슈' 등),
#   이름이 언제든 바뀔 수 있으므로 카테고리명에 포함된 키워드로 판단한다.
#   → 새 카테고리(천년왕국 스토리·성경 번역 이야기·이단 바로 알기·시대 분별 …)도 자동 통과.
ALLOW_KEYWORD = (
    "성경", "성서", "말씀", "묵상", "신학", "복음", "예언", "종말", "천년왕국",
    "번역", "이단", "분별", "교회", "설교", "기도", "믿음", "신앙", "성령", "구원",
)
# 카테고리를 통과해도 제목에 이것이 있으면 제외(정치·시사 유입 차단)
SKIP_KEYWORD = ("대선", "총선", "여론조사", "국힘", "민주당", "이재명", "윤석열")


def site_blog_conf():
    """content/site.json 의 blog.rss / blog.url 을 우선 사용(주소 변경 시 한 곳만 고치면 됨)."""
    try:
        s = json.loads(io.open(SITE, encoding="utf-8").read())
        b = s.get("blog") or {}
        return (b.get("rss") or DEFAULT_RSS), (b.get("url") or DEFAULT_HOME)
    except Exception:
        return DEFAULT_RSS, DEFAULT_HOME


def strip_html(s):
    s = re.sub(r"(?is)<(script|style).*?</\1>", " ", s or "")
    s = re.sub(r"(?s)<[^>]+>", " ", s)
    s = (s.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<")
          .replace("&gt;", ">").replace("&quot;", '"').replace("&#39;", "'"))
    return re.sub(r"\s+", " ", s).strip()


def to_iso(pub):
    """RSS pubDate(RFC822) → YYYY-MM-DD. 파싱 실패 시 원문 유지."""
    for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S GMT", "%a, %d %b %Y %H:%M:%S"):
        try:
            return datetime.datetime.strptime((pub or "").strip(), fmt).strftime("%Y-%m-%d")
        except Exception:
            pass
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", pub or "")
    return "%s-%s-%s" % m.groups() if m else ""


def text(node, tag):
    el = node.find(tag)
    return (el.text or "").strip() if el is not None and el.text else ""


def excluded(category, title):
    """성경·신학 카테고리만 통과. 카테고리가 비어 있으면 제목으로 한 번 더 판별."""
    hay = category or title
    if not any(k in hay for k in ALLOW_KEYWORD):
        return True
    return any(k in title for k in SKIP_KEYWORD)


def fetch(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (compatible; BiblyBot/1.0; +https://biblynote.com)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def main():
    rss_url, home_url = site_blog_conf()
    raw = fetch(rss_url)
    root = ET.fromstring(raw)

    items, skipped = [], 0
    for it in root.iter("item"):
        title = strip_html(text(it, "title"))
        link  = text(it, "link")
        cat   = strip_html(text(it, "category"))
        if not title or not link:
            continue
        if excluded(cat, title):
            skipped += 1
            continue
        body = strip_html(text(it, "description"))
        tags = [t.strip() for t in re.split(r"[,\s]+", strip_html(text(it, "tag"))) if t.strip()]
        items.append({
            "title":    title,
            "link":     link,
            "category": cat,
            "date":     to_iso(text(it, "pubDate")),
            "summary":  body[:SUMMARY_LEN] + ("…" if len(body) > SUMMARY_LEN else ""),
            "tags":     tags[:6],
        })
        if len(items) >= MAX_ITEMS:
            break

    if not items:
        print("경고: 노출 가능한 글이 0건 — 기존 blog-feed.json 을 유지합니다.", file=sys.stderr)
        return 1

    data = {
        "source":       rss_url,
        "blog_url":     home_url,
        "generated_at": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "items":        items,
    }

    # generated_at 만 바뀐 경우엔 파일을 건드리지 않는다(불필요한 커밋 방지)
    if os.path.exists(OUT):
        try:
            old = json.loads(io.open(OUT, encoding="utf-8").read())
            if old.get("items") == items:
                print("변경 없음 — %d건 유지" % len(items))
                return 0
        except Exception:
            pass

    io.open(OUT, "w", encoding="utf-8").write(json.dumps(data, ensure_ascii=False, indent=2))
    print("blog-feed.json 갱신: %d건 노출 · %d건 제외(정치·연예 등)" % (len(items), skipped))
    for i in items[:3]:
        print("  -", i["date"], i["category"], "|", i["title"][:40])
    return 0


if __name__ == "__main__":
    sys.exit(main())
