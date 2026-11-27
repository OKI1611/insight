/* app-shell.js — 앱 모드(<html class="app">)에서만: 남색 상단바(뒤로·제목·검색·메뉴) + 하단 탭바 5개 주입.
   앱 홈(app.html, body[data-app-home])은 자체 헤더를 쓰므로 탭바만 붙인다.
   의존: app.css(스타일), app-mode.js(html.app 판정). 웹(비앱)에서는 아무 것도 하지 않는다. */
(function(){
  if(!document.documentElement.classList.contains('app')) return;
  // 앱 글자 크기(앱 메뉴에서 선택, 기본 15px). 인라인 !important 라 app.css 기본값과 content-loader 의 웹 설정(17px)보다 우선
  window.__appFont = function(px, save){ try{ if(save !== false) localStorage.setItem('biblyAppFont', px); }catch(e){} document.documentElement.style.setProperty('font-size', px, 'important'); };
  try{ var __f = localStorage.getItem('biblyAppFont'); if(__f) window.__appFont(__f, false); }catch(e){}
  try{ var vp = document.querySelector('meta[name=viewport]'); if(vp && !/viewport-fit/.test(vp.content)) vp.content = vp.content.replace(/\s*$/, '') + ', viewport-fit=cover'; }catch(e){}
  var ICON = {
    home:'<svg viewBox="0 0 24 24"><path d="M3 11.5 12 4l9 7.5"/><path d="M5 10v10h14V10"/><path d="M10 20v-6h4v6"/></svg>',
    play:'<svg viewBox="0 0 24 24"><rect x="3" y="5" width="18" height="14" rx="3"/><path d="M10 9.5v5l4.5-2.5z" fill="currentColor" stroke="none"/></svg>',
    book:'<svg viewBox="0 0 24 24"><path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v16H6.5A2.5 2.5 0 0 0 4 21z"/><path d="M4 18.5A2.5 2.5 0 0 1 6.5 16H20"/><path d="M12 7v5"/><path d="M9.5 9.5h5"/></svg>',
    find:'<svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.6-3.6"/></svg>',
    user:'<svg viewBox="0 0 24 24"><circle cx="12" cy="8.5" r="3.6"/><path d="M4.5 20a7.5 7.5 0 0 1 15 0"/></svg>',
    back:'<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 5l-7 7 7 7"/></svg>',
    search:'<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>',
    menu:'<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M4 7h16M4 12h16M4 17h16"/></svg>',
    bars:'<svg viewBox="0 0 24 24"><path d="M4 6.5h16M4 12h16M4 17.5h16"/></svg>',
    bible:'<svg viewBox="0 0 24 24"><path d="M6 3.5h11.5A1.5 1.5 0 0 1 19 5v15.5H7a2 2 0 0 1-2-2V4.5a1 1 0 0 1 1-1z"/><path d="M5 18.5a2 2 0 0 1 2-2h12"/><path d="M12 7v6M9.5 9.2h5"/></svg>'
  };
  var TABS = [
    { k:'home',  l:'홈',   h:'/app',        i:ICON.home, m:/^\/(app(\.html)?)?$/ },
    { k:'learn', l:'강의', h:'/curriculum', i:ICON.play, m:/^\/(curriculum|watch|find|curriculum-guide|booklet)(\.html)?$/ },
    { k:'bible', l:'성경', h:'/bible',      i:ICON.bible, m:/^\/(bible|dictionary|themes|bible-english(-unit)?|translation-notes|kjv-preface|daily|memorize|meditation|bible-plan)(\.html)?$/, center:true },
    { k:'my',    l:'MY',   h:'/mylearning', i:ICON.user, m:/^\/(mylearning|academy|exam|profile|support|notices|event|tester)(\.html)?$/ },
    { k:'menu',  l:'전체메뉴', h:'#menu',  i:ICON.bars, m:/^$/, menu:true }
  ];
  var path = (location.pathname.replace(/\/+$/, '') || '/');
  function tabOf(p){
    if(/^\/app-menu(\.html)?$/.test(p)){ var pp = new URLSearchParams(location.search).get('p') || ''; var k = (pp === 'search') ? 'find' : (pp === 'dictionary' || pp === 'themes' || pp === 'english' || pp === 'notes') ? 'bible' : (pp === 'store' || pp === 'academy') ? 'learn' : 'home'; return TABS.filter(function(t){ return t.k === k; })[0]; }
    for(var i=0;i<TABS.length;i++){ if(TABS[i].m.test(p)) return TABS[i]; } return null;
  }
  var cur = tabOf(path);
  var isHome = !!(document.body && document.body.hasAttribute('data-app-home'));

  function pageTitle(){
    if(window.__appTitle) return window.__appTitle;
    var m = document.querySelector('meta[name="app-title"]'); if(m && m.content) return m.content;
    var t = (document.title || '').split(/\s[—|·|]\s|\s-\s/)[0].trim();
    return t || '바이블 인사이트';
  }
  // 페이지가 상단바 제목을 직접 정한다(예: 성경 「요한복음 3장」)
  window.__setAppTitle = function(t){ window.__appTitle = t; var el = document.getElementById('appTitle'); if(el){ el.textContent = t; el.classList.toggle('long', t.length > 14); } };
  function goBack(){
    // 화면 안에서 먼저 닫을 것이 있으면(예: 질의응답 글 → 목록) 그 화면이 처리한다
    try{ if(typeof window.__appBack === 'function' && window.__appBack()) return; }catch(e){}
    if(history.length > 1 && document.referrer && document.referrer.indexOf(location.origin) === 0){ history.back(); }
    else location.href = '/app';
  }
  // 앱에는 아직 다국어(i18n.js)를 넣지 않는다(2026-11-27 저자 지시) — 언어 단추·번역 없음
  // 수강생 질문방 새 글 알림(🔔 + N) — 앱 홈·앱 메뉴처럼 site-header.js 가 없는 화면에서도
  (function(){ try{ if(window.__biblyQnaBell || document.querySelector('script[src*="qna-notify.js"]')) return; var q = document.createElement('script'); q.src = '/qna-notify.js?v=20261127a'; q.defer = true; document.head.appendChild(q); }catch(e){} })();
  // 새 강의·새 글 앱 푸시 알림 켜기(앱 홈 카드 + 구독 맞추기)
  (function(){ try{ if(window.__biblyPush || document.querySelector('script[src*="push-client.js"]')) return; var q = document.createElement('script'); q.src = '/push-client.js?v=20261127a'; q.defer = true; document.head.appendChild(q); }catch(e){} })();
  function buildBar(){
    if(isHome || document.getElementById('appBar')) return;
    var bar = document.createElement('div'); bar.id = 'appBar';
    bar.innerHTML = '<div class="ab">'
      + '<button type="button" id="appBack" aria-label="뒤로">' + ICON.back + '</button>'
      + '<div class="ttl' + (pageTitle().length > 14 ? ' long' : '') + '" id="appTitle">' + pageTitle().replace(/[<>&]/g, '') + '</div>'
      + '<a href="/app-menu?p=search" id="appSearchBtn" aria-label="검색">' + ICON.search + '</a>'
      + '<button type="button" id="appMenuBtn" aria-label="전체 메뉴">' + ICON.menu + '</button>'
      + '</div>';
    document.body.insertBefore(bar, document.body.firstChild);
    document.getElementById('appBack').addEventListener('click', goBack);
    document.getElementById('appSearchBtn').addEventListener('click', function(e){ if(typeof window.__appSearch === 'function'){ e.preventDefault(); window.__appSearch(); } });
    document.getElementById('appMenuBtn').addEventListener('click', openMenu);
  }
  function buildTabs(){
    if(document.getElementById('appTabs')) return;
    var nav = document.createElement('nav'); nav.id = 'appTabs'; nav.setAttribute('aria-label', '앱 메뉴');
    nav.innerHTML = TABS.map(function(t){
      var on = cur && cur.k === t.k ? ' on' : '';
      if(t.menu) return '<button type="button" data-tab="menu" class="tb">' + t.i + '<span>' + t.l + '</span></button>';
      if(t.center) return '<a href="' + t.h + '" data-tab="' + t.k + '" class="tb ctr' + on + '"><span class="ctrc">' + t.i + '</span><span>' + t.l + '</span></a>';
      return '<a href="' + t.h + '" data-tab="' + t.k + '" class="tb' + on + '">' + t.i + '<span>' + t.l + '</span></a>';
    }).join('');
    document.body.appendChild(nav);
    nav.querySelector('[data-tab="menu"]').addEventListener('click', openMenu);
    // 탭 루트 ↔ 탭 루트 이동은 히스토리를 쌓지 않는다(뒤로 가기가 탭을 되감지 않도록)
    nav.addEventListener('click', function(e){
      var a = e.target.closest('a'); if(!a) return;
      var here = path + location.search;
      var atRoot = TABS.some(function(t){ return here === t.h || path === t.h || path === t.h + '.html'; });
      if(atRoot){ e.preventDefault(); location.replace(a.getAttribute('href')); }
    });
  }

  // ══ 전체 메뉴(2단: 왼쪽 분류 · 오른쪽 메뉴) ══
  // 분류·메뉴는 홈페이지 메뉴의 단일 출처(content/site.json nav)를 그대로 읽는다 → 홈페이지 메뉴를 고치면 앱도 같이 바뀐다.
  // 앱 안에서 더 잘 보이는 앱 전용 화면이 있는 페이지는 그쪽으로 연결한다(APPROUTE).
  var APPROUTE = {
    'dictionary.html':'/app-menu?p=dictionary', 'themes.html':'/app-menu?p=themes', 'qna-board.html':'/app-menu?p=board',
    'booklet.html':'/app-menu?p=store', 'academy.html':'/app-menu?p=academy', 'notices.html':'/app-menu?p=notices',
    'event.html':'/app-menu?p=events', 'support.html':'/app-menu?p=support', 'bible-english.html':'/app-menu?p=english',
    'resources.html':'/app-menu?p=resources', 'search.html':'/app-menu?p=search'
  };
  function appHref(h){
    if(!h) return '#';
    var m = h.match(/^\/?([\w-]+\.html)(\?[^#]*)?(#.*)?$/); if(!m) return h;
    var file = m[1], q = m[2] || '', hash = m[3] || '';
    if(file === 'books.html') return '/app-menu?p=books' + (hash ? '&id=' + hash.slice(1) : '');
    if(file === 'qna.html'){ var r = (q.match(/room=(\w+)/) || [])[1]; return '/app-menu?p=qna' + (r ? '&room=' + r : ''); }
    if(APPROUTE[file] && !hash) return APPROUTE[file];
    return '/' + file.replace(/\.html$/, '') + q + hash;
  }
  var GICON = {   // 분류 머리 아이콘(선 아이콘)
    intro:'<path d="M12 21s-7-4.4-7-10a7 7 0 0 1 14 0c0 5.6-7 10-7 10z"/><circle cx="12" cy="11" r="2.5"/>',
    learn:'<rect x="3" y="5" width="18" height="14" rx="3"/><path d="M10 9.5v5l4.5-2.5z"/>',
    bible:'<path d="M6 3.5h11.5A1.5 1.5 0 0 1 19 5v15.5H7a2 2 0 0 1-2-2V4.5a1 1 0 0 1 1-1z"/><path d="M12 7v6M9.5 9.2h5"/>',
    dict:'<circle cx="11" cy="11" r="6.5"/><path d="m20 20-4-4"/>',
    faith:'<path d="M12 3v18M7 8h10"/>',
    qna:'<path d="M21 12a8 8 0 0 1-11.6 7.1L4 20l1-4.6A8 8 0 1 1 21 12z"/>',
    store:'<path d="M6 6h15l-1.5 9h-12z"/><path d="M6 6 5 3H2"/><circle cx="9" cy="20" r="1.3"/><circle cx="18" cy="20" r="1.3"/>',
    books:'<path d="M5 4h11a3 3 0 0 1 3 3v13H8a3 3 0 0 0-3 3z"/><path d="M5 4v16a3 3 0 0 1 3-3h11"/>',
    academy:'<path d="M3 9.5 12 5l9 4.5-9 4.5z"/><path d="M7 11.5V16c0 1.5 2.3 3 5 3s5-1.5 5-3v-4.5"/>'
  };
  function gicon(g){
    var h = (g.href || '').split(/[?#]/)[0];
    var k = /about/.test(h) ? 'intro' : /curriculum/.test(h) ? 'learn' : /dictionary/.test(h) ? 'dict' : /preachers/.test(h) ? 'faith'
      : /qna/.test(h) ? 'qna' : /booklet/.test(h) ? 'store' : /books/.test(h) ? 'books' : /academy/.test(h) ? 'academy' : 'bible';
    return '<svg viewBox="0 0 24 24" aria-hidden="true">' + GICON[k] + '</svg>';
  }
  var FALLBACK_NAV = [
    { label:'강의·커리큘럼', href:'curriculum.html', children:[{ label:'커리큘럼 전체 보기', href:'curriculum.html' }] },
    { label:'성경', href:'bible.html', children:[{ label:'성경 읽기', href:'bible.html' }] }
  ];
  function esc2(s){ return String(s == null ? '' : s).replace(/[&<>"]/g, function(c){ return { '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;' }[c]; }); }
  var NAV = null, menuEl = null;
  function loadNav(){
    if(NAV) return Promise.resolve(NAV);
    return fetch('/content/site.json').then(function(r){ return r.json(); })
      .then(function(d){ NAV = (d && d.nav && d.nav.length) ? d.nav : FALLBACK_NAV; return NAV; })
      .catch(function(){ NAV = FALLBACK_NAV; return NAV; });
  }
  function link(h, label){ return '<a href="' + esc2(appHref(h)) + '">' + esc2(label) + '</a>'; }
  function renderGroup(i){
    var g = NAV[i]; if(!g || !menuEl) return;
    [].forEach.call(menuEl.querySelectorAll('.afL button'), function(b, k){ b.classList.toggle('on', k === i); });
    var html = '<a class="afH" href="' + esc2(appHref(g.href)) + '">' + gicon(g) + '<b>' + esc2(g.label) + '</b><svg class="chev" viewBox="0 0 24 24" aria-hidden="true"><path d="m9 6 6 6-6 6"/></svg></a>';
    var flat = [], subs = [];
    (g.children || []).forEach(function(c){ if(c.children && c.children.length) subs.push(c); else flat.push(c); });
    if(flat.length) html += '<div class="afG">' + flat.map(function(c){ return link(c.href, c.label); }).join('') + '</div>';
    subs.forEach(function(c){
      html += '<a class="afS" href="' + esc2(appHref(c.href)) + '">' + esc2(c.label) + '</a>'
        + '<div class="afG one">' + c.children.map(function(x){ return link(x.href, x.label); }).join('') + '</div>';
    });
    var R = menuEl.querySelector('.afR'); R.innerHTML = html;
    var sc = menuEl.querySelector('.afScroll'), cat = menuEl.querySelector('.afCat');
    if(sc && cat && sc.scrollTop > cat.offsetTop) sc.scrollTop = cat.offsetTop;
  }
  var SERVICE = [
    { l:'내 강의실', h:'/mylearning', i:'<path d="M4 19V6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v13"/><path d="M4 19h16"/><path d="M8 9h8M8 13h5"/>' },
    { l:'공지사항', h:'/app-menu?p=notices', i:'<path d="M4 11v2a2 2 0 0 0 2 2h1l6 4V5L7 9H6a2 2 0 0 0-2 2z"/><path d="M17 9.5a3.5 3.5 0 0 1 0 5"/>' },
    { l:'이벤트', h:'/app-menu?p=events', i:'<rect x="3" y="8" width="18" height="13" rx="2"/><path d="M3 12h18M12 8v13"/>' },
    { l:'후원하기', h:'/app-menu?p=support', i:'<path d="M19 14c1.5-1.5 3-3.2 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.8 0-3 .5-4.5 2-1.5-1.5-2.7-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4 3 5.5l7 7z"/>', rose:true },
    { l:'장바구니', h:'/booklet#cart', i:'<path d="M6 6h15l-1.5 9h-12z"/><path d="M6 6 5 3H2"/><circle cx="9" cy="20" r="1.3"/><circle cx="18" cy="20" r="1.3"/>' },
    { l:'주문 내역', h:'/orders', i:'<rect x="5" y="3" width="14" height="18" rx="2"/><path d="M9 8h6M9 12h6M9 16h4"/>' },
    { l:'고객센터', h:'/store-help', i:'<path d="M4 13a8 8 0 0 1 16 0"/><rect x="3" y="13" width="4" height="6" rx="1.5"/><rect x="17" y="13" width="4" height="6" rx="1.5"/>' },
    { l:'검색', h:'/app-menu?p=search', i:'<circle cx="11" cy="11" r="7"/><path d="m20 20-3.6-3.6"/>' }
  ];
  var FONTS = [['auto', '보통'], ['18px', '크게'], ['20px', '아주 크게']];
  function curFont(){ try{ return localStorage.getItem('biblyAppFont') || 'auto'; }catch(e){ return 'auto'; } }
  // 글자 크기: '보통' = 저장값을 지우고 화면 폭에 따른 기본값 · 크게 18 · 아주 크게 20
  window.__appSetFont = function(px){
    if(px === 'auto'){ try{ localStorage.removeItem('biblyAppFont'); }catch(e){} document.documentElement.style.removeProperty('font-size'); }
    else window.__appFont(px);
    [].forEach.call(document.querySelectorAll('[data-px]'), function(b){ b.classList.toggle('on', b.getAttribute('data-px') === px); });
  };
  function renderService(){
    var f = curFont();
    return '<div class="afSvG">' + SERVICE.map(function(s){ return '<a href="' + s.h + '"' + (s.rose ? ' class="rose"' : '') + '><svg viewBox="0 0 24 24" aria-hidden="true">' + s.i + '</svg><span>' + s.l + '</span></a>'; }).join('') + '</div>'
      + '<p class="afT">글자 크기</p><div class="afFs">'
      + FONTS.map(function(x){ return '<button type="button" data-px="' + x[0] + '" class="' + (f === x[0] ? 'on' : '') + '">' + x[1] + '</button>'; }).join('')
      + '</div>'
      + '<div class="afFoot"><a href="/privacy">개인정보처리방침</a><a href="/terms">이용약관</a><a href="/about">바이블 인사이트 소개</a></div>';
  }
  function buildMenu(){
    if(menuEl) return menuEl;
    menuEl = document.createElement('div'); menuEl.id = 'appFull'; menuEl.setAttribute('role', 'dialog'); menuEl.setAttribute('aria-label', '전체 메뉴');
    menuEl.innerHTML = '<div class="afTop">'
      + '<nav class="afQ"><a href="/app" class="on">바이블 인사이트</a><a href="/bible">성경</a><a href="/curriculum">강의</a><a href="/app-menu?p=books">저자의 책</a></nav>'
      + '<button type="button" class="afX" aria-label="닫기"><svg viewBox="0 0 24 24"><path d="M6 6l12 12M18 6 6 18"/></svg></button></div>'
      + '<div class="afScroll">'
      + '<a class="afBrand" href="/about"><span class="bm"><img src="/images/icon-192.png?v=8" alt=""/><b>바이블 인사이트 아카데미</b></span><span class="bs">말씀으로 시대를 읽다</span><span class="go">바로가기<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m9 6 6 6-6 6"/></svg></span></a>'
      + '<div class="afSeg" role="tablist"><button type="button" class="on" data-seg="cat">카테고리</button><button type="button" data-seg="svc">서비스</button></div>'
      + '<div class="afCat"><div class="afL"></div><div class="afR"></div></div>'
      + '<div class="afSvc" hidden>' + renderService() + '</div>'
      + '</div>';
    document.body.appendChild(menuEl);
    menuEl.querySelector('.afX').addEventListener('click', function(){ closeMenu(); });
    menuEl.querySelector('.afSeg').addEventListener('click', function(e){
      var b = e.target.closest('button'); if(!b) return;
      [].forEach.call(this.querySelectorAll('button'), function(x){ x.classList.toggle('on', x === b); });
      var svc = b.getAttribute('data-seg') === 'svc';
      menuEl.querySelector('.afCat').hidden = svc; menuEl.querySelector('.afSvc').hidden = !svc;
    });
    menuEl.querySelector('.afFs').addEventListener('click', function(e){ var b = e.target.closest('button[data-px]'); if(b) window.__appSetFont(b.getAttribute('data-px')); });
    menuEl.querySelector('.afL').addEventListener('click', function(e){ var b = e.target.closest('button'); if(b) renderGroup(+b.getAttribute('data-i')); });
    menuEl.addEventListener('click', function(e){ var a = e.target.closest('a'); if(a && a.getAttribute('href') && a.getAttribute('href').charAt(0) !== '#') closeMenu(true); });
    loadNav().then(function(nav){
      menuEl.querySelector('.afL').innerHTML = nav.map(function(g, i){ return '<button type="button" data-i="' + i + '">' + esc2(g.label) + '</button>'; }).join('');
      // 지금 보는 화면이 속한 분류를 먼저 연다
      var here = path.replace(/^\//, '').replace(/\.html$/, '') + '.html', pick = 0;
      nav.forEach(function(g, i){
        var all = [g].concat(g.children || []);
        (g.children || []).forEach(function(c){ (c.children || []).forEach(function(x){ all.push(x); }); });
        if(all.some(function(c){ return (c.href || '').split(/[?#]/)[0] === here; }) && !pick) pick = i;
      });
      renderGroup(pick);
    });
    return menuEl;
  }
  var menuOpen = false;
  function openMenu(){
    buildMenu(); if(menuOpen) return;
    menuOpen = true; menuEl.classList.add('open'); document.documentElement.classList.add('afLock');
    try{ history.pushState({ appFull:1 }, ''); }catch(e){}   // 안드로이드 뒤로 = 메뉴 닫기
  }
  function closeMenu(navigating){
    if(!menuOpen) return;
    menuOpen = false; menuEl.classList.remove('open'); document.documentElement.classList.remove('afLock');
    if(!navigating){ try{ if(history.state && history.state.appFull) history.back(); }catch(e){} }
  }
  window.addEventListener('popstate', function(){ if(menuOpen){ menuOpen = false; menuEl.classList.remove('open'); document.documentElement.classList.remove('afLock'); } });
  window.__appOpenMenu = openMenu;
  function buildStatus(){ if(document.getElementById('appStatus')) return; var s = document.createElement('div'); s.id = 'appStatus'; s.setAttribute('aria-hidden', 'true'); document.body.insertBefore(s, document.body.firstChild); }
  function run(){ try{ buildStatus(); buildBar(); buildTabs(); }catch(e){} }
  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', run); else run();
  // 제목이 늦게 바뀌는 페이지(강의 등)는 상단바 제목도 따라간다
  try{
    var tEl = document.querySelector('title');
    if(tEl && window.MutationObserver){ new MutationObserver(function(){ if(window.__appTitle) return; var el = document.getElementById('appTitle'); if(el){ var t = pageTitle(); el.textContent = t; el.classList.toggle('long', t.length > 14); } }).observe(tEl, { childList:true }); }
  }catch(e){}
})();
