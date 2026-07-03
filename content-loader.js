/* content-loader.js — 관리자 편집 즉시 반영
   content/course.json · content/site.json 요청을 가로채,
   Supabase site_content에 저장된 최신본이 있으면 그것을, 없으면 정적 파일을 돌려준다.
   반드시 페이지의 다른 스크립트보다 먼저(<head>) 로드되어야 함. */
(function(){
  if(window.__biblyLoaderReady) return; window.__biblyLoaderReady = true;
  // FOUC(전체 화면 깜빡임) 제거 — Tailwind CDN이 커스텀 색을 입히기 전 '무스타일' 화면이
  //  잠깐 보였다가 스타일이 입혀지며 번쩍이는 현상 차단. 본문을 아주 잠깐 숨겼다가
  //  스타일 준비되면 부드럽게 표시. (무슨 일이 있어도 최대 650ms 후엔 반드시 보이게 안전장치)
  try{
    var __de = document.documentElement, __revealed = false;
    // reveal = 숨김 클래스 제거만(→ body는 기본 opacity:1로 즉시 복귀). transition·animation은
    //  탭이 비활성일 때 타임라인이 멈춰 숨김 상태로 고착될 수 있어 쓰지 않는다.
    //  본문은 reveal 시점에 이미 스타일이 다 입혀져 있으므로 즉시 표시해도 깜빡임이 없다.
    function __reveal(){ if(__revealed) return; __revealed = true; try{ __de.classList.remove('bibly-fouc'); }catch(e){} }
    var __fst = document.createElement('style'); __fst.id = 'biblyFoucStyle';
    __fst.textContent = 'html.bibly-fouc body{opacity:0!important}';
    (document.head || __de).appendChild(__fst);
    __de.classList.add('bibly-fouc');
    setTimeout(__reveal, 650);   // 최우선 하드 안전장치(예외가 나도 반드시 표시)
    var __whenStyled = function(){
      // Tailwind가 커스텀 색(ink=#213a6b)을 실제로 입혔는지 프로브로 확인 후 표시
      try{
        var p = document.createElement('div');
        p.className = 'bg-ink';
        p.style.cssText = 'position:fixed;left:-9999px;top:-9999px;width:1px;height:1px;pointer-events:none';
        document.body.appendChild(p);
        var tries = 0;
        (function chk(){
          tries++;
          var bg = getComputedStyle(p).backgroundColor;
          if(bg === 'rgb(33, 58, 107)' || tries > 34){ try{ p.remove(); }catch(e){} __reveal(); }
          else requestAnimationFrame(chk);
        })();
      }catch(e){ __reveal(); }
    };
    if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', __whenStyled);
    else __whenStyled();
  }catch(e){ try{ document.documentElement.classList.remove('bibly-fouc'); }catch(_){} }
  // 접근성 — 저장된(또는 기본 17px) 글자 크기를 깜빡임 없이 즉시 적용
  try{ var __fs = localStorage.getItem('biblyFont') || '17px'; document.documentElement.style.fontSize = __fs; }catch(e){}
  // 한글 줄바꿈을 어절 단위로(단어 중간에서 끊기지 않게) — 전 페이지 공통 타이포 개선
  try{
    var __ks = document.createElement('style');
    __ks.textContent = 'body{word-break:keep-all;overflow-wrap:break-word}';
    (document.head || document.documentElement).appendChild(__ks);
  }catch(e){}
  var SB = 'https://bmxkndkwefdgsomlznoo.supabase.co';
  var AK = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJteGtuZGt3ZWZkZ3NvbWx6bm9vIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODA1NzAwODIsImV4cCI6MjA5NjE0NjA4Mn0.l1yHhMVYwMqYSL8ub9PtrJPOl7CYr7yqstG2AER1EaU';
  var orig = window.fetch ? window.fetch.bind(window) : null;
  if(!orig) return;
  var cache = {};
  function live(key){
    if(cache[key] !== undefined) return Promise.resolve(cache[key]);
    var ctrl = typeof AbortController !== 'undefined' ? new AbortController() : null;
    var to = ctrl ? setTimeout(function(){ ctrl.abort(); }, 5000) : null;
    return orig(SB + '/rest/v1/site_content?select=data&key=eq.' + key, { signal: ctrl ? ctrl.signal : undefined, headers:{ apikey:AK, Authorization:'Bearer ' + AK } })
      .then(function(r){ if(to) clearTimeout(to); return r.ok ? r.json() : []; })
      .then(function(rows){ var d = (rows && rows[0]) ? rows[0].data : null; cache[key] = d; return d; })
      .catch(function(){ if(to) clearTimeout(to); cache[key] = null; return null; });
  }
  window.fetch = function(url, opts){
    try{
      var u = String((url && url.url) ? url.url : url);
      var m = u.match(/content\/(course|site)\.json/);
      var method = (opts && opts.method) ? String(opts.method).toUpperCase() : 'GET';
      if(m && method === 'GET'){
        var key = m[1];
        return live(key).then(function(d){
          if(d) return new Response(JSON.stringify(d), { status:200, headers:{ 'Content-Type':'application/json' } });
          return orig(url, opts);
        });
      }
    }catch(e){}
    return orig(url, opts);
  };
})();
