/* app-mode.js — 「앱으로 열렸는가」를 페인트 전에 판정해 <html class="app">를 붙인다.
   플레이 스토어 앱(TWA com.biblynote.twa, 시작 주소 /?source=pwa)·홈 화면에 추가한 PWA(standalone)가 대상.
   세션 저장소만 쓴다: TWA와 크롬 브라우저는 저장소를 공유하므로 localStorage에 남기면
   브라우저로 들어온 방문까지 앱 모드가 되어 버린다. ?app=0 으로 해제(디버그). */
(function(){
  try{
    var q = location.search || '';
    var KEY = 'bibly_app';
    if(/[?&]app=0\b/.test(q)){ try{ sessionStorage.removeItem(KEY); }catch(e){} return; }
    var standalone = false;
    try{ standalone = (window.matchMedia && matchMedia('(display-mode: standalone)').matches) || window.navigator.standalone === true; }catch(e){}
    var fromTwa = /^android-app:\/\/com\.biblynote\.twa/i.test(document.referrer || '');
    var flagged = /[?&](source=pwa|app=1)\b/.test(q);
    var session = false; try{ session = sessionStorage.getItem(KEY) === '1'; }catch(e){}
    // PC에 설치한 PWA(넓은 화면)는 웹 레이아웃이 더 낫다 — 1024px 미만에서만 앱 모드
    var narrow = Math.min(screen.width || 9999, window.innerWidth || 9999) < 1024;
    var isApp = (standalone || fromTwa || flagged || session) && narrow;
    if(!isApp) return;
    try{ sessionStorage.setItem(KEY, '1'); }catch(e){}
    document.documentElement.classList.add('app');
    window.BIBLY_APP = true;
    // 홈은 앱 전용 홈으로 — 히스토리를 남기지 않는다(뒤로 가기가 웹 홈으로 튀지 않게)
    var p = location.pathname.replace(/\/+$/, '') || '/';
    // 웹 세부 페이지는 앱 전용 화면(app-menu)으로 — 결제·신청 같은 웹 전용 흐름(buy=, track=, #apply, #order)은 그대로 둔다
    var sub = p.replace(/\.html$/, '');
    var MAP = { '/books':'books', '/notices':'notices', '/event':'events', '/support':'support', '/booklet':'store', '/academy':'academy', '/qna':'qna', '/dictionary':'dictionary' };
    if(MAP[sub]){
      var qs = new URLSearchParams(q), h = location.hash || '';
      var webOnly = (sub === '/booklet' && (qs.get('buy') || qs.get('track') || /#order|#cart/.test(h)))
                 || (sub === '/academy' && /#apply|#packages|#pay/.test(h))
                 || qs.get('web') === '1';
      if(!webOnly){
        var keep = [];
        ['room','id','q','cat'].forEach(function(k){ if(qs.get(k)) keep.push(k + '=' + encodeURIComponent(qs.get(k))); });
        if(sub === '/books' && h) keep.push('id=' + encodeURIComponent(h.slice(1)));
        location.replace('/app-menu?p=' + MAP[sub] + (keep.length ? '&' + keep.join('&') : ''));
        return;
      }
    }
    if(p === '/' || p === '/index.html'){
      var keep = q.replace(/[?&](source=pwa|app=1)\b/g, '').replace(/^&/, '?');
      if(keep === '?') keep = '';
      location.replace('/app' + keep + (location.hash || ''));
    }
  }catch(e){}
})();
