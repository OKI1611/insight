/* i18n_audit.js — 외국어 화면에 한국어가 얼마나 남았는지 페이지별로 센다(로컬 미리보기 전용)
   사용(localhost:4599 탭에서): localStorage.setItem('bibly_lang','en'); 스크립트 불러온 뒤
     __i18nAudit(['academy', ...], 'http://127.0.0.1:4610')  → 수신기에 audit_<페이지>.json
   번역 대상에서 빠지는 곳(data-l·data-noi18n·script 등)과 안내 띠는 세지 않는다. */
(function(){
  var KO = /[가-힣]/;
  function skip(el){
    for(var p = el; p && p.nodeType === 1; p = p.parentNode){
      var n = p.nodeName;
      if(n === 'SCRIPT' || n === 'STYLE' || n === 'TEXTAREA' || n === 'NOSCRIPT') return true;
      if(p.hasAttribute('data-noi18n') || p.hasAttribute('data-l') || p.id === 'biblyLangNote' || p.id === 'biblyLangMenu') return true;
    }
    return false;
  }
  function visible(el){
    for(var p = el; p && p.nodeType === 1; p = p.parentNode){
      var cs = p.ownerDocument.defaultView.getComputedStyle(p);
      if(cs.display === 'none' || cs.visibility === 'hidden') return false;
    }
    return true;
  }
  window.__i18nAudit = async function(pages, recv, wait){
    wait = wait || 5000; var log = window.__auditLog = [];
    for(var i=0;i<pages.length;i++){
      var p = pages[i];
      try{
        var f = document.createElement('iframe');
        f.style.cssText = 'position:fixed;left:-3000px;top:0;width:420px;height:900px;border:0';
        f.src = '/' + p; document.body.appendChild(f);
        await new Promise(function(r){ f.onload = r; setTimeout(r, 15000); });
        await new Promise(function(r){ setTimeout(r, wait); });
        var d = f.contentDocument, left = [], vis = 0;
        var tw = d.createTreeWalker(d.body, NodeFilter.SHOW_TEXT), t;
        while((t = tw.nextNode())){
          var k = t.nodeValue.trim(); if(!k || !KO.test(k) || skip(t.parentNode)) continue;
          var v = visible(t.parentNode); if(v) vis++;
          left.push((v ? '' : '(hidden) ') + k.slice(0, 120));
        }
        await fetch(recv + '/?name=' + encodeURIComponent('audit_' + p), { method:'POST', body: JSON.stringify({ page:p, lang: d.documentElement.getAttribute('data-ui'), visible: vis, total: left.length, left: left }) });
        log.push(p + ':' + vis + '/' + left.length); f.remove();
      }catch(e){ log.push(p + ':ERR ' + e.message); }
    }
    log.push('DONE'); return log;
  };
})();
