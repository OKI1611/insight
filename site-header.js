/* site-header.js — 공통 헤더 컴포넌트 (모든 하위 페이지 공용)
   사용법: 본문 맨 위에 <div id="siteHeader" data-active="community.html"></div> 를 두고,
           <head> 에서 <script src="/site-header.js"></script> 로 불러온다.
   - 로고 + 메뉴(content/site.json, 없으면 기본값) + 인증영역(내 강의실 · 후원 · 로그인/로그아웃)을 그린다.
   - 로그인 모달이 필요한 페이지는 window.biblyHeaderLogin 함수를 정의하면 '로그인' 클릭 시 그 함수가 호출된다(없으면 index.html 로 이동).
   - <head> 로드(=content-loader.js 와 동일)라 미리보기 환경에서도 실행됨. */
(function(){
  if(window.__biblyHeaderInit) return; window.__biblyHeaderInit = true;
  var SB = 'https://bmxkndkwefdgsomlznoo.supabase.co';
  var AK = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJteGtuZGt3ZWZkZ3NvbWx6bm9vIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODA1NzAwODIsImV4cCI6MjA5NjE0NjA4Mn0.l1yHhMVYwMqYSL8ub9PtrJPOl7CYr7yqstG2AER1EaU';
  var ADMIN = 'josephoh1611@gmail.com';
  var DEFAULT_MENU = [
    { label:'소개', href:'about.html', children:[
      { label:'우리의 사명·소개', href:'about.html' },
      { label:'강사 소개', href:'about.html#instructor' },
      { label:'설립 이야기 · 간증', href:'about.html#story' },
      { label:'1기 창립 멤버', href:'founding.html' }
    ]},
    { label:'강의·커리큘럼', href:'curriculum.html', children:[
      { label:'전체 커리큘럼', href:'curriculum.html' },
      { label:'정규 심화 과정(아카데미)', href:'academy.html' },
      { label:'나에게 맞는 강의 찾기', href:'find.html' }
    ]},
    { label:'성경', href:'bible.html', children:[
      { label:'성경 읽기', href:'bible.html' },
      { label:'매일 말씀과 함께', href:'daily.html' },
      { label:'성경암송 365', href:'memorize.html' },
      { label:'성경 통독표 (1년 1독)', href:'bible-plan.html' },
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
      { label:'자료실', href:'resources.html' },
      { label:'칼럼', href:'column.html' }
    ]},
    { label:'스토어', href:'booklet.html', children:[
      { label:'PDF 책자·이용권', href:'booklet.html' },
      { label:'선물·후원 좌석', href:'gift.html' },
      { label:'고객센터(주문·배송·반품)', href:'store-help.html' },
      { label:'내 구매·자료', href:'mylearning.html' }
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
    + '<img src="/images/logo-bible-insight.png?v=2" alt="바이블 인사이트 로고" class="h-9 md:h-10 w-auto shrink-0" />'
    + '<span class="leading-none text-left"><span class="block font-bold text-[18px] tracking-tight text-neutral-900">바이블 인사이트<span class="text-gold">.</span></span>'
    + '<span class="inline-flex items-center gap-1.5 mt-0.5"><span class="h-px w-4 bg-gold/40"></span><span class="text-[9px] font-semibold text-gold tracking-[0.3em]">ACADEMY</span></span></span></a>';

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
    return '<a href="search.html" aria-label="스마트 검색" title="스마트 검색" class="inline-flex items-center justify-center w-9 h-9 rounded-full hover:bg-ink/5 text-neutral-900/70"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.4-3.4"/></svg></a>'
      + '<a href="watch.html" class="inline-flex items-center gap-1 bg-gold text-white font-bold px-3.5 py-1.5 rounded-full hover:opacity-90 transition text-xs whitespace-nowrap shadow-soft">▶ 바로 수강</a>'
      + '<a href="mylearning.html" class="hidden xl:inline-flex items-center gap-1 border border-gold/45 text-gold font-semibold px-3 py-1.5 rounded-full hover:bg-gold/10 transition text-xs whitespace-nowrap">내 강의실</a>';
  }
  // 상단 퀵바(유틸리티) — 수학싸부식: 공지·이벤트·후원 + 로그인 상태/마이메뉴
  function topbarHTML(){
    var sep = '<span class="sep hidden sm:inline">·</span>';
    var common = '<a href="notices.html">공지사항</a>' + sep
      + '<a href="event.html" class="font-semibold">혜택 이벤트</a>' + sep
      + '<a href="support.html" class="hidden sm:inline">후원</a>';
    var s = readStored(), right;
    if(s && s.user){
      var nm = (s.user.user_metadata && (s.user.user_metadata.full_name || s.user.user_metadata.name)) || (s.user.email ? s.user.email.split('@')[0] : '회원');
      var admin = (s.user.email === ADMIN) ? sep + '<a href="admin.html" class="!text-gold font-semibold">관리자</a>' : '';
      right = '<span id="biblyAuthName" class="font-semibold !text-paper/90">' + esc(nm) + '님</span>' + sep
        + '<a href="mylearning.html" class="hidden sm:inline">마이</a>' + sep
        + '<a href="bible-plan.html" class="hidden sm:inline">성경 통독</a>' + sep
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
      if(!kids.length) return '<a href="' + href + '" class="py-3 border-b border-ink/5 ' + (_isOn(m.href) ? 'text-gold font-semibold' : 'text-neutral-900/75') + '">' + esc(m.label) + '</a>';
      var head = '<a href="' + href + '" class="pt-3 pb-1 font-bold ' + (_isOn(m.href) ? 'text-gold' : 'text-neutral-900/80') + '">' + esc(m.label) + '</a>';
      var sub = kids.map(function(c){ return '<a href="' + _hrefOf(c.href) + '" class="py-2 pl-4 border-b border-ink/5 text-[14px] ' + (_isOn(c.href) ? 'text-gold font-semibold' : 'text-neutral-900/60') + '">└ ' + esc(c.label) + '</a>'; }).join('');
      return head + sub;
    }).join('');
    return '<div class="max-w-6xl mx-auto px-4 py-1 flex flex-col text-[15px]">'
      + '<a href="search.html" class="py-3 border-b border-ink/5 text-gold font-semibold">스마트 검색</a>' + items
      + '<a href="mylearning.html" class="py-3 border-b border-ink/5 text-gold font-semibold">내 강의실</a>'
      + '<a href="index.html" onclick="return __biblyHome(event)" class="py-3 text-neutral-900/55">홈</a>'
      + '</div>';
  }
  window.__biblyToggleMenu = function(){ var m = document.getElementById('biblyMobMenu'); if(m) m.classList.toggle('hidden'); };

  function headerHTML(menu){
    return topbarHTML()
      + '<header class="sticky top-0 z-40 bg-paper/90 backdrop-blur border-b border-ink/8">'
      + '<div class="max-w-7xl mx-auto px-4 h-14 flex items-center gap-3">'
      + LOGO
      + '<nav id="navmenu" class="hidden xl:flex items-center gap-5 text-[14.5px] font-medium text-neutral-900 whitespace-nowrap pl-1">' + menuHTML(menu) + '</nav>'
      + '<div class="ml-auto flex items-center gap-2 sm:gap-3 text-sm shrink-0">' + mainCtaHTML()
      + '<button id="biblyHamb" aria-label="메뉴 열기" onclick="__biblyToggleMenu()" class="xl:hidden w-9 h-9 -mr-1 flex items-center justify-center rounded-lg hover:bg-ink/5 text-neutral-900/70"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 6h16M4 12h16M4 18h16"/></svg></button>'
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
    function lnk(href, label){ return '<a href="' + href + '" class="text-neutral-600 hover:text-gold transition">' + label + '</a>'; }
    return '<footer class="bibly-footer bg-paper border-t border-neutral-200 pt-14 pb-10 mt-16">'
      + '<div class="max-w-6xl mx-auto px-5 grid gap-10 md:grid-cols-[1.5fr_1fr]">'
      + '<div class="max-w-md">'
      + '<p class="font-bold text-xl tracking-tight text-neutral-900">BIBLY<span class="text-gold">.</span> <span class="text-neutral-500 text-sm font-medium">바이블 인사이트</span></p>'
      + '<p class="text-sm mt-3 text-neutral-600 leading-relaxed">말씀으로 시대를 읽다 — 유튜브 「오광일의 인사이트 브리핑」 공식 강의 플랫폼</p>'
      + '<p class="text-sm mt-4 text-neutral-800 font-medium">contact@biblynote.com</p>'
      + '<p class="text-xs mt-4 text-neutral-400 leading-relaxed">본 사이트 강의 영상의 무단 다운로드·녹화·재배포를 금합니다.</p>'
      + '</div>'
      + '<nav class="grid grid-cols-2 gap-x-8 gap-y-3 text-sm">'
      + lnk('curriculum.html', '커리큘럼') + lnk('academy.html', '정규 심화 과정')
      + lnk('about.html', '우리의 사명') + lnk('community.html', '질문·나눔')
      + lnk('resources.html', '자료실') + lnk('request.html', '강의 요청·건의')
      + lnk('mylearning.html', '내 강의실') + lnk(YT, '유튜브 채널')
      + lnk('support.html', '후원 안내') + lnk('terms.html', '이용약관·환불 규정')
      + '</nav>'
      + '</div>'
      + '<p class="text-center text-neutral-400 text-xs mt-12 pt-7 border-t border-neutral-200 max-w-6xl mx-auto px-5">© 2026 BIBLY · 바이블 인사이트 (오광일의 인사이트 브리핑). All rights reserved.</p>'
      + '</footer>';
  }

  function injectNavCSS(){
    if(document.getElementById('biblyNavCSS')) return;
    var st = document.createElement('style'); st.id = 'biblyNavCSS';
    st.textContent = '.navItem{position:relative}.navItem>a{cursor:pointer}'
      + '.biblyTop{position:relative;padding:6px 2px;letter-spacing:-.005em;transition:color .18s}'
      + '.biblyTop::after{content:"";position:absolute;left:2px;right:2px;bottom:0;height:2px;background:linear-gradient(90deg,#00704a,#dcb866);border-radius:2px;transform:scaleX(0);transform-origin:left;transition:transform .22s cubic-bezier(.4,0,.2,1)}'
      + '.biblyTop:hover::after,.navItem:hover>.biblyTop::after,.biblyOn::after{transform:scaleX(1)}'
      + '.navDrop{position:absolute;left:0;top:100%;padding-top:12px;opacity:0;visibility:hidden;transform:translateY(6px);transition:opacity .16s,transform .16s,visibility .16s;z-index:60}'
      + '.navItem:hover .navDrop{opacity:1;visibility:visible;transform:none}'
      + '.navDropCard{background:#fff;border:1px solid rgba(21,32,58,.08);border-radius:.9rem;box-shadow:0 18px 50px -20px rgba(21,32,58,.45);padding:.45rem;min-width:212px}'
      + '.navDropCard a{display:flex;align-items:center;gap:.6rem;padding:.62rem .85rem;border-radius:.65rem;font-size:.9rem;font-weight:600;color:#171717;white-space:nowrap;transition:background .15s,color .15s,transform .15s}'
      + '.navDropCard a::before{content:"";width:6px;height:6px;border-radius:50%;background:rgba(0,112,74,.4);flex:none;transition:transform .15s,background .15s}'
      + '.navDropCard a:hover{background:#eef3fb;color:#00704a;transform:translateX(2px)}'
      + '.navDropCard a:hover::before{background:#00704a;transform:scale(1.4)}'
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
        var nav = document.getElementById('navmenu'); if(nav){ nav.className = nav.className.replace('text-neutral-900/90','text-neutral-900'); nav.innerHTML = menuHTML(mn); }
        var mob = document.getElementById('biblyMobMenu'); if(mob) mob.innerHTML = mobileMenuHTML(mn);
      }
      // 사업자 정보 공통 표기(전 페이지 하단 자동 · 이미 표기된 페이지는 건너뜀)
      try{
        var biz = s && s.business;
        if(biz && biz.reg_no && document.body.innerText.indexOf(biz.reg_no) < 0){
          var L = function(t){ return '<span style="color:#9ca3af">' + t + '</span> '; };
          var V = function(t){ return '<span style="color:#404040">' + t + '</span>'; };
          var S = '<span style="color:#d4d4d4;margin:0 10px">│</span>';
          var eco = biz.ecommerce_no ? ('신고 ' + biz.ecommerce_no) : '신고 준비 중';
          var addr = String(biz.address || '').replace('강남구', '<span style="color:#00704a;font-weight:600">강남구</span>');
          var bl = document.createElement('div');
          bl.setAttribute('data-bibly-bizinfo','');
          bl.style.cssText = 'max-width:1120px;margin:36px auto 0;padding:30px 20px 4px;text-align:center;border-top:1px solid #e5e5e5';
          bl.innerHTML =
            '<img src="/images/logo-bible-insight.png?v=2" alt="바이블 인사이트" style="height:34px;width:auto;display:block;margin:0 auto 13px"/>'
            + '<span style="display:inline-flex;align-items:center;gap:6px;border-radius:999px;background:rgba(0,112,74,.1);border:1px solid rgba(0,112,74,.25);padding:4px 14px;margin-bottom:13px;font-size:11px;font-weight:600;letter-spacing:.02em;color:#00704a">서울 강남 본부 · GANGNAM, SEOUL</span>'
            + '<div style="font-weight:700;font-size:13px;letter-spacing:.02em;color:#404040;margin-bottom:11px">BIBLY <span style="color:#00704a">·</span> 바이블 인사이트</div>'
            + '<div style="font-size:11.5px;line-height:2.05;color:#737373">'
            +   L('상호') + V(biz.name) + S + L('대표') + V(biz.ceo) + S + L('사업자등록번호') + V(biz.reg_no)
            +   '<br>' + L('통신판매업') + V(eco) + S + L('주소') + '<span style="color:#404040">' + addr + '</span>'
            +   (biz.contact_email ? '<br>' + L('문의') + V(biz.contact_email) : '')
            + '</div>';
          var f = document.querySelector('footer');
          if(f) f.appendChild(bl); else document.body.appendChild(bl);
        }
      }catch(e){}
      // 통신판매업 신고번호 단일화: data-biz="eco" 표시 자리를 site.json 값으로 채움
      //  (하드코딩 페이지 index·store-help·terms 도 site.json 한 곳만 고치면 자동 반영)
      try{
        var bz = s && s.business;
        var ecoTxt = (bz && bz.ecommerce_no) ? ('제 ' + bz.ecommerce_no + ' 호')
                     : ((bz && bz.ecommerce_status) ? bz.ecommerce_status : '신고 준비 중');
        var nodes = document.querySelectorAll('[data-biz="eco"]');
        for(var i=0;i<nodes.length;i++){ nodes[i].textContent = ecoTxt; }
      }catch(e){}
      // 왼쪽 퀵메뉴 바(전 페이지 공통 · 자주 쓰는 곳 바로가기 + 맨 위로)
      try{ buildQuickRail(s); }catch(e){}
    }).catch(function(){ try{ buildQuickRail(null); }catch(e){} });
    // 3) 로그인 이름 보강
    refineName(readStored());
    // 4) 공통 푸터(기존 footer 없을 때만)
    try{
      if(!document.querySelector('footer')){
        var wrap = document.createElement('div'); wrap.innerHTML = footerHTML();
        document.body.appendChild(wrap.firstChild);
      }
    }catch(e){}
    // 5) 왼쪽 퀵메뉴 바(site.json 흐름과 무관하게 항상 생성 · 중복 방지 가드 있음)
    try{ buildQuickRail(null); }catch(e){}
  }

  // 왼쪽 퀵메뉴 바(메가스터디식) — 자주 쓰는 곳 바로가기 + 맨 위로. 전 페이지 공통, 데스크톱 섹션 사이드바와 겹치면 자동 숨김.
  function buildQuickRail(s){
    if(document.getElementById('biblyRail')) return;
    var yt = (s && s.youtube && s.youtube.channel_url) || 'https://www.youtube.com/channel/UC82IOMnZud8NNt3BYzAxTMg';
    var items = [
      { ic:'▶', lb:'유튜브', href:yt, ext:true },
      { ic:'', lb:'성경', href:'bible.html' },
      { ic:'', lb:'사전', href:'dictionary.html' },
      { ic:'', lb:'강의', href:'curriculum.html' },
      { ic:'', lb:'교재구매', href:'booklet.html' },
      { ic:'', lb:'장바구니', href:'booklet.html#cart' },
      { ic:'', lb:'후원', href:'support.html' }
    ];
    if(!document.getElementById('biblyRailCSS')){
      var st = document.createElement('style'); st.id='biblyRailCSS';
      st.textContent =
        '#biblyRail{position:fixed;left:12px;top:50%;transform:translateY(-50%);z-index:44;display:flex;flex-direction:column;gap:1px;background:#fff;border:1px solid rgba(33,58,107,.1);border-radius:16px;box-shadow:0 12px 34px -14px rgba(21,32,58,.35);padding:6px}'
        + '#biblyRail a{display:flex;flex-direction:column;align-items:center;gap:2px;width:48px;padding:9px 0;border-radius:12px;text-decoration:none;color:#42506c;transition:background .15s,color .15s;cursor:pointer}'
        + '#biblyRail a:hover{background:#f4f7fc;color:#00704a}'
        + '#biblyRail .ic{font-size:17px;line-height:1}'
        + '#biblyRail .lb{font-size:10px;font-weight:700;letter-spacing:-.02em}'
        + '#biblyRail .rtop{border-top:1px solid rgba(33,58,107,.08);margin-top:3px;padding-top:9px;color:rgba(33,58,107,.45)}'
        + '@media(max-width:767px){#biblyRail{display:none}}';   // 모바일에선 본문 가림 방지로 숨김
      document.head.appendChild(st);
    }
    var rail = document.createElement('nav'); rail.id='biblyRail'; rail.setAttribute('aria-label','빠른 이동 메뉴');
    var html = items.map(function(it){
      return '<a href="'+it.href+'"'+(it.ext?' target="_blank" rel="noopener"':'')+' title="'+it.lb+'"><span class="ic">'+it.ic+'</span><span class="lb">'+it.lb+'</span></a>';
    }).join('');
    html += '<a class="rtop" title="맨 위로" onclick="window.scrollTo({top:0,behavior:\'smooth\'});return false;"><span class="ic">⤴</span><span class="lb">TOP</span></a>';
    rail.innerHTML = html;
    document.body.appendChild(rail);
    // 퀵바는 항상 화면 맨 왼쪽 가장자리에 고정
    rail.style.left = '12px'; rail.style.right = 'auto';
  }

  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', build);
  else build();
})();
