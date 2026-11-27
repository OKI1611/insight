/* i18n_extract.js — 페이지 화면 글자(번역 대상) 자동 추출기
   ─────────────────────────────────────────────────────────────
   로컬 미리보기(localhost:4599)의 한 탭에서 불러 쓴다. 언어는 반드시 한국어(localStorage bibly_lang 삭제).
     const s = document.createElement('script'); s.src = '/tools/i18n_extract.js'; document.head.appendChild(s);
     // 그 뒤: __i18nExtract(['academy', 'bible', ...], 'http://127.0.0.1:4610')
   각 페이지를 숨은 iframe 으로 열어 스크립트가 그린 화면까지 기다린 뒤, i18n.js 와 **같은 규칙**으로 키를 뽑는다.
     - text : 한글이 든 글자 마디(앞뒤 기호 └ · ▶ → › 등은 떼어 낸 핵심)
     - html : 태그가 섞인 문장(굵게·링크·줄바꿈이 낀 문장) — i18n.js applyHtml 과 같은 조건, 키 = innerHTML(공백 정리)
     - attr : placeholder · title · aria-label · alt
   원본 HTML 에 그대로 없는 숫자 섞인 글자(스크립트가 숫자를 넣어 그린 것)는 숫자를 {n} 으로 바꾼다.
   결과는 수신기(scratchpad/i18n/receiver.py)로 POST → <페이지>.json
*/
(function(){
  var BLOCKS = 'div,p,section,article,ul,ol,li,table,h1,h2,h3,h4,h5,h6,header,footer,nav,form,button,img';
  var EDGE = /^([\s└·•▶►→←↑↓※✓✔★☆▲▼○●◆◇■□\-–—]*)([\s\S]*?)([\s→←↑↓▶►›»]*)$/;
  var KO = /[가-힣]/;
  function norm(s){ return s.replace(/(<span data-stat="[^"]*">)[^<]*(<\/span>)/g, '$1$2').replace(/\s+/g, ' ').trim(); }
  function skip(el){
    for(var p = el; p && p.nodeType === 1; p = p.parentNode){
      var n = p.nodeName;
      if(n === 'SCRIPT' || n === 'STYLE' || n === 'TEXTAREA' || n === 'CODE' || n === 'PRE' || n === 'NOSCRIPT') return true;
      if(p.hasAttribute('data-noi18n') || p.hasAttribute('data-l') || p.isContentEditable) return true;
      if(p.id === 'biblyAuthName' || p.id === 'biblyLangMenu' || p.id === 'biblyLangSlot') return true;
    }
    return false;
  }
  function qualifies(el){
    if(!el.children || !el.children.length) return false;
    var tx = el.textContent; if(tx.length > 1500 || !KO.test(tx)) return false;
    return !el.querySelector(BLOCKS);
  }
  // 한 문장이 태그로 쪼개진 경우만 html 로 본다: 한글 마디가 둘 이상 + 그중 하나는 요소 바로 아래 글자.
  // (링크만 줄지어 있는 메뉴 묶음, '✓ 아이콘 + 문장' 같은 것은 글자 마디 단위로 내려가서 뽑는다)
  function mixed(el){
    var ko = 0, direct = false;
    for(var c = el.firstChild; c; c = c.nextSibling){
      if(c.nodeType === 3){ if(KO.test(c.nodeValue)){ ko++; direct = true; } }
      else if(c.nodeType === 1 && !/^(SVG|IMG|BR)$/i.test(c.nodeName) && KO.test(c.textContent)) ko++;
    }
    return ko >= 2 && direct;
  }
  function core(t){ var m = t.match(EDGE); return (m && m[2]) ? m[2].trim() : t; }
  function extract(doc, src){
    var out = [], seen = {};
    function add(k, type){ if(!k || !KO.test(k)) return; var id = type + '\u0001' + k; if(seen[id]) return; seen[id] = 1; out.push({ k:k, type:type }); }
    function text(raw){
      var k = core(raw.trim()); if(!KO.test(k)) return;
      if(/\d/.test(k) && src.indexOf(k) < 0) k = k.replace(/\d[\d,.]*/g, '{n}');
      add(k, 'text');
    }
    function walk(el){
      if(skip(el)) return;
      if(qualifies(el) && mixed(el)){ add(norm(el.innerHTML), 'html'); return; }
      for(var c = el.firstChild; c; c = c.nextSibling){
        if(c.nodeType === 3) text(c.nodeValue);
        else if(c.nodeType === 1) walk(c);
      }
    }
    walk(doc.body);
    var els = doc.body.querySelectorAll('[placeholder],[title],[aria-label],[alt]');
    for(var i=0;i<els.length;i++){
      if(skip(els[i])) continue;
      ['placeholder','title','aria-label','alt'].forEach(function(a){ var v = els[i].getAttribute(a); if(v && KO.test(v)) add(v.trim(), 'attr'); });
    }
    if(KO.test(doc.title)) add(doc.title.trim(), 'title');
    var md = doc.querySelector('meta[name="description"]'); if(md && KO.test(md.content)) add(md.content.trim(), 'meta');
    return out;
  }
  window.__i18nExtract = async function(pages, recv, wait){
    wait = wait || 4500;
    var log = window.__i18nLog = [];
    for(var i=0;i<pages.length;i++){
      var p = pages[i];
      try{
        var src = await fetch('/' + p + '.html').then(function(r){ return r.text(); });
        var f = document.createElement('iframe');
        f.style.cssText = 'position:fixed;left:-3000px;top:0;width:420px;height:900px;border:0';
        f.src = '/' + p;
        document.body.appendChild(f);
        await new Promise(function(r){ f.onload = r; setTimeout(r, 15000); });
        await new Promise(function(r){ setTimeout(r, wait); });
        var d = f.contentDocument;
        var items = extract(d, src);
        await fetch(recv + '/?name=' + encodeURIComponent(p), { method:'POST', headers:{'Content-Type':'text/plain'}, body: JSON.stringify({ page:p, url: f.contentWindow.location.href, items: items }) });
        log.push(p + ':' + items.length);
        f.remove();
      }catch(e){ log.push(p + ':ERR ' + e.message); }
    }
    log.push('DONE');
    return log;
  };
})();
