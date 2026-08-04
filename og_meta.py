# -*- coding: utf-8 -*-
"""Insert OG/Twitter/canonical meta into pages missing them."""
import io, os

IMG = "https://biblynote.com/images/og-cover.png?v=7"
SITE = "BIBLY 바이블 인사이트"
ANCHOR = '<link rel="icon" href="/favicon.ico" sizes="any" />'

pages = {
  "community.html":  ("질문·나눔·기도요청 — BIBLY 바이블 인사이트",
                      "성경·신앙·삶의 질문을 나누고 함께 답을 찾는 커뮤니티 · 자유게시판 · 기도요청.",
                      "https://biblynote.com/community"),
  "find.html":       ("나에게 맞는 강의 찾기 — BIBLY 바이블 인사이트",
                      "7문항 진단으로 나에게 꼭 맞는 강의와 학습 순서를 추천해 드려요.",
                      "https://biblynote.com/find"),
  "mylearning.html": ("내 강의실 — BIBLY 바이블 인사이트",
                      "수강 신청한 강의의 학습 현황과 진도를 한눈에 확인하세요.",
                      "https://biblynote.com/mylearning"),
  "resources.html":  ("자료실 — BIBLY 바이블 인사이트",
                      "암송노트·강의노트·도표 등 강의와 함께 보는 학습 자료실.",
                      "https://biblynote.com/resources"),
  "request.html":    ("강의 요청·건의함 — BIBLY 바이블 인사이트",
                      "듣고 싶은 강의를 신청하고, 사이트·강의에 대한 건의·피드백을 남겨주세요.",
                      "https://biblynote.com/request"),
  "column.html":     ("오광일 칼럼 — BIBLY 바이블 인사이트",
                      "오광일이 전하는 성경과 시대를 읽는 칼럼.",
                      "https://biblynote.com/column"),
  "bible.html":      ("성경 읽기 — BIBLY 바이블 인사이트",
                      "온라인으로 성경을 편하게 읽어보세요. BIBLY 바이블 인사이트.",
                      "https://biblynote.com/bible"),
  "support.html":    ("후원 안내 — BIBLY 바이블 인사이트",
                      "광고·협찬 없이 여러분의 후원으로 이어지는 100% 무료 사역에 함께해 주세요.",
                      "https://biblynote.com/support"),
}

def block(title, desc, url):
    e = lambda s: s.replace('&','&amp;').replace('"','&quot;')
    t, d = e(title), e(desc)
    return (
      '\n  <link rel="canonical" href="%s" />' % url +
      '\n  <meta property="og:type" content="website" />' +
      '\n  <meta property="og:site_name" content="%s" />' % SITE +
      '\n  <meta property="og:title" content="%s" />' % t +
      '\n  <meta property="og:description" content="%s" />' % d +
      '\n  <meta property="og:url" content="%s" />' % url +
      '\n  <meta property="og:image" content="%s" />' % IMG +
      '\n  <meta name="twitter:card" content="summary_large_image" />' +
      '\n  <meta name="twitter:title" content="%s" />' % t +
      '\n  <meta name="twitter:description" content="%s" />' % d +
      '\n  <meta name="twitter:image" content="%s" />' % IMG
    )

log = []
for fn, (title, desc, url) in pages.items():
    if not os.path.exists(fn):
        log.append("%s : (없음)" % fn); continue
    raw = io.open(fn, encoding="utf-8").read()
    if 'og:title' in raw:
        log.append("%s : 이미 있음(skip)" % fn); continue
    if ANCHOR not in raw:
        log.append("%s : 앵커 없음(skip)" % fn); continue
    raw = raw.replace(ANCHOR, ANCHOR + block(title, desc, url), 1)
    io.open(fn, "w", encoding="utf-8", newline="").write(raw)
    log.append("%s : OG 추가" % fn)

io.open("_og_log.txt", "w", encoding="utf-8").write("\n".join(log))
