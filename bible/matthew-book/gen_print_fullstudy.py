# -*- coding: utf-8 -*-
# 마태복음 영한대역 인쇄용 조판 (신국판 152x225mm, 풀 스터디, 상하 대역)
import json, os, html
os.chdir(r'C:\Users\SIMSTER\Desktop\biblynote')
OUT = r'C:\Users\SIMSTER\AppData\Local\Temp\claude\C--Users-SIMSTER-Desktop---\d2164d6a-e1a2-441e-a2ea-afd24e1a8325\scratchpad\matthew-print.html'

def esc(s): return html.escape(str(s or ''), quote=False)

def voc_html(voc):
    if not voc: return ''
    items = ' · '.join(f'<i>{esc(w[0])}</i>{(" "+esc(w[1])) if w[1] else ""} {esc(w[2])}' for w in voc)
    return f'<div class="ap voc"><span class="apl">어휘</span>{items}</div>'

def gra_html(idi, gra):
    rows = []
    for x in (idi or []): rows.append(f'<b>{esc(x[0])}</b> {esc(x[1])}')
    for x in (gra or []): rows.append(f'<b>{esc(x[0])}</b> {esc(x[1])}')
    if not rows: return ''
    return '<div class="ap gra"><span class="apl">KJV 어법</span>' + ' · '.join(rows) + '</div>'

body = []
for ch in (1, 2):
    verses = json.load(open(f'bible/en/Matthew-{ch}.json', encoding='utf-8'))
    body.append(f'<div class="chap"><div class="chnum">{ch}</div><div class="chko">제 {ch} 장</div></div>')
    for i, v in enumerate(verses, 1):
        note = f'<div class="ap note"><span class="apl">주해</span>{esc(v.get("note"))}</div>' if v.get('note') else ''
        ap = note + voc_html(v.get('voc')) + gra_html(v.get('idi'), v.get('gra'))
        apbox = f'<div class="apbox">{ap}</div>' if ap else ''
        body.append(
            f'<div class="v"><span class="vn">{i}</span>'
            f'<span class="ko">{esc(v.get("ko"))}</span>'
            f'<span class="en">{esc(v.get("en"))}</span>{apbox}</div>')

BODY = '\n'.join(body)

CSS = r"""
@page{ size:152mm 225mm; margin:16mm 15mm 16mm; }
@page:first{ margin:0; }
*{box-sizing:border-box}
:root{
  --ink:#1f2c46; --en:#5a6273; --accent:#977824; --accent2:#c2a24a; --rule:#e6dfcf;
  --note:#4c525f; --label:#9a8f74; --paper:#fdfbf5;
}
html{background:#8a8a8a}
body{margin:0;background:var(--paper);color:var(--ink);
  font-family:"Noto Serif KR","Nanum Myeongjo","Batang",serif;line-height:1.62;
  font-size:10.2pt;-webkit-print-color-adjust:exact;print-color-adjust:exact}

/* 표제지 */
.title{page-break-after:always;height:225mm;display:flex;flex-direction:column;
  align-items:center;justify-content:center;text-align:center;background:var(--paper);
  border:0;position:relative}
.title .rule{width:44mm;height:2px;background:linear-gradient(90deg,transparent,var(--accent),transparent);margin:7mm 0}
.title .series{font-family:"Pretendard",system-ui,sans-serif;font-size:9pt;letter-spacing:.42em;
  text-transform:uppercase;color:var(--accent);font-weight:600}
.title h1{font-size:44pt;font-weight:700;letter-spacing:.08em;margin:6mm 0 3mm}
.title .en{font-style:italic;font-size:14pt;color:var(--en);font-family:Georgia,serif;letter-spacing:.06em}
.title .foot{position:absolute;bottom:22mm;font-family:"Pretendard",system-ui,sans-serif;
  font-size:8.5pt;color:var(--label);letter-spacing:.06em;line-height:1.9}
.title .kjvmark{font-family:Georgia,serif;font-size:10pt;color:var(--accent);letter-spacing:.1em}

/* 장 */
.chap{text-align:center;margin:9mm 0 5mm;break-after:avoid}
.chap .chnum{font-family:Georgia,serif;font-size:26pt;font-weight:700;color:var(--accent);line-height:1}
.chap .chko{font-family:"Pretendard",system-ui,sans-serif;font-size:8pt;letter-spacing:.34em;
  color:var(--label);text-transform:uppercase;margin-top:1.5mm}

/* 절 */
.v{position:relative;padding-left:6.5mm;margin-bottom:2.6mm;break-inside:avoid}
.vn{position:absolute;left:0;top:.15em;font-family:Georgia,serif;font-size:7.6pt;font-weight:700;
  color:var(--accent);font-variant-numeric:tabular-nums}
.ko{display:block;font-size:10.6pt;line-height:1.72;color:var(--ink)}
.en{display:block;font-family:Georgia,"Times New Roman",serif;font-size:9pt;line-height:1.5;
  color:var(--en);margin-top:.6mm}

/* 부속 */
.apbox{margin:1.4mm 0 0;padding-left:3mm;border-left:1.5px solid var(--accent2)}
.ap{font-size:8.2pt;line-height:1.52;color:var(--note);margin-top:1mm;
  font-family:"Pretendard",system-ui,"Nanum Myeongjo",sans-serif}
.ap.note{font-family:"Noto Serif KR","Nanum Myeongjo",serif}
.apl{font-family:"Pretendard",system-ui,sans-serif;font-size:6.6pt;font-weight:700;letter-spacing:.11em;
  text-transform:uppercase;color:var(--accent);margin-right:.5em;vertical-align:.1em}
.ap i{font-family:Georgia,serif;font-style:italic;font-weight:600;color:var(--ink)}
.ap.gra b,.ap.voc i{white-space:nowrap}
.ap b{font-family:Georgia,serif;font-weight:700;color:var(--ink)}

/* 러닝 헤더/풋터 (매 페이지 반복) */
.rhead{position:fixed;top:6mm;left:0;right:0;text-align:center;
  font-family:"Pretendard",system-ui,sans-serif;font-size:7.5pt;letter-spacing:.3em;
  color:var(--label);text-transform:uppercase}
.rfoot{position:fixed;bottom:6mm;left:0;right:0;text-align:center;color:var(--accent2);font-size:9pt}
"""

HTML = f"""<title>마태복음 KJV 영한대역 · 인쇄 조판 샘플</title>
<style>{CSS}</style>
<div class="rhead">마태복음 · The Gospel of Matthew</div>
<div class="rfoot">✦</div>

<section class="title">
  <div class="series">정본역 킹제임스 성경 · 영한대역 스터디 바이블</div>
  <div class="rule"></div>
  <h1>마태복음</h1>
  <div class="en">The Gospel According to St. Matthew</div>
  <div class="foot">
    <div class="kjvmark">KING JAMES VERSION</div>
    흠정역(KJV) 본문 · 새로운 우리말 번역<br/>절별 주해 · 원어 어휘 · KJV 고어 어법 풀이
  </div>
</section>

<div class="text">
{BODY}
</div>
"""
open(OUT, 'w', encoding='utf-8').write(HTML)
print('생성:', OUT, round(os.path.getsize(OUT)/1024,1), 'KB')
