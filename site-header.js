/* site-header.js — 공통 헤더 컴포넌트 (모든 하위 페이지 공용)
   사용법: 본문 맨 위에 <div id="siteHeader" data-active="community.html"></div> 를 두고,
           <head> 에서 <script src="/site-header.js"></script> 로 불러온다.
   - 로고 + 메뉴(content/site.json, 없으면 기본값) + 인증영역(📚 내 강의실 · ♥ 후원 · 로그인/로그아웃)을 그린다.
   - 로그인 모달이 필요한 페이지는 window.biblyHeaderLogin 함수를 정의하면 '로그인' 클릭 시 그 함수가 호출된다(없으면 index.html 로 이동).
   - <head> 로드(=content-loader.js 와 동일)라 미리보기 환경에서도 실행됨. */
(function(){
  if(window.__biblyHeaderInit) return; window.__biblyHeaderInit = true;
  var SB = 'https://bmxkndkwefdgsomlznoo.supabase.co';
  var AK = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJteGtuZGt3ZWZkZ3NvbWx6bm9vIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODA1NzAwODIsImV4cCI6MjA5NjE0NjA4Mn0.l1yHhMVYwMqYSL8ub9PtrJPOl7CYr7yqstG2AER1EaU';
  var ADMIN = 'josephoh1611@gmail.com';
  var DEFAULT_MENU = [
    { label:'우리의 사명', href:'about.html' },
    { label:'나에게 맞는 강의 찾기', href:'find.html' },
    { label:'커리큘럼', href:'curriculum.html' },
    { label:'질문·나눔·기도요청', href:'community.html' },
    { label:'강의 요청·건의함', href:'request.html' },
    { label:'자료실', href:'resources.html' },
    { label:'성경 읽기', href:'bible.html' }
  ];

  function esc(s){ return String(s == null ? '' : s).replace(/[&<>"]/g, function(c){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); }

  function readStored(){
    try{
      for(var i=0;i<localStorage.length;i++){
        var k = localStorage.key(i); if(!/auth-token/.test(k)) continue;
        var v = JSON.parse(localStorage.getItem(k));
        var s = (v && v.user) ? v : (v && v.currentSession) ? v.currentSession : null;
        if(s && s.user){ if(s.expires_at && s.expires_at*1000 < Date.now()) return null; return s; }
      }
    }catch(e){}
    return null;
  }
  window.__biblyLogout = window.__biblyLogout || function(){
    try{ for(var i=localStorage.length-1;i>=0;i--){ var k=localStorage.key(i); if(/-auth-token/.test(k)) localStorage.removeItem(k); } }catch(e){}
    location.reload();
  };
  window.__biblyHeaderLoginClick = function(){
    if(typeof window.biblyHeaderLogin === 'function'){ try{ window.biblyHeaderLogin(); return; }catch(e){} }
    location.href = 'index.html';
  };

  var LOGO =
    '<a href="index.html" class="flex items-center gap-2 shrink-0">'
    + '<span class="w-8 h-8 rounded-lg bg-ink flex items-center justify-center shrink-0">'
    + '<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="#b8923f" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 6.6C10.4 5.5 8.4 5 6 5C4.7 5 3.7 5.15 3 5.35V18.2C3.7 18 4.7 17.85 6 17.85C8.4 17.85 10.4 18.35 12 19.5"/><path d="M12 6.6C13.6 5.5 15.6 5 18 5C19.3 5 20.3 5.15 21 5.35V18.2C20.3 18 19.3 17.85 18 17.85C15.6 17.85 13.6 18.35 12 19.5"/><path d="M12 6.6V19.5"/></svg></span>'
    + '<span class="leading-none"><span class="block font-extrabold text-[15px] tracking-tight">BIBLY<span class="text-gold">.</span></span>'
    + '<span class="block text-[9px] text-ink/45 tracking-wide mt-0.5">말씀으로 시대를 읽다</span></span></a>';

  var mount, active;

  function menuHTML(menu){
    return menu.map(function(m){
      var hash = String(m.href).charAt(0) === '#';
      var href = hash ? ('index.html' + m.href) : m.href;
      var on = !hash && (href.split('?')[0] === active);
      return '<a href="' + href + '" class="whitespace-nowrap ' + (on ? 'text-gold font-semibold' : 'hover:text-gold') + '">' + esc(m.label) + '</a>';
    }).join('');
  }

  function authHTML(){
    var mylearn = '<a href="mylearning.html" class="hidden xl:inline-flex items-center gap-1 border border-gold/45 text-gold font-semibold px-3 py-1.5 rounded-full hover:bg-gold/10 transition text-xs whitespace-nowrap">📚 내 강의실</a>';
    var support = '<a href="support.html" aria-label="후원하기" title="후원하기" class="inline-flex items-center justify-center w-8 h-8 rounded-full bg-rose-500/10 text-rose-500 border border-rose-300 hover:bg-rose-500 hover:text-white transition shrink-0" style="font-size:15px">♥</a>';
    var s = readStored(), authpart;
    if(s && s.user){
      var nm = (s.user.user_metadata && (s.user.user_metadata.full_name || s.user.user_metadata.name)) || (s.user.email ? s.user.email.split('@')[0] : '회원');
      var admin = (s.user.email === ADMIN) ? ' <span class="text-gold font-semibold">· 관리자</span>' : '';
      authpart = '<span id="biblyAuthName" class="text-ink/60 text-xs whitespace-nowrap">' + esc(nm) + '님' + admin
        + ' · <button onclick="__biblyLogout()" class="hover:text-gold">로그아웃</button></span>';
    } else {
      authpart = '<button onclick="__biblyHeaderLoginClick()" class="bg-gold text-white font-semibold px-3.5 py-1.5 rounded-full hover:opacity-90 transition text-xs whitespace-nowrap">로그인</button>';
    }
    return mylearn + support + authpart
      + '<a href="index.html" class="hidden xl:inline text-ink/45 hover:text-gold whitespace-nowrap text-sm">홈</a>';
  }

  // 모바일 드롭다운 메뉴(햄버거)
  function mobileMenuHTML(menu){
    var items = menu.map(function(m){
      var hash = String(m.href).charAt(0) === '#';
      var href = hash ? ('index.html' + m.href) : m.href;
      var on = !hash && (href.split('?')[0] === active);
      return '<a href="' + href + '" class="py-3 border-b border-ink/5 ' + (on ? 'text-gold font-semibold' : 'text-ink/75') + '">' + esc(m.label) + '</a>';
    }).join('');
    return '<div class="max-w-6xl mx-auto px-4 py-1 flex flex-col text-[15px]">' + items
      + '<a href="mylearning.html" class="py-3 border-b border-ink/5 text-gold font-semibold">📚 내 강의실</a>'
      + '<a href="index.html" class="py-3 text-ink/55">🏠 홈</a>'
      + '</div>';
  }
  window.__biblyToggleMenu = function(){ var m = document.getElementById('biblyMobMenu'); if(m) m.classList.toggle('hidden'); };

  function headerHTML(menu){
    return '<header class="sticky top-0 z-40 bg-paper/90 backdrop-blur border-b border-ink/8">'
      + '<div class="max-w-7xl mx-auto px-4 h-14 flex items-center gap-3">'
      + LOGO
      + '<nav id="navmenu" class="hidden xl:flex items-center gap-4 text-sm text-ink/70 whitespace-nowrap pl-1">' + menuHTML(menu) + '</nav>'
      + '<div class="ml-auto flex items-center gap-2 sm:gap-3 text-sm shrink-0">' + authHTML()
      + '<button id="biblyHamb" aria-label="메뉴 열기" onclick="__biblyToggleMenu()" class="xl:hidden w-9 h-9 -mr-1 flex items-center justify-center rounded-lg hover:bg-ink/5 text-ink/70"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 6h16M4 12h16M4 18h16"/></svg></button>'
      + '</div>'
      + '</div>'
      + '<div id="biblyMobMenu" class="xl:hidden hidden border-t border-ink/8 bg-paper/95 backdrop-blur shadow-sm">' + mobileMenuHTML(menu) + '</div>'
      + '</header>';
  }

  // 로그인한 회원의 실제 이름(profiles.full_name)으로 보강 — 비차단
  function refineName(s){
    if(!s || !s.user || !s.user.id) return;
    var uid = s.user.id;
    fetch(SB + '/rest/v1/profiles?select=full_name&id=eq.' + uid, { headers:{ apikey:AK, Authorization:'Bearer ' + (s.access_token || AK) } })
      .then(function(r){ return r.ok ? r.json() : []; })
      .then(function(rows){
        var fn = rows && rows[0] && rows[0].full_name; if(!fn) return;
        var span = document.getElementById('biblyAuthName'); if(!span) return;
        var admin = (s.user.email === ADMIN) ? ' <span class="text-gold font-semibold">· 관리자</span>' : '';
        span.innerHTML = esc(fn) + '님' + admin + ' · <button onclick="__biblyLogout()" class="hover:text-gold">로그아웃</button>';
      }).catch(function(){});
  }

  function build(){
    mount = document.getElementById('siteHeader');
    if(!mount) return;
    active = mount.getAttribute('data-active') || (location.pathname.split('/').pop() || 'index.html');
    // 1) 기본 메뉴로 즉시 렌더(깜빡임 방지)
    mount.outerHTML = headerHTML(DEFAULT_MENU);
    // 2) site.json 으로 메뉴 보강
    fetch('content/site.json?t=' + Date.now()).then(function(r){ return r.json(); }).then(function(s){
      if(s && s.menu){
        var nav = document.getElementById('navmenu'); if(nav) nav.innerHTML = menuHTML(s.menu);
        var mob = document.getElementById('biblyMobMenu'); if(mob) mob.innerHTML = mobileMenuHTML(s.menu);
      }
    }).catch(function(){});
    // 3) 로그인 이름 보강
    refineName(readStored());
  }

  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', build);
  else build();
})();
