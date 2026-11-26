/* i18n.js — 바이블 인사이트 다국어(한국어 · English · Español · 日本語 · 中文 繁體)
   ─────────────────────────────────────────────────────────────────────────
   - 언어 결정: 주소 ?lang=xx  >  localStorage 'bibly_lang'  >  'ko'
   - <html data-ui="xx" lang="..."> 를 붙인다 → 긴 글은 페이지가 언어별 블록을 직접 갖고 CSS로 고른다
     (예: rapture.html 의 <article class="rp" data-l="en">).
   - 짧은 화면 글자(메뉴·버튼·안내문)는 사전으로 바꾼다:
       /i18n/common.json            ← 모든 페이지 공통(머리글·메뉴·바닥글)
       /i18n/pages/<페이지>.json      ← PAGES 목록에 이름이 있는 페이지만 불러온다
     키 = 화면에 보이는 한국어 그대로(앞뒤 공백 제외), 값 = {en, es, ja, zh}.
     글 안에 태그가 섞인 문장은 요소에 data-i18n="키" 를 달고 값에 HTML 을 넣는다.
   - 사전에 없는 글자는 한국어로 남는다. 기계 번역은 쓰지 않는다(용어 기준: i18n/GLOSSARY.md).
   - 언어 선택 단추: id="biblyLangSlot" 자리(머리글 상단 띠)에 그린다.
   ───────────────────────────────────────────────────────────────────────── */
(function(){
  if(window.__biblyI18n) return;
  var LANGS = [
    { c:'ko', n:'한국어',      b:'KO', h:'ko' },
    { c:'en', n:'English',    b:'EN', h:'en' },
    { c:'es', n:'Español',    b:'ES', h:'es' },
    { c:'ja', n:'日本語',      b:'JA', h:'ja' },
    { c:'zh', n:'中文(繁體)',  b:'中', h:'zh-Hant' }
  ];
  // 사전 파일이 있는 페이지(없는 페이지는 요청하지 않는다)
  var PAGES = [];
  var VER = '20261126a';

  function valid(c){ for(var i=0;i<LANGS.length;i++) if(LANGS[i].c===c) return LANGS[i]; return null; }
  var lang = 'ko';
  try{
    var q = new URLSearchParams(location.search).get('lang');
    if(q && valid(q)){ lang = q; try{ localStorage.setItem('bibly_lang', q); }catch(e){} }
    else { var s = localStorage.getItem('bibly_lang'); if(s && valid(s)) lang = s; }
  }catch(e){}
  var L = valid(lang);
  var root = document.documentElement;
  root.setAttribute('data-ui', lang);
  if(lang !== 'ko') root.setAttribute('lang', L.h);

  var api = window.__biblyI18n = { lang: lang, langs: LANGS, t: function(k){ return k; } };

  // ── 글꼴: 일본어·중국어는 한글 글꼴의 한자 모양 대신 그 나라 글꼴로 ──
  (function(){
    var css = '#biblyLangBtn{display:inline-flex;align-items:center;gap:.35rem;height:26px;padding:0 .6rem;border-radius:999px;border:1px solid rgba(255,255,255,.28);background:rgba(255,255,255,.06);color:inherit;font-size:12px;font-weight:700;white-space:nowrap;cursor:pointer}'
      + '#biblyLangBtn:hover{border-color:rgba(255,255,255,.6)}'
      + '#biblyLangBtn svg{opacity:.85}'
      + '#biblyLangMenu{position:fixed;z-index:2147483000;min-width:12.5rem;background:#fff;border:1px solid rgba(33,58,107,.14);border-radius:14px;box-shadow:0 18px 48px -12px rgba(21,32,58,.35);padding:6px;font-family:Pretendard,system-ui,sans-serif}'
      + '#biblyLangMenu button{display:flex;align-items:center;gap:.7rem;width:100%;min-height:44px;padding:0 .75rem;border-radius:10px;font-size:15px;color:#1f2937;text-align:left;background:none;border:0;cursor:pointer}'
      + '#biblyLangMenu button:hover{background:#eaf0f8}'
      + '#biblyLangMenu button[aria-current="true"]{background:#e6f2ec;color:#00704a;font-weight:800}'
      + '#biblyLangMenu b{display:inline-flex;align-items:center;justify-content:center;width:30px;height:22px;border-radius:6px;background:#182c54;color:#fff;font-size:11px;font-weight:800;letter-spacing:.02em}'
      + '#biblyLangNote{background:#fff8e6;border-bottom:1px solid #f0d58a;color:#4a3b10;font-size:13px;line-height:1.5;padding:.5rem 1rem;text-align:center;font-family:Pretendard,system-ui,sans-serif}'
      + '#biblyLangNote button{margin-left:.6rem;font-weight:800;color:#00704a;background:none;border:0;cursor:pointer;min-height:32px}';
    // 한국어용 줄바꿈(keep-all)은 띄어쓰기가 없는 일본어·중국어에서 문장부호에서만 줄이 바뀌게 만든다
    if(lang === 'ja' || lang === 'zh') css += 'html[data-ui="' + lang + '"] body,html[data-ui="' + lang + '"] body *{word-break:normal!important;line-break:strict}';
    if(lang === 'ja') css += 'html[data-ui="ja"] body,html[data-ui="ja"] body *:not(svg):not(path):not(code){font-family:Pretendard,"Hiragino Sans","Hiragino Kaku Gothic ProN","Yu Gothic UI","Yu Gothic",Meiryo,"Noto Sans JP",sans-serif}';
    if(lang === 'zh') css += 'html[data-ui="zh"] body,html[data-ui="zh"] body *:not(svg):not(path):not(code){font-family:Pretendard,"PingFang TC","Microsoft JhengHei","Noto Sans TC",sans-serif}';
    var st = document.createElement('style'); st.id = 'biblyI18nCss'; st.textContent = css;
    (document.head || root).appendChild(st);
  })();

  // ── 언어 선택 단추 ──
  var GLOBE = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.5 2.6 3.8 5.6 3.8 9s-1.3 6.4-3.8 9c-2.5-2.6-3.8-5.6-3.8-9S9.5 5.6 12 3z"/></svg>';
  var CARET = '<svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" aria-hidden="true"><path d="M6 9l6 6 6-6"/></svg>';
  function closeMenu(){ var m = document.getElementById('biblyLangMenu'); if(m) m.remove(); var b = document.getElementById('biblyLangBtn'); if(b) b.setAttribute('aria-expanded','false'); }
  function choose(c){
    try{ localStorage.setItem('bibly_lang', c); }catch(e){}
    try{
      var u = new URL(location.href);
      if(c === 'ko') u.searchParams.delete('lang'); else u.searchParams.set('lang', c);
      location.replace(u.toString());
    }catch(e){ location.reload(); }
  }
  function openMenu(btn){
    closeMenu();
    var m = document.createElement('div'); m.id = 'biblyLangMenu'; m.setAttribute('role','menu');
    m.innerHTML = LANGS.map(function(x){
      return '<button type="button" role="menuitem" data-c="' + x.c + '" lang="' + x.h + '"' + (x.c === lang ? ' aria-current="true"' : '') + '><b>' + x.b + '</b>' + x.n + '</button>';
    }).join('');
    document.body.appendChild(m);
    var r = btn.getBoundingClientRect(), w = m.offsetWidth;
    var left = Math.min(Math.max(8, r.right - w), window.innerWidth - w - 8);
    m.style.left = left + 'px'; m.style.top = (r.bottom + 6) + 'px';
    btn.setAttribute('aria-expanded','true');
    m.addEventListener('click', function(e){ var b = e.target.closest('button[data-c]'); if(b) choose(b.getAttribute('data-c')); });
    setTimeout(function(){
      document.addEventListener('click', function h(e){ if(!m.contains(e.target) && e.target !== btn){ closeMenu(); document.removeEventListener('click', h, true); } }, true);
    }, 0);
  }
  function mountButtons(){
    var slots = document.querySelectorAll('#biblyLangSlot, .biblyLangSlot');
    for(var i=0;i<slots.length;i++){
      var s = slots[i]; if(s.getAttribute('data-done')) continue;
      s.setAttribute('data-done','1');
      s.innerHTML = '<button id="biblyLangBtn" type="button" aria-haspopup="menu" aria-expanded="false" aria-label="Language / 언어">' + GLOBE + '<span lang="' + L.h + '">' + L.n + '</span>' + CARET + '</button>';
      s.querySelector('button').addEventListener('click', function(e){
        e.stopPropagation();
        if(document.getElementById('biblyLangMenu')) closeMenu(); else openMenu(this);
      });
    }
  }
  window.addEventListener('resize', closeMenu);
  window.addEventListener('scroll', closeMenu, { passive:true });

  // ── 사전 번역(한국어가 아닐 때만) ──
  var DICT = {}, busy = false, pending = [];
  function tr(k){ var e = DICT[k]; return e && e[lang] ? e[lang] : null; }
  api.t = function(k){ return tr(k) || k; };
  function skip(el){
    for(var p = el; p && p.nodeType === 1; p = p.parentNode){
      var n = p.nodeName;
      if(n === 'SCRIPT' || n === 'STYLE' || n === 'TEXTAREA' || n === 'CODE' || n === 'PRE') return true;
      if(p.hasAttribute('data-noi18n') || p.hasAttribute('data-l') || p.isContentEditable) return true;
      if(p.id === 'biblyAuthName' || p.id === 'biblyLangMenu') return true;
    }
    return false;
  }
  var ATTRS = ['placeholder','title','aria-label','alt'];
  function apply(node){
    if(!node) return;
    if(node.nodeType === 3){
      if(node.parentNode && !skip(node.parentNode)){
        var raw = node.nodeValue, k = raw.trim();
        if(k && /[가-힣]/.test(k)){ var v = tr(k); if(v) node.nodeValue = raw.replace(k, v); }
      }
      return;
    }
    if(node.nodeType !== 1 || skip(node)) return;
    // 태그가 섞인 문장: data-i18n="키"
    var hs = node.querySelectorAll ? node.querySelectorAll('[data-i18n]') : [];
    var list = [node].concat(Array.prototype.slice.call(hs));
    list.forEach(function(el){
      if(el.getAttribute && el.getAttribute('data-i18n')){ var v = tr(el.getAttribute('data-i18n')); if(v) el.innerHTML = v; }
    });
    var tw = document.createTreeWalker(node, NodeFilter.SHOW_TEXT, null, false), t, arr = [];
    while((t = tw.nextNode())) arr.push(t);
    arr.forEach(apply);
    var els = [node].concat(Array.prototype.slice.call(node.querySelectorAll('[placeholder],[title],[aria-label],[alt]')));
    els.forEach(function(el){
      if(skip(el)) return;
      ATTRS.forEach(function(a){
        var x = el.getAttribute && el.getAttribute(a); if(!x) return;
        var k = x.trim(); if(!/[가-힣]/.test(k)) return;
        var v = tr(k); if(v) el.setAttribute(a, v);
      });
    });
  }
  function flush(){
    busy = false;
    var p = pending; pending = [];
    p.forEach(function(n){ if(n.isConnected !== false) apply(n); });
    mountButtons();
  }
  function queue(n){ pending.push(n); if(!busy){ busy = true; (window.requestAnimationFrame || setTimeout)(flush); } }
  function pageName(){
    var p = location.pathname.replace(/\/+$/,'').split('/').pop() || 'index';
    return p.replace(/\.html$/,'') || 'index';
  }
  function load(u){ return fetch(u).then(function(r){ return r.ok ? r.json() : {}; }).catch(function(){ return {}; }); }
  function meta(){
    var t = document.querySelector('meta[name="title:' + lang + '"]'); if(t) document.title = t.getAttribute('content');
    var d = document.querySelector('meta[name="desc:' + lang + '"]'), md = document.querySelector('meta[name="description"]');
    if(d && md) md.setAttribute('content', d.getAttribute('content'));
  }
  // 아직 번역되지 않은 페이지가 많다는 것을 정직하게 알린다(세션마다 한 번)
  var NOTE = {
    en: 'Bible Insight is being translated. Pages not yet translated appear in Korean.',
    es: 'Bible Insight se está traduciendo. Las páginas aún no traducidas aparecen en coreano.',
    ja: 'バイブル・インサイトは現在翻訳中です。未翻訳のページは韓国語で表示されます。',
    zh: '聖經洞見正在翻譯中。尚未翻譯的頁面會以韓文顯示。'
  };
  var OK = { en:'OK', es:'Entendido', ja:'閉じる', zh:'知道了' };
  function note(){
    try{ if(sessionStorage.getItem('bibly_lang_note') === lang) return; }catch(e){}
    if(document.querySelector('.rp[data-l="' + lang + '"]')) return; // 이 페이지는 번역본이 있음
    var d = document.createElement('div'); d.id = 'biblyLangNote'; d.setAttribute('data-noi18n','1');
    d.innerHTML = NOTE[lang] + '<button type="button">' + OK[lang] + '</button>';
    d.querySelector('button').onclick = function(){ d.remove(); try{ sessionStorage.setItem('bibly_lang_note', lang); }catch(e){} };
    document.body.insertBefore(d, document.body.firstChild);
  }

  function start(){
    mountButtons();
    // 머리글이 나중에 그려져도 단추가 붙도록
    new MutationObserver(function(ms){
      if(lang === 'ko'){ mountButtons(); return; }
      ms.forEach(function(m){
        if(m.type === 'characterData') queue(m.target);
        else for(var i=0;i<m.addedNodes.length;i++) queue(m.addedNodes[i]);
      });
    }).observe(document.body, { childList:true, subtree:true, characterData: lang !== 'ko' });
    if(lang === 'ko') return;
    meta(); note();
    var name = pageName(), jobs = [load('/i18n/common.json?v=' + VER)];
    if(PAGES.indexOf(name) >= 0) jobs.push(load('/i18n/pages/' + name + '.json?v=' + VER));
    Promise.all(jobs).then(function(ds){
      ds.forEach(function(d){ for(var k in d) if(k.charAt(0) !== '_') DICT[k] = d[k]; });
      apply(document.body);
      var t = document.title; if(DICT[t] && DICT[t][lang]) document.title = DICT[t][lang];
    });
  }
  if(document.body) start(); else document.addEventListener('DOMContentLoaded', start);
})();
