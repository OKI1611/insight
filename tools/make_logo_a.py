# -*- coding: utf-8 -*-
"""
바이블 인사이트 로고 A안(열린 책 · 한 점의 빛) 자산 생성기 — 2026-11-09
  헤드리스 크롬으로 HTML 템플릿을 정확한 픽셀 크기로 렌더링한다(투명 배경 PNG).
  사용: python -X utf8 tools/make_logo_a.py  (insight 루트 어디서 실행해도 됨)
산출물
  images/logo-heritage-wide.png (헤더 록업, 남색·투명)  / logo-heritage-wide-dark.png (흰색·투명)
  images/logo-heritage-square.png (512, JSON-LD)
  images/icon-192.png · icon-512.png · icon-maskable-512.png · apple-touch-icon.png
  images/favicon-16/32/48.png · favicon.png(64) · /favicon.svg · /favicon.ico
  images/bible-insight-emblem.png (남색 심볼·투명) · bible-insight-emblem-white.png
  images/og-cover.png (1200×630)
  <산출물 폴더>/play-icon-512.png (불투명) · feature-graphic-1024x500.png · brand-mark.svg · lockup.svg
"""
import io, os, sys, subprocess, tempfile, shutil
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, "images")
OUT_STORE = r"C:\Users\오광일\OneDrive\바탕 화면\홈페이지 제작\로고 리디자인 제안\산출물"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

NAVY, NAVY2, LIGHT = "#1E3A68", "#2A4F8C", "#FFFFFF"
FONT_LINK = '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Manrope:wght@700;800&family=Noto+Sans+KR:wght@500;600;700&display=swap">'

def mark(color, size, extra=""):
    """열린 책 + 점 — viewBox 0 0 100 100 (제안 페이지 mk-a 와 동일 경로)"""
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 100 100" {extra}>'
            f'<g fill="none" stroke="{color}" stroke-width="6.5" stroke-linecap="round" stroke-linejoin="round">'
            f'<path d="M50 40C42 31 30 29 18 31V72C30 70 42 72 50 80"/><path d="M50 40C58 31 70 29 82 31V72C70 70 58 72 50 80"/><path d="M50 40V80"/></g>'
            f'<circle cx="50" cy="19" r="5.5" fill="{color}"/></svg>')

def page(w, h, body, bg="transparent"):
    return f"""<!doctype html><html><head><meta charset="utf-8">{FONT_LINK}<style>
html,body{{margin:0;padding:0;width:{w}px;height:{h}px;overflow:hidden;background:{bg}}}
body{{font-family:'Manrope','Noto Sans KR',sans-serif;-webkit-font-smoothing:antialiased}}
.ko{{font-family:'Noto Sans KR','Malgun Gothic',sans-serif}}
</style></head><body>{body}</body></html>"""

def lockup(color, mark_px, en_px, ko_px, gap):
    sub = "rgba(255,255,255,.78)" if color == LIGHT else "rgba(30,58,104,.78)"
    return (f'<div style="display:flex;align-items:center;gap:{gap}px;height:100%">{mark(color, mark_px)}'
            f'<div style="display:grid;gap:{round(en_px*0.07)}px;line-height:1.05">'
            f'<div style="font-weight:800;font-size:{en_px}px;letter-spacing:-0.022em;color:{color};white-space:nowrap">Bible Insight</div>'
            f'<div class="ko" style="font-weight:600;font-size:{ko_px}px;letter-spacing:.2em;color:{sub};white-space:nowrap">바이블 인사이트</div></div></div>')

def tile(size, mark_ratio=0.62, radius=0):
    r = f"border-radius:{radius}px;" if radius else ""
    return (f'<div style="width:{size}px;height:{size}px;{r}background:linear-gradient(160deg,{NAVY2},{NAVY});display:grid;place-items:center">'
            f'{mark(LIGHT, round(size*mark_ratio))}</div>')

def render(html, w, h, out):
    if os.path.exists(out): os.remove(out)      # 크롬 --screenshot 은 기존 파일을 덮어쓰지 않는다
    d = tempfile.mkdtemp()
    p = os.path.join(d, "t.html")
    io.open(p, "w", encoding="utf-8").write(html)
    cmd = [CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
           "--default-background-color=00000000", "--virtual-time-budget=8000",
           f"--window-size={w},{h}", f"--screenshot={out}", "file:///" + p.replace("\\", "/")]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=90)
    shutil.rmtree(d, ignore_errors=True)
    im = Image.open(out); assert im.size == (w, h), (out, im.size)
    return im

def main():
    os.makedirs(OUT_STORE, exist_ok=True)
    J = lambda *a: os.path.join(*a)
    # ── 1. 헤더 록업(투명) 남색 / 흰색 ──
    render(page(1200, 260, lockup(NAVY, 220, 118, 40, 34)), 1200, 260, J(IMG, "logo-heritage-wide.png"))
    render(page(1200, 260, lockup(LIGHT, 220, 118, 40, 34)), 1200, 260, J(IMG, "logo-heritage-wide-dark.png"))
    # ── 2. 정사각 512(JSON-LD) / 앱·PWA 아이콘 ──
    sq = render(page(512, 512, tile(512)), 512, 512, J(IMG, "logo-heritage-square.png"))
    sq.convert("RGB").save(J(IMG, "logo-heritage-square.png"))
    render(page(512, 512, tile(512)), 512, 512, J(IMG, "icon-512.png"))
    render(page(512, 512, tile(512, mark_ratio=0.50)), 512, 512, J(IMG, "icon-maskable-512.png"))   # 안전영역 80% 안에
    render(page(192, 192, tile(192)), 192, 192, J(IMG, "icon-192.png"))
    render(page(180, 180, tile(180)), 180, 180, J(IMG, "apple-touch-icon.png"))
    # 파비콘은 모서리 둥글게(22%) — 탭에서 사각이 덜 딱딱해 보인다
    for s in (64, 48, 32, 16):
        name = "favicon.png" if s == 64 else f"favicon-{s}.png"
        render(page(s, s, tile(s, radius=round(s*0.22))), s, s, J(IMG, name))
    ico = [Image.open(J(IMG, f"favicon-{s}.png")) for s in (16, 32, 48)]
    ico[2].save(J(ROOT, "favicon.ico"), format="ICO", sizes=[(16, 16), (32, 32), (48, 48)], append_images=ico[:2])
    io.open(J(ROOT, "favicon.svg"), "w", encoding="utf-8").write(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" role="img" aria-label="Bible Insight">'
        f'<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{NAVY2}"/><stop offset="1" stop-color="{NAVY}"/></linearGradient></defs>'
        '<rect width="100" height="100" rx="22" fill="url(#g)"/>'
        '<g transform="translate(19 19) scale(.62)"><g fill="none" stroke="#fff" stroke-width="6.5" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M50 40C42 31 30 29 18 31V72C30 70 42 72 50 80"/><path d="M50 40C58 31 70 29 82 31V72C70 70 58 72 50 80"/><path d="M50 40V80"/></g>'
        '<circle cx="50" cy="19" r="5.5" fill="#fff"/></g></svg>')
    # ── 3. 엠블럼(심볼 단독·투명) ──
    render(page(256, 256, mark(NAVY, 256)), 256, 256, J(IMG, "bible-insight-emblem.png"))
    render(page(256, 256, mark(LIGHT, 256)), 256, 256, J(IMG, "bible-insight-emblem-white.png"))
    # ── 4. 공유 카드 og 1200×630 ──
    og = (f'<div style="width:1200px;height:630px;background:linear-gradient(135deg,{NAVY2} 0%,{NAVY} 55%,#16305A 100%);'
          f'display:flex;flex-direction:column;justify-content:center;padding:0 96px;box-sizing:border-box;color:#fff">'
          f'<div style="height:170px">{lockup(LIGHT, 170, 96, 32, 30)}</div>'
          f'<div class="ko" style="margin-top:54px;font-size:40px;font-weight:700;letter-spacing:-.01em;line-height:1.35">보는 신앙에서, 스스로 읽고 분별하는 신앙으로</div>'
          f'<div class="ko" style="margin-top:14px;font-size:26px;font-weight:500;color:rgba(255,255,255,.72);letter-spacing:.01em">강의 · 성경 읽기 · 성경사전 · 질문과 답, 모두 무료 &nbsp;·&nbsp; biblynote.com</div></div>')
    render(page(1200, 630, og), 1200, 630, J(IMG, "og-cover.png")).convert("RGB").save(J(IMG, "og-cover.png"))
    # ── 5. 스토어 자산(저장소 밖) ──
    render(page(512, 512, tile(512)), 512, 512, J(OUT_STORE, "play-icon-512.png")).convert("RGB").save(J(OUT_STORE, "play-icon-512.png"))
    fg = (f'<div style="width:1024px;height:500px;background:linear-gradient(135deg,{NAVY2},{NAVY} 60%,#16305A);display:flex;align-items:center;gap:56px;padding:0 84px;box-sizing:border-box;color:#fff">'
          f'{mark(LIGHT, 250)}<div><div style="font-weight:800;font-size:96px;letter-spacing:-.022em;line-height:1">Bible Insight</div>'
          f'<div class="ko" style="font-weight:600;font-size:34px;letter-spacing:.2em;color:rgba(255,255,255,.78);margin-top:14px">바이블 인사이트</div>'
          f'<div class="ko" style="font-weight:500;font-size:28px;color:rgba(255,255,255,.85);margin-top:34px">성경을 스스로 읽는 사람들의 학교</div></div></div>')
    render(page(1024, 500, fg), 1024, 500, J(OUT_STORE, "feature-graphic-1024x500.png")).convert("RGB").save(J(OUT_STORE, "feature-graphic-1024x500.png"))
    shutil.copy(J(ROOT, "favicon.svg"), J(OUT_STORE, "app-icon.svg"))
    io.open(J(OUT_STORE, "brand-mark.svg"), "w", encoding="utf-8").write(mark(NAVY, 512, 'xmlns="http://www.w3.org/2000/svg"'))
    for f in ("logo-heritage-wide.png", "logo-heritage-wide-dark.png", "icon-512.png", "og-cover.png"):
        shutil.copy(J(IMG, f), J(OUT_STORE, f))
    # ── 검수용 합성 시트 ──
    sheet = Image.new("RGB", (1240, 1000), "#EEF1F5")
    sheet.paste(Image.open(J(IMG, "logo-heritage-wide.png")).resize((620, 134)), (20, 20), Image.open(J(IMG, "logo-heritage-wide.png")).resize((620, 134)))
    dark = Image.new("RGB", (620, 134), NAVY); d = Image.open(J(IMG, "logo-heritage-wide-dark.png")).resize((620, 134)); dark.paste(d, (0, 0), d); sheet.paste(dark, (20, 170))
    x = 20
    for f, s in (("icon-512.png", 200), ("icon-maskable-512.png", 200), ("apple-touch-icon.png", 180), ("icon-192.png", 192), ("favicon.png", 64), ("favicon-48.png", 48), ("favicon-32.png", 32), ("favicon-16.png", 16)):
        im = Image.open(J(IMG, f)).convert("RGBA").resize((s, s)); sheet.paste(im, (x, 330), im); x += s + 16
    e = Image.open(J(IMG, "bible-insight-emblem.png")).resize((120, 120)); sheet.paste(e, (20, 560), e)
    nav = Image.new("RGB", (120, 120), NAVY); ew = Image.open(J(IMG, "bible-insight-emblem-white.png")).resize((120, 120)); nav.paste(ew, (0, 0), ew); sheet.paste(nav, (160, 560))
    sheet.paste(Image.open(J(IMG, "og-cover.png")).resize((600, 315)), (300, 560))
    sheet.paste(Image.open(J(OUT_STORE, "feature-graphic-1024x500.png")).resize((300, 146)), (920, 560))
    sheet.save(J(OUT_STORE, "_검수시트.png"))
    print("done →", OUT_STORE)

if __name__ == "__main__":
    main()
