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
    { label:'무료로 시작하기', href:'welcome.html' },
    { label:'BIBLY 이야기', href:'about.html', children:[
      { label:'우리의 사명·소개', href:'about.html' },
      { label:'🎖️ 1기 창립 멤버', href:'founding.html' }
    ]},
    { label:'강의·커리큘럼', href:'curriculum.html', children:[
      { label:'전체 커리큘럼', href:'curriculum.html' },
      { label:'정규 심화 과정(아카데미)', href:'academy.html' },
      { label:'나에게 맞는 강의 찾기', href:'find.html' },
      { label:'칼럼', href:'column.html' }
    ]},
    { label:'스토어', href:'booklet.html', children:[
      { label:'PDF 책자·이용권', href:'booklet.html' },
      { label:'고객센터(주문·배송·반품)', href:'store-help.html' },
      { label:'내 구매·자료', href:'mylearning.html' }
    ]},
    { label:'성경', href:'bible.html', children:[
      { label:'성경 읽기', href:'bible.html' },
      { label:'매일 말씀과 함께', href:'daily.html' },
      { label:'성경암송 365', href:'memorize.html' },
      { label:'주제별 성경', href:'themes.html' },
      { label:'성경사전', href:'dictionary.html' }
    ]},
    { label:'위대한 믿음', href:'preachers.html', children:[
      { label:'위대한 설교자', href:'preachers.html' },
      { label:'위대한 기도자', href:'prayers.html' }
    ]},
    { label:'소통·나눔', href:'community.html', children:[
      { label:'질문·나눔·기도요청', href:'community.html' },
      { label:'신앙상담', href:'counsel.html' },
      { label:'강의 요청·건의함', href:'request.html' },
      { label:'자료실', href:'resources.html' }
    ]}
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
  // 홈/로고 클릭: 이미 홈(index)에 있으면 해시 제거 후 맨 위로 (엉뚱한 위치로 가는 문제 방지)
  window.__biblyHome = function(e){
    var p = location.pathname;
    var onIndex = p === '/' || p === '/index.html' || /\/index\.html$/.test(p) || p.charAt(p.length-1) === '/';
    if(onIndex){
      if(e && e.preventDefault) e.preventDefault();
      if(location.hash){ try{ history.replaceState(null,'',p); }catch(_){} }
      window.scrollTo({ top:0, behavior:'smooth' });
      return false;
    }
    return true;
  };

  var LOGO =
    '<a href="index.html" onclick="return __biblyHome(event)" class="flex items-center gap-2 shrink-0">'
    + '<svg class="w-9 h-9 shrink-0" viewBox="0 0 48 48" role="img" aria-label="BIBLY"><rect x="9" y="9" width="30" height="30" rx="6" transform="rotate(45 24 24)" fill="#b8923f"/><text x="24" y="32.5" text-anchor="middle" font-family="Georgia, serif" font-size="22" font-weight="700" fill="#213a6b">B</text></svg>'
    + '<span class="leading-none"><span class="block font-extrabold text-[15px] tracking-tight">BIBLY<span class="text-gold">.</span></span>'
    + '<span class="block text-[9px] text-ink/45 tracking-wide mt-0.5">말씀으로 시대를 읽다</span></span></a>';

  var mount, active;

  function _hrefOf(h){ return String(h).charAt(0) === '#' ? ('index.html' + h) : h; }
  function _isOn(h){ return _hrefOf(h).split('?')[0] === active; }
  function menuHTML(menu){
    return menu.map(function(m){
      var href = _hrefOf(m.href), kids = m.children || [];
      var on = _isOn(m.href) || kids.some(function(c){ return _isOn(c.href); });
      var cls = on ? 'text-gold font-semibold biblyOn' : 'hover:text-gold';
      if(!kids.length) return '<a href="' + href + '" class="biblyTop whitespace-nowrap ' + cls + '">' + esc(m.label) + '</a>';
      var caret = '<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" class="ml-0.5 opacity-60"><path d="M6 9l6 6 6-6"/></svg>';
      var sub = kids.map(function(c){ return '<a href="' + _hrefOf(c.href) + '">' + esc(c.label) + '</a>'; }).join('');
      return '<div class="navItem"><a href="' + href + '" class="biblyTop whitespace-nowrap inline-flex items-center ' + cls + '">' + esc(m.label) + caret + '</a>'
        + '<div class="navDrop"><div class="navDropCard">' + sub + '</div></div></div>';
    }).join('');
  }

  // 메인 헤더 우측 CTA — 두란노식 강조 '바로 수강' + 내 강의실(로그인/로그아웃은 상단 퀵바)
  function mainCtaHTML(){
    return '<a href="watch.html" class="inline-flex items-center gap-1 bg-gold text-white font-bold px-3.5 py-1.5 rounded-full hover:opacity-90 transition text-xs whitespace-nowrap shadow-soft">▶ 바로 수강</a>'
      + '<a href="mylearning.html" class="hidden xl:inline-flex items-center gap-1 border border-gold/45 text-gold font-semibold px-3 py-1.5 rounded-full hover:bg-gold/10 transition text-xs whitespace-nowrap">📚 내 강의실</a>';
  }
  // 상단 퀵바(유틸리티) — 수학싸부식: 공지·이벤트·후원 + 로그인 상태/마이메뉴
  function topbarHTML(){
    var sep = '<span class="sep hidden sm:inline">·</span>';
    var common = '<a href="notices.html">📢 공지사항</a>' + sep
      + '<a href="event.html" class="font-semibold">🎁 혜택 이벤트</a>' + sep
      + '<a href="support.html" class="hidden sm:inline">♥ 후원</a>';
    var s = readStored(), right;
    if(s && s.user){
      var nm = (s.user.user_metadata && (s.user.user_metadata.full_name || s.user.user_metadata.name)) || (s.user.email ? s.user.email.split('@')[0] : '회원');
      var admin = (s.user.email === ADMIN) ? sep + '<a href="admin.html" class="!text-gold font-semibold">⚙ 관리자</a>' : '';
      right = '<span id="biblyAuthName" class="font-semibold !text-paper/90">' + esc(nm) + '님</span>' + sep
        + '<a href="mylearning.html" class="hidden sm:inline">📚 마이</a>' + sep
        + '<a href="bible-plan.html" class="hidden sm:inline">📖 성경 통독</a>' + sep
        + common + admin + sep
        + '<button onclick="__biblyLogout()">로그아웃</button>';
    } else {
      right = common + sep + '<button onclick="__biblyHeaderLoginClick()" class="font-semibold !text-gold">로그인</button>';
    }
    return '<div class="bibly-topbar bg-ink text-xs"><div class="max-w-7xl mx-auto px-4 h-9 flex items-center justify-end gap-x-2.5 overflow-x-auto">' + right + '</div></div>';
  }

  // 모바일 드롭다운 메뉴(햄버거)
  function mobileMenuHTML(menu){
    var items = menu.map(function(m){
      var href = _hrefOf(m.href), kids = m.children || [];
      if(!kids.length) return '<a href="' + href + '" class="py-3 border-b border-ink/5 ' + (_isOn(m.href) ? 'text-gold font-semibold' : 'text-ink/75') + '">' + esc(m.label) + '</a>';
      var head = '<a href="' + href + '" class="pt-3 pb-1 font-bold ' + (_isOn(m.href) ? 'text-gold' : 'text-ink/80') + '">' + esc(m.label) + '</a>';
      var sub = kids.map(function(c){ return '<a href="' + _hrefOf(c.href) + '" class="py-2 pl-4 border-b border-ink/5 text-[14px] ' + (_isOn(c.href) ? 'text-gold font-semibold' : 'text-ink/60') + '">└ ' + esc(c.label) + '</a>'; }).join('');
      return head + sub;
    }).join('');
    return '<div class="max-w-6xl mx-auto px-4 py-1 flex flex-col text-[15px]">' + items
      + '<a href="mylearning.html" class="py-3 border-b border-ink/5 text-gold font-semibold">📚 내 강의실</a>'
      + '<a href="index.html" onclick="return __biblyHome(event)" class="py-3 text-ink/55">🏠 홈</a>'
      + '</div>';
  }
  window.__biblyToggleMenu = function(){ var m = document.getElementById('biblyMobMenu'); if(m) m.classList.toggle('hidden'); };

  function headerHTML(menu){
    return topbarHTML()
      + '<header class="sticky top-0 z-40 bg-paper/90 backdrop-blur border-b border-ink/8">'
      + '<div class="max-w-7xl mx-auto px-4 h-14 flex items-center gap-3">'
      + LOGO
      + '<nav id="navmenu" class="hidden xl:flex items-center gap-5 text-[14.5px] font-medium text-[#15223d] whitespace-nowrap pl-1">' + menuHTML(menu) + '</nav>'
      + '<div class="ml-auto flex items-center gap-2 sm:gap-3 text-sm shrink-0">' + mainCtaHTML()
      + '<button id="biblyHamb" aria-label="메뉴 열기" onclick="__biblyToggleMenu()" class="xl:hidden w-9 h-9 -mr-1 flex items-center justify-center rounded-lg hover:bg-ink/5 text-ink/70"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 6h16M4 12h16M4 18h16"/></svg></button>'
      + '</div>'
      + '</div>'
      + '<div id="biblyMobMenu" class="xl:hidden hidden border-t border-ink/8 bg-paper/95 backdrop-blur shadow-sm max-h-[calc(100dvh-6.5rem)] overflow-y-auto overscroll-contain">' + mobileMenuHTML(menu) + '</div>'
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

  // 공통 푸터(하위 페이지) — 이미 footer가 있는 페이지는 건너뜀
  var YT = 'https://www.youtube.com/channel/UC82IOMnZud8NNt3BYzAxTMg';
  function footerHTML(){
    function lnk(href, label, cls){ return '<a href="' + href + '" class="hover:text-gold transition ' + (cls||'') + '">' + label + '</a>'; }
    return '<footer class="bibly-footer bg-paper border-t border-ink/10 py-12 mt-16">'
      + '<div class="max-w-6xl mx-auto px-5 flex flex-col md:flex-row justify-between gap-8">'
      + '<div class="max-w-md">'
      + '<p class="font-bold text-lg">BIBLY<span class="text-gold">.</span> <span class="text-ink/50 text-sm font-normal">바이블 인사이트</span></p>'
      + '<p class="text-sm mt-2 text-ink/60 leading-relaxed">말씀으로 시대를 읽다 · 유튜브 「오광일의 인사이트 브리핑」 공식 강의 플랫폼</p>'
      + '<p class="text-sm mt-3 text-ink/50">✉ contact@biblynote.com</p>'
      + '<p class="text-xs mt-3 text-ink/35 leading-relaxed">본 사이트 강의 영상의 무단 다운로드·녹화·재배포를 금합니다.</p>'
      + '</div>'
      + '<div class="grid grid-cols-2 gap-x-10 gap-y-2.5 text-sm text-ink/60 shrink-0">'
      + lnk('curriculum.html', '커리큘럼') + lnk('academy.html', '정규 심화 과정')
      + lnk('about.html', '우리의 사명') + lnk('community.html', '질문·나눔')
      + lnk('resources.html', '자료실') + lnk('request.html', '강의 요청·건의')
      + lnk('mylearning.html', '내 강의실') + lnk(YT, '▶ 유튜브 채널', '')
      + lnk('support.html', '♥ 후원 안내') + lnk('terms.html', '이용약관·환불 규정')
      + '</div>'
      + '</div>'
      + '<p class="text-center text-ink/30 text-xs mt-10">© 2026 BIBLY · 바이블 인사이트 (오광일의 인사이트 브리핑). All rights reserved.</p>'
      + '</footer>';
  }

  function injectNavCSS(){
    if(document.getElementById('biblyNavCSS')) return;
    var st = document.createElement('style'); st.id = 'biblyNavCSS';
    st.textContent = '.navItem{position:relative}.navItem>a{cursor:pointer}'
      + '.biblyTop{position:relative;padding:6px 2px;letter-spacing:-.005em;transition:color .18s}'
      + '.biblyTop::after{content:"";position:absolute;left:2px;right:2px;bottom:0;height:2px;background:linear-gradient(90deg,#b8923f,#dcb866);border-radius:2px;transform:scaleX(0);transform-origin:left;transition:transform .22s cubic-bezier(.4,0,.2,1)}'
      + '.biblyTop:hover::after,.navItem:hover>.biblyTop::after,.biblyOn::after{transform:scaleX(1)}'
      + '.navDrop{position:absolute;left:0;top:100%;padding-top:12px;opacity:0;visibility:hidden;transform:translateY(6px);transition:opacity .16s,transform .16s,visibility .16s;z-index:60}'
      + '.navItem:hover .navDrop{opacity:1;visibility:visible;transform:none}'
      + '.navDropCard{background:#fff;border:1px solid rgba(21,32,58,.08);border-radius:.9rem;box-shadow:0 18px 50px -20px rgba(21,32,58,.45);padding:.45rem;min-width:212px}'
      + '.navDropCard a{display:flex;align-items:center;gap:.6rem;padding:.62rem .85rem;border-radius:.65rem;font-size:.9rem;font-weight:600;color:#15223d;white-space:nowrap;transition:background .15s,color .15s,transform .15s}'
      + '.navDropCard a::before{content:"";width:6px;height:6px;border-radius:50%;background:rgba(184,146,63,.4);flex:none;transition:transform .15s,background .15s}'
      + '.navDropCard a:hover{background:#eef3fb;color:#b8923f;transform:translateX(2px)}'
      + '.navDropCard a:hover::before{background:#b8923f;transform:scale(1.4)}'
      + '.bibly-topbar a,.bibly-topbar button{color:rgba(247,249,252,.72);white-space:nowrap;transition:color .15s}'
      + '.bibly-topbar a:hover,.bibly-topbar button:hover{color:#dcb866}'
      + '.bibly-topbar .sep{color:rgba(247,249,252,.22)}'
      + '.bibly-topbar>div{scrollbar-width:none}.bibly-topbar>div::-webkit-scrollbar{display:none}';
    document.head.appendChild(st);
  }
  function build(){
    mount = document.getElementById('siteHeader');
    if(!mount) return;
    injectNavCSS();
    active = mount.getAttribute('data-active') || (location.pathname.split('/').pop() || 'index.html');
    // 1) 기본 메뉴로 즉시 렌더(깜빡임 방지)
    mount.outerHTML = headerHTML(DEFAULT_MENU);
    // 2) site.json 으로 메뉴 보강(nav=그룹 우선, 없으면 menu)
    fetch('content/site.json?t=' + Date.now()).then(function(r){ return r.json(); }).then(function(s){
      var mn = (s && s.nav && s.nav.length) ? s.nav : (s && s.menu);
      if(mn){
        var nav = document.getElementById('navmenu'); if(nav){ nav.className = nav.className.replace('text-ink/90','text-[#15223d]'); nav.innerHTML = menuHTML(mn); }
        var mob = document.getElementById('biblyMobMenu'); if(mob) mob.innerHTML = mobileMenuHTML(mn);
      }
    }).catch(function(){});
    // 3) 로그인 이름 보강
    refineName(readStored());
    // 4) 공통 푸터(기존 footer 없을 때만)
    try{
      if(!document.querySelector('footer')){
        var wrap = document.createElement('div'); wrap.innerHTML = footerHTML();
        document.body.appendChild(wrap.firstChild);
      }
    }catch(e){}
  }

  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', build);
  else build();
})();
