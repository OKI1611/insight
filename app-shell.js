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
    chat:'<svg viewBox="0 0 24 24"><path d="M21 12a8 8 0 0 1-11.6 7.1L4 20l1-4.6A8 8 0 1 1 21 12z"/><path d="M9 11h6"/><path d="M9 14h3.5"/></svg>',
    user:'<svg viewBox="0 0 24 24"><circle cx="12" cy="8.5" r="3.6"/><path d="M4.5 20a7.5 7.5 0 0 1 15 0"/></svg>',
    back:'<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 5l-7 7 7 7"/></svg>',
    search:'<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>',
    menu:'<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M4 7h16M4 12h16M4 17h16"/></svg>'
  };
  var TABS = [
    { k:'home',  l:'홈',   h:'/app',        i:ICON.home, m:/^\/(app(\.html)?)?$/ },
    { k:'learn', l:'강의', h:'/curriculum', i:ICON.play, m:/^\/(curriculum|watch|find|curriculum-guide|booklet)(\.html)?$/ },
    { k:'bible', l:'성경', h:'/bible',      i:ICON.book, m:/^\/(bible|dictionary|themes|bible-english(-unit)?|translation-notes|kjv-preface|search)(\.html)?$/ },
    { k:'qna',   l:'질문', h:'/qna',        i:ICON.chat, m:/^\/(qna|qna-board|qna-write|community)(\.html)?$/ },
    { k:'my',    l:'MY',   h:'/mylearning', i:ICON.user, m:/^\/(mylearning|academy|exam|profile|support|notices|event|tester)(\.html)?$/ }
  ];
  var path = (location.pathname.replace(/\/+$/, '') || '/');
  function tabOf(p){ for(var i=0;i<TABS.length;i++){ if(TABS[i].m.test(p)) return TABS[i]; } return null; }
  var cur = tabOf(path);
  var isHome = !!(document.body && document.body.hasAttribute('data-app-home')) || (cur && cur.k==='home');

  function pageTitle(){
    if(window.__appTitle) return window.__appTitle;
    var m = document.querySelector('meta[name="app-title"]'); if(m && m.content) return m.content;
    var t = (document.title || '').split(/\s[—|·|]\s|\s-\s/)[0].trim();
    return t || 'BIBLY';
  }
  // 페이지가 상단바 제목을 직접 정한다(예: 성경 「요한복음 3장」)
  window.__setAppTitle = function(t){ window.__appTitle = t; var el = document.getElementById('appTitle'); if(el){ el.textContent = t; el.classList.toggle('long', t.length > 14); } };
  function goBack(){
    if(history.length > 1 && document.referrer && document.referrer.indexOf(location.origin) === 0){ history.back(); }
    else location.href = '/app';
  }
  function buildBar(){
    if(isHome || document.getElementById('appBar')) return;
    var bar = document.createElement('div'); bar.id = 'appBar';
    bar.innerHTML = '<div class="ab">'
      + '<button type="button" id="appBack" aria-label="뒤로">' + ICON.back + '<span class="bk">뒤로</span></button>'
      + '<div class="ttl' + (pageTitle().length > 14 ? ' long' : '') + '" id="appTitle">' + pageTitle().replace(/[<>&]/g, '') + '</div>'
      + '<a href="/search" id="appSearchBtn" aria-label="검색">' + ICON.search + '</a>'
      + '<button type="button" id="appMenuBtn" aria-label="전체 메뉴">' + ICON.menu + '</button>'
      + '</div>';
    document.body.insertBefore(bar, document.body.firstChild);
    document.getElementById('appBack').addEventListener('click', goBack);
    document.getElementById('appSearchBtn').addEventListener('click', function(e){ if(typeof window.__appSearch === 'function'){ e.preventDefault(); window.__appSearch(); } });
    document.getElementById('appMenuBtn').addEventListener('click', function(){
      var m = document.getElementById('biblyMobMenu');
      if(m){ if(m.parentNode !== bar) bar.appendChild(m); m.classList.toggle('hidden'); }
      else location.href = '/app';
    });
    // site-header.js 가 나중에 그려도 전체 메뉴를 상단바 아래로 옮겨 둔다
    var tries = 0, tm = setInterval(function(){
      var m = document.getElementById('biblyMobMenu');
      if(m && m.parentNode !== bar){ m.classList.add('hidden'); bar.appendChild(m); clearInterval(tm); }
      if(++tries > 40) clearInterval(tm);
    }, 150);
  }
  function buildTabs(){
    if(document.getElementById('appTabs')) return;
    var nav = document.createElement('nav'); nav.id = 'appTabs'; nav.setAttribute('aria-label', '앱 메뉴');
    nav.innerHTML = TABS.map(function(t){
      return '<a href="' + t.h + '" data-tab="' + t.k + '" class="' + (cur && cur.k === t.k ? 'on' : '') + '">' + t.i + '<span>' + t.l + '</span></a>';
    }).join('');
    document.body.appendChild(nav);
    // 탭 루트 ↔ 탭 루트 이동은 히스토리를 쌓지 않는다(뒤로 가기가 탭을 되감지 않도록)
    nav.addEventListener('click', function(e){
      var a = e.target.closest('a'); if(!a) return;
      var atRoot = TABS.some(function(t){ return path === t.h || path === t.h + '.html'; });
      if(atRoot){ e.preventDefault(); location.replace(a.getAttribute('href')); }
    });
  }
  function run(){ try{ buildBar(); buildTabs(); }catch(e){} }
  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', run); else run();
  // 제목이 늦게 바뀌는 페이지(강의 등)는 상단바 제목도 따라간다
  try{
    var tEl = document.querySelector('title');
    if(tEl && window.MutationObserver){ new MutationObserver(function(){ if(window.__appTitle) return; var el = document.getElementById('appTitle'); if(el){ var t = pageTitle(); el.textContent = t; el.classList.toggle('long', t.length > 14); } }).observe(tEl, { childList:true }); }
  }catch(e){}
})();
