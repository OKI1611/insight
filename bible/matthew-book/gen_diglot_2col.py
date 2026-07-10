# -*- coding: utf-8 -*-
# 마태복음 2단 영한대역 + 하단 절별 영단어 정리 (깔끔 버전)
import json, os, html
os.chdir(r'C:\Users\SIMSTER\Desktop\biblynote')
OUT = r'C:\Users\SIMSTER\AppData\Local\Temp\claude\C--Users-SIMSTER-Desktop---\d2164d6a-e1a2-441e-a2ea-afd24e1a8325\scratchpad\matthew-diglot.html'
def esc(s): return html.escape(str(s or ''), quote=False)

sections = []
for ch in (1, 2):
    verses = json.load(open(f'bible/en/Matthew-{ch}.json', encoding='utf-8'))
    rows = [f'<div class="chap"><div class="cwrap"><span class="num">{ch}</span><span class="ko">제 {ch} 장</span></div></div>']
    voclines = []
    for i, v in enumerate(verses, 1):
        rows.append(
            f'<div class="v"><span class="vn">{i}</span>'
            f'<div class="vko">{esc(v.get("ko"))}</div>'
            f'<div class="ven">{esc(v.get("en"))}</div></div>')
        voc = v.get('voc') or []
        if voc:
            words = ' <span class="dot">·</span> '.join(
                f'<i>{esc(w[0])}</i>{f" <span class=pos>{esc(w[1])}</span>" if w[1] else ""} {esc(w[2])}'
                for w in voc)
            voclines.append(f'<div class="vlrow"><span class="vln">{i}</span><span class="vlwords">{words}</span></div>')
    voc_block = ''
    if voclines:
        voc_block = ('<div class="voclist"><div class="vlhead">어휘 · Vocabulary'
                     f' <span class="vlch">마태복음 {ch}장</span></div>'
                     '<div class="vlgrid">' + ''.join(voclines) + '</div></div>')
    sections.append(''.join(rows) + voc_block)
BODY = '\n'.join(sections)

CSS = r"""
*{box-sizing:border-box}
:root{
  --paper:#f2efe6;--page:#fbf9f3;--ink:#22304c;--en:#59606f;--accent:#9a7b22;--accent2:#c9b06a;
  --rule:#e7e1d2;--label:#a89e84;--fs:1.16rem;
  --ko:"Noto Serif KR","Nanum Myeongjo","Batang",serif;
  --enf:Georgia,"Times New Roman","Nanum Myeongjo",serif;
  --ui:"Pretendard",system-ui,-apple-system,"Malgun Gothic",sans-serif;
  --shadow:0 1px 2px rgba(40,32,10,.05),0 12px 34px rgba(40,32,10,.09);
}
@media (prefers-color-scheme:dark){:root{
  --paper:#101219;--page:#181b24;--ink:#e9e5d7;--en:#a6adbc;--accent:#cba650;--accent2:#8a7534;
  --rule:#2a2e3a;--label:#8b8674;--shadow:0 1px 2px rgba(0,0,0,.3),0 18px 40px rgba(0,0,0,.4);
}}
:root[data-theme="light"]{--paper:#f2efe6;--page:#fbf9f3;--ink:#22304c;--en:#59606f;--accent:#9a7b22;--accent2:#c9b06a;--rule:#e7e1d2;--label:#a89e84;--shadow:0 1px 2px rgba(40,32,10,.05),0 12px 34px rgba(40,32,10,.09)}
:root[data-theme="dark"]{--paper:#101219;--page:#181b24;--ink:#e9e5d7;--en:#a6adbc;--accent:#cba650;--accent2:#8a7534;--rule:#2a2e3a;--label:#8b8674;--shadow:0 1px 2px rgba(0,0,0,.3),0 18px 40px rgba(0,0,0,.4)}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--ko);
  -webkit-font-smoothing:antialiased;line-height:1.6}
.wrap{max-width:1040px;margin:0 auto;padding:0 20px 90px}
.bar{position:sticky;top:0;z-index:20;display:flex;gap:16px;align-items:center;justify-content:flex-end;
  padding:10px 20px;margin:0 -20px;background:color-mix(in srgb,var(--paper) 88%,transparent);
  backdrop-filter:blur(9px);border-bottom:1px solid var(--rule);font-family:var(--ui)}
.bar .lab{font-size:11px;letter-spacing:.09em;text-transform:uppercase;color:var(--label);margin-right:2px}
.bar button{font-family:var(--ui);font-size:12.5px;color:var(--en);background:transparent;
  border:1px solid var(--accent2);border-radius:999px;padding:5px 12px;cursor:pointer}
.bar button:hover{border-color:var(--accent);color:var(--accent)}
button:focus-visible{outline:2px solid var(--accent);outline-offset:2px}

.book{background:var(--page);margin-top:24px;border:1px solid var(--rule);border-radius:3px;
  box-shadow:var(--shadow);padding:54px clamp(22px,5vw,64px) 66px}
.masthead{text-align:center;padding-bottom:24px;margin-bottom:8px;border-bottom:1px solid var(--rule)}
.eyebrow{font-family:var(--ui);font-size:11.5px;letter-spacing:.34em;text-transform:uppercase;color:var(--accent);font-weight:600}
.booktitle{font-weight:700;font-size:clamp(2.4rem,7vw,3.5rem);margin:.28em 0 .1em;letter-spacing:.06em;text-wrap:balance}
.booten{font-family:var(--enf);font-style:italic;font-size:clamp(.85rem,2.4vw,1.02rem);letter-spacing:.12em;color:var(--en)}
.blurb{font-family:var(--ui);font-size:12.5px;color:var(--label);margin-top:15px}

.chap{text-align:center;margin:50px 0 30px;display:flex;align-items:center;justify-content:center;gap:20px}
.chap::before,.chap::after{content:"";height:1px;width:min(78px,16vw);background:linear-gradient(90deg,transparent,var(--accent2))}
.chap::after{background:linear-gradient(90deg,var(--accent2),transparent)}
.chap .cwrap{display:flex;flex-direction:column;gap:5px;align-items:center}
.chap .num{font-family:var(--enf);font-size:2.5rem;font-weight:700;color:var(--accent);line-height:1}
.chap .ko{font-family:var(--ui);font-size:12px;letter-spacing:.3em;color:var(--label);text-transform:uppercase}

/* 2단 대역 */
.v{display:grid;grid-template-columns:2rem minmax(0,1fr) minmax(0,1fr);column-gap:2.4rem;row-gap:.15rem;
  align-items:start;margin-bottom:1.05rem}
.vn{grid-column:1;text-align:right;padding-top:.3em;font-family:var(--enf);font-size:.82rem;font-weight:700;
  color:var(--accent);font-variant-numeric:tabular-nums}
.vko{grid-column:2;font-family:var(--ko);font-size:var(--fs);line-height:1.9;color:var(--ink);letter-spacing:.01em}
.ven{grid-column:3;font-family:var(--enf);font-size:calc(var(--fs)*.87);line-height:1.6;color:var(--en);padding-top:.03em}
@media(max-width:700px){
  .v{grid-template-columns:1.6rem 1fr;row-gap:.3rem}
  .ven{grid-column:2;padding-top:.1em}
}

/* 하단 절별 어휘 */
.voclist{margin:42px 0 8px;padding:26px clamp(16px,3vw,30px);background:color-mix(in srgb,var(--accent2) 8%,var(--page));
  border:1px solid var(--rule);border-radius:8px}
.vlhead{font-family:var(--ui);font-size:11px;letter-spacing:.26em;text-transform:uppercase;color:var(--accent);
  font-weight:700;margin-bottom:16px;display:flex;align-items:center;gap:10px}
.vlhead::after{content:"";flex:1;height:1px;background:var(--rule)}
.vlhead .vlch{font-family:var(--ko);letter-spacing:.02em;text-transform:none;color:var(--label);font-weight:500;font-size:12px}
.vlgrid{display:grid;grid-template-columns:1fr 1fr;gap:.35rem 2.6rem}
@media(max-width:700px){.vlgrid{grid-template-columns:1fr}}
.vlrow{display:grid;grid-template-columns:1.5rem 1fr;gap:.7rem;font-size:.86rem;line-height:1.7;
  padding:.15rem 0;border-bottom:1px dotted color-mix(in srgb,var(--accent2) 40%,transparent)}
.vln{text-align:right;font-family:var(--enf);font-weight:700;font-size:.76rem;color:var(--accent);padding-top:.18em}
.vlwords{font-family:var(--ui);color:var(--en)}
.vlwords i{font-family:var(--enf);font-style:italic;font-weight:600;color:var(--ink)}
.vlwords .pos{color:var(--label);font-size:.82em;margin:0 .1em}
.vlwords .dot{color:var(--accent2);margin:0 .1em}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
"""

HTML = f"""<title>마태복음 2단 영한대역 + 절별 단어</title>
<style>{CSS}</style>
<div class="wrap" id="wrap">
  <div class="bar">
    <span class="lab">글자 크기</span>
    <button onclick="fs(-1)">A−</button><button onclick="fs(1)">A+</button>
  </div>
  <div class="book" id="book">
    <div class="masthead">
      <div class="eyebrow">KJV 새번역 · 영한대역</div>
      <h1 class="booktitle">마태복음</h1>
      <div class="booten">The Gospel According to St. Matthew</div>
      <div class="blurb">흠정역(KJV) 본문 · 새로운 우리말 번역 · 장별 영어 단어 정리</div>
    </div>
    {BODY}
  </div>
</div>
<script>
let f=1.16;
function fs(d){{f=Math.max(.98,Math.min(1.5,f+d*.06));document.getElementById('book').style.setProperty('--fs',f+'rem');}}
</script>
"""
open(OUT, 'w', encoding='utf-8').write(HTML)
print('생성:', OUT, round(os.path.getsize(OUT)/1024,1), 'KB')
