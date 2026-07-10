# -*- coding: utf-8 -*-
import json, os, html
os.chdir(r'C:\Users\SIMSTER\Desktop\biblynote')
OUT = r'C:\Users\SIMSTER\AppData\Local\Temp\claude\C--Users-SIMSTER-Desktop---\d2164d6a-e1a2-441e-a2ea-afd24e1a8325\scratchpad\matthew-sample.html'

chapters = []
for ch in (1, 2):
    verses = json.load(open(f'bible/en/Matthew-{ch}.json', encoding='utf-8'))
    out = []
    for i, v in enumerate(verses, 1):
        out.append({
            'n': i, 'en': v.get('en',''), 'ko': v.get('ko',''),
            'note': v.get('note',''),
            'voc': v.get('voc') or [], 'idi': v.get('idi') or [], 'gra': v.get('gra') or [],
        })
    chapters.append({'ch': ch, 'verses': out})

DATA = json.dumps(chapters, ensure_ascii=False).replace('</', '<\\/')

CSS = r"""
*{box-sizing:border-box}
:root{
  --paper:#f2efe6; --page:#fbf9f3; --ink:#22304c; --en:#59606f; --accent:#9a7b22;
  --accent2:#c9b06a; --rubric:#8c3a2c; --rule:#e7e1d2; --label:#a89e84; --chip:#efe9da; --chipbd:#e2d9c2;
  --shadow:0 1px 2px rgba(40,32,10,.05),0 12px 34px rgba(40,32,10,.09);
  --fs:1.155rem;
  --ko:"Noto Serif KR","Nanum Myeongjo","Batang",serif;
  --enf:Georgia,"Times New Roman","Nanum Myeongjo",serif;
  --ui:"Pretendard",system-ui,-apple-system,"Malgun Gothic",sans-serif;
}
@media (prefers-color-scheme:dark){:root{
  --paper:#101219; --page:#181b24; --ink:#e9e5d7; --en:#a6adbc; --accent:#cba650;
  --accent2:#8a7534; --rubric:#cf7358; --rule:#2a2e3a; --label:#8b8674;
  --chip:#23262f; --chipbd:#343845; --shadow:0 1px 2px rgba(0,0,0,.3),0 18px 40px rgba(0,0,0,.4);
}}
:root[data-theme="light"]{
  --paper:#f2efe6;--page:#fbf9f3;--ink:#22304c;--en:#59606f;--accent:#9a7b22;--accent2:#c9b06a;
  --rubric:#8c3a2c;--rule:#e7e1d2;--label:#a89e84;--chip:#efe9da;--chipbd:#e2d9c2;
  --shadow:0 1px 2px rgba(40,32,10,.05),0 12px 34px rgba(40,32,10,.09);
}
:root[data-theme="dark"]{
  --paper:#101219;--page:#181b24;--ink:#e9e5d7;--en:#a6adbc;--accent:#cba650;--accent2:#8a7534;
  --rubric:#cf7358;--rule:#2a2e3a;--label:#8b8674;--chip:#23262f;--chipbd:#343845;
  --shadow:0 1px 2px rgba(0,0,0,.3),0 18px 40px rgba(0,0,0,.4);
}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--ko);
  -webkit-font-smoothing:antialiased;line-height:1.6}
.wrap{max-width:860px;margin:0 auto;padding:0 20px 96px}

/* toolbar */
.bar{position:sticky;top:0;z-index:20;display:flex;flex-wrap:wrap;gap:10px 18px;align-items:center;
  padding:11px 20px;margin:0 -20px 0;background:color-mix(in srgb,var(--paper) 88%,transparent);
  backdrop-filter:blur(9px);border-bottom:1px solid var(--rule);font-family:var(--ui)}
.bar .grp{display:flex;gap:4px;align-items:center}
.bar .lab{font-size:11px;letter-spacing:.09em;text-transform:uppercase;color:var(--label);margin-right:4px}
.bar button{font-family:var(--ui);font-size:12.5px;color:var(--en);background:transparent;
  border:1px solid var(--chipbd);border-radius:999px;padding:5px 12px;cursor:pointer;transition:.18s}
.bar button:hover{border-color:var(--accent)}
.bar button[aria-pressed="true"]{background:var(--accent);color:#fff;border-color:var(--accent)}
.bar .sp{flex:1}

/* book */
.book{background:var(--page);margin-top:26px;border:1px solid var(--rule);border-radius:3px;
  box-shadow:var(--shadow);padding:56px clamp(22px,6vw,72px) 72px}
.masthead{text-align:center;padding-bottom:26px;margin-bottom:8px;border-bottom:1px solid var(--rule)}
.eyebrow{font-family:var(--ui);font-size:11.5px;letter-spacing:.34em;text-transform:uppercase;
  color:var(--accent);font-weight:600}
.booktitle{font-family:var(--ko);font-weight:700;font-size:clamp(2.5rem,7vw,3.6rem);margin:.28em 0 .1em;
  letter-spacing:.06em;text-wrap:balance}
.booten{font-family:var(--enf);font-style:italic;font-size:clamp(.85rem,2.4vw,1.02rem);
  letter-spacing:.12em;color:var(--en)}
.blurb{font-family:var(--ui);font-size:12.5px;color:var(--label);margin-top:16px;letter-spacing:.02em}

/* chapter opener */
.chap{text-align:center;margin:52px 0 30px;display:flex;align-items:center;justify-content:center;gap:20px}
.chap::before,.chap::after{content:"";height:1px;width:min(74px,16vw);background:linear-gradient(90deg,transparent,var(--accent2))}
.chap::after{background:linear-gradient(90deg,var(--accent2),transparent)}
.chap .num{font-family:var(--enf);font-size:2.5rem;font-weight:700;color:var(--accent);line-height:1}
.chap .ko{font-family:var(--ui);font-size:12px;letter-spacing:.3em;color:var(--label);text-transform:uppercase}
.chap .cwrap{display:flex;flex-direction:column;gap:5px;align-items:center}

/* verse */
.v{position:relative;padding-left:2.5rem;margin:0 0 1.15rem}
.vn{position:absolute;left:0;top:.2em;font-family:var(--enf);font-size:.82rem;font-weight:700;
  color:var(--accent);font-variant-numeric:tabular-nums;min-width:2rem}
.vko{font-family:var(--ko);font-size:var(--fs);line-height:1.92;color:var(--ink);letter-spacing:.01em}
.ven{font-family:var(--enf);font-size:calc(var(--fs)*.86);line-height:1.62;color:var(--en);margin-top:.28em}

/* apparatus */
.app{margin:.55rem 0 .2rem;display:none;flex-direction:column;gap:.5rem;
  border-left:2px solid var(--accent2);padding:.5rem 0 .5rem .95rem}
.level-full .app:has(.note),.level-full .app:has(.lex),
.level-note .app:has(.note),.level-note .app:has(.voc){display:flex}
.note,.lex{display:none}
.level-full .note,.level-note .note{display:block}
.level-full .lex.voc,.level-note .lex.voc{display:flex;flex-wrap:wrap}
.level-full .lex.gra{display:block}
.note{font-family:var(--ko);font-size:.9rem;line-height:1.72;color:var(--en)}
.note .tag,.lex .tag{font-family:var(--ui);font-size:10px;font-weight:700;letter-spacing:.13em;
  text-transform:uppercase;color:var(--accent);margin-right:.5em;vertical-align:.08em}
.lex{font-family:var(--ui);font-size:.8rem;line-height:1.55;color:var(--en);gap:5px 7px;align-items:baseline}
.chip{background:var(--chip);border:1px solid var(--chipbd);border-radius:5px;padding:2.5px 8px;white-space:nowrap}
.chip i{font-family:var(--enf);font-style:italic;color:var(--ink);font-weight:600}
.chip em{font-style:normal;color:var(--label);font-size:.86em;margin:0 3px}
.gra{margin-top:.3rem}
.gra .row{margin-top:.2rem}
.gra b{font-family:var(--enf);color:var(--ink);font-weight:700}

/* parallel mode */
.mode-parallel .book{max-width:none}
.mode-parallel .v{padding-left:0;display:grid;grid-template-columns:2rem minmax(0,1fr) minmax(0,1fr);
  column-gap:2.2rem;row-gap:.15rem;align-items:start}
.mode-parallel .vn{position:static;grid-column:1;grid-row:1;text-align:right;padding-top:.28em}
.mode-parallel .vko{grid-column:2}
.mode-parallel .ven{grid-column:3;margin-top:0;padding-top:.02em}
.mode-parallel .app{grid-column:1/-1;margin-left:0}
@media(max-width:680px){
  .mode-parallel .v{grid-template-columns:1.6rem 1fr;}
  .mode-parallel .ven{grid-column:2}
}
.wrap.mode-parallel{max-width:1120px}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
button:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
"""

def esc(s): return html.escape(str(s), quote=False)

HTML = f"""<title>마태복음 KJV 영한대역 샘플 (1–2장)</title>
<style>{CSS}</style>
<div class="wrap mode-stack level-full" id="wrap">
  <div class="bar">
    <div class="grp"><span class="lab">판형</span>
      <button id="m-stack" aria-pressed="true" onclick="setMode('stack')">상하 대역</button>
      <button id="m-par" aria-pressed="false" onclick="setMode('parallel')">좌우 2단</button>
    </div>
    <div class="grp"><span class="lab">부속</span>
      <button id="lv-full" aria-pressed="true" onclick="setLevel('full')">풀 스터디</button>
      <button id="lv-note" aria-pressed="false" onclick="setLevel('note')">주해 중심</button>
      <button id="lv-plain" aria-pressed="false" onclick="setLevel('plain')">대역 위주</button>
    </div>
    <div class="sp"></div>
    <div class="grp"><span class="lab">크기</span>
      <button onclick="fs(-1)">A-</button><button onclick="fs(1)">A+</button>
    </div>
  </div>

  <div class="book" id="book">
    <div class="masthead">
      <div class="eyebrow">KJV 새번역 · 영한대역 스터디 바이블</div>
      <h1 class="booktitle">마태복음</h1>
      <div class="booten">The Gospel According to St. Matthew</div>
      <div class="blurb">흠정역(KJV) 본문 · 새로운 우리말 번역 · 절별 주해와 원어 어휘 · KJV 어법 풀이</div>
    </div>
    <div id="text"></div>
  </div>
</div>

<script>
const DATA = {DATA};
function chipVoc(voc){{
  if(!voc||!voc.length) return '';
  const c = voc.map(w=>`<span class="chip"><i>${{esc(w[0])}}</i>${{w[1]?`<em>${{esc(w[1])}}</em>`:' '}}${{esc(w[2]||'')}}</span>`).join('');
  return `<div class="lex voc"><span class="tag">어휘</span>${{c}}</div>`;
}}
function graBlock(idi,gra){{
  const rows=[];
  (idi||[]).forEach(x=>rows.push(`<div class="row"><b>${{esc(x[0])}}</b> — ${{esc(x[1])}}</div>`));
  (gra||[]).forEach(x=>rows.push(`<div class="row"><b>${{esc(x[0])}}</b> — ${{esc(x[1])}}</div>`));
  if(!rows.length) return '';
  return `<div class="lex gra"><span class="tag">KJV 어법</span>${{rows.join('')}}</div>`;
}}
function esc(s){{return String(s==null?'':s).replace(/[&<>]/g,m=>({{'&':'&amp;','<':'&lt;','>':'&gt;'}}[m]));}}
function render(){{
  let h='';
  for(const c of DATA){{
    h+=`<div class="chap"><div class="cwrap"><span class="num">${{c.ch}}</span><span class="ko">제 ${{c.ch}} 장</span></div></div>`;
    for(const v of c.verses){{
      const lex = chipVoc(v.voc)+graBlock(v.idi,v.gra);
      const note = v.note?`<div class="note"><span class="tag">주해</span>${{esc(v.note)}}</div>`:'';
      const app = (note||lex)?`<div class="app">${{note}}${{lex}}</div>`:'';
      h+=`<div class="v"><span class="vn">${{v.ch||''}}${{v.n}}</span>`+
         `<div class="vko">${{esc(v.ko)}}</div><div class="ven">${{esc(v.en)}}</div>${{app}}</div>`;
    }}
  }}
  document.getElementById('text').innerHTML=h;
}}
const wrap=document.getElementById('wrap');
function setMode(m){{
  wrap.classList.toggle('mode-parallel',m==='parallel');
  wrap.classList.toggle('mode-stack',m==='stack');
  document.getElementById('m-stack').setAttribute('aria-pressed',m==='stack');
  document.getElementById('m-par').setAttribute('aria-pressed',m==='parallel');
}}
function setLevel(lv){{
  ['full','note','plain'].forEach(x=>{{
    wrap.classList.toggle('level-'+x, x===lv);
    document.getElementById('lv-'+x).setAttribute('aria-pressed', x===lv);
  }});
}}
let curfs=1.155;
function fs(d){{curfs=Math.max(.95,Math.min(1.5,curfs+d*.06));document.getElementById('book').style.setProperty('--fs',curfs+'rem');}}
render();
</script>
"""

open(OUT, 'w', encoding='utf-8').write(HTML)
print('생성:', OUT, round(os.path.getsize(OUT)/1024,1), 'KB')
