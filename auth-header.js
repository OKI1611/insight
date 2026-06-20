/* 공통 헤더 인증 위젯 — #authArea 에 '내 강의실 + 로그인/로그아웃'을 렌더
   라이브러리 불필요(로컬 세션만 읽음). 모든 페이지 헤더에서 동일하게 표시 */
(function(){
  // ===== 채널톡(Channel.io) 실시간 상담 위젯 — 모든 페이지 공통 =====
  // 수강생이 채팅을 시작하면 대표강사 휴대폰/PC 앱으로 알림이 오고, 부재중이면
  // 채널톡 '운영시간·부재중 메시지'가 자동으로 정중한 안내를 보냅니다.
  try{
    (function(){var w=window;if(w.ChannelIO){return;}var ch=function(){ch.c(arguments);};ch.q=[];ch.c=function(args){ch.q.push(args);};w.ChannelIO=ch;function l(){if(w.ChannelIOInitialized){return;}w.ChannelIOInitialized=true;var s=document.createElement("script");s.type="text/javascript";s.async=true;s.src="https://cdn.channel.io/plugin/ch-plugin-web.js";var x=document.getElementsByTagName("script")[0];if(x.parentNode){x.parentNode.insertBefore(s,x);}}if(document.readyState==="complete"){l();}else{w.addEventListener("DOMContentLoaded",l);w.addEventListener("load",l);}})();
    ChannelIO('boot', { pluginKey: '37797b37-e00a-4c2f-8767-16d8fb3dcfd2', hideChannelButtonOnBoot: true });
  }catch(e){}
  // 우리 디자인의 '무엇이든 물어보세요' 버튼 → 채널톡 상담창 열기 (미로드 시 Q&A 게시판 폴백)
  window.__biblyChat = function(){
    if(window.ChannelIO){ try{ ChannelIO('showMessenger'); return; }catch(e){} }
    location.href = 'community.html?board=qna';
  };

  // 간단한 방문 통계 — 세션당 1회, 비로그인 포함 (Supabase REST, 비차단)
  try{
    if(!sessionStorage.getItem('_bv')){
      sessionStorage.setItem('_bv','1');
      var SB='https://bmxkndkwefdgsomlznoo.supabase.co';
      var AK='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJteGtuZGt3ZWZkZ3NvbWx6bm9vIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODA1NzAwODIsImV4cCI6MjA5NjE0NjA4Mn0.l1yHhMVYwMqYSL8ub9PtrJPOl7CYr7yqstG2AER1EaU';
      fetch(SB+'/rest/v1/site_visits',{method:'POST',headers:{apikey:AK,'Content-Type':'application/json',Prefer:'return=minimal'},body:JSON.stringify({path:location.pathname})}).catch(function(){});
    }
  }catch(e){}

  // ===== PWA 자동 업데이트 (모든 페이지) =====
  // 설치형 앱이 새 배포를 자동 감지해 최신 상태로 갱신한다.
  try{
    if('serviceWorker' in navigator){
      var __biHadCtrl = !!navigator.serviceWorker.controller;
      var __biReloading = false;
      var __biReload = function(){ if(__biReloading) return; __biReloading = true; location.reload(); };
      // 1) 새 서비스워커가 활성화되면(=새 버전 배포) 자동 새로고침
      navigator.serviceWorker.addEventListener('controllerchange', function(){ if(__biHadCtrl) __biReload(); });
      // 2) 콘텐츠 변경 감지: 현재 문서의 ETag가 바뀌면 갱신
      var __biTag = null;
      var __biGetTag = function(cb){
        try{
          fetch(location.href, { cache:'no-store', method:'HEAD' }).then(function(r){
            var t = r.headers.get('ETag') || r.headers.get('Last-Modified') || '';
            if(t){ cb(t); }
            else { fetch(location.href, { cache:'no-store' }).then(function(r2){ cb(r2.headers.get('ETag') || r2.headers.get('Last-Modified') || ''); }).catch(function(){}); }
          }).catch(function(){});
        }catch(e){}
      };
      var __biShowUpdate = function(){
        if(document.getElementById('biblyUpdateBar')) return;
        var a = document.activeElement;
        var typing = a && (a.tagName === 'INPUT' || a.tagName === 'TEXTAREA' || a.isContentEditable);
        if(!typing){ __biReload(); return; }   // 입력 중이 아니면 즉시 자동 새로고침
        var bar = document.createElement('div');  // 입력 중이면 작성 내용 보호 위해 '탭하여 새로고침' 배너
        bar.id = 'biblyUpdateBar';
        bar.style.cssText = 'position:fixed;left:50%;transform:translateX(-50%);bottom:78px;z-index:2147483647;background:#2b3440;color:#f8f9f6;padding:11px 18px;border-radius:9999px;box-shadow:0 10px 34px rgba(0,0,0,.32);font-size:14px;display:flex;gap:10px;align-items:center;cursor:pointer;font-family:Pretendard,system-ui,sans-serif';
        bar.innerHTML = '<span>🔄 새로운 내용이 있어요</span><b style="color:#cfe0cf">새로고침</b>';
        bar.onclick = __biReload;
        if(document.body) document.body.appendChild(bar);
      };
      var __biCheck = function(){
        __biGetTag(function(t){
          if(!t) return;
          if(__biTag === null){ __biTag = t; return; }   // 최초엔 기준값만 설정
          if(t !== __biTag){ __biTag = t; __biShowUpdate(); }
        });
      };
      window.addEventListener('load', function(){
        navigator.serviceWorker.register('/sw.js').then(function(reg){ try{ reg.update(); }catch(e){} }).catch(function(){});
        __biCheck();
      });
      // 앱을 다시 열거나 탭으로 돌아올 때마다 최신 여부 점검
      document.addEventListener('visibilitychange', function(){
        if(document.visibilityState === 'visible'){
          __biCheck();
          try{ navigator.serviceWorker.getRegistration().then(function(r){ if(r) r.update(); }).catch(function(){}); }catch(e){}
        }
      });
    }
  }catch(e){}

  // 후원 링크 — 가볍고 빠른 전용 후원 페이지로
  var SUP = 'support.html';

  // ===== 접근성·질문 플로팅 UI (모든 페이지) =====
  try{
    if(document.body && !document.getElementById('biblyFab')){
      var SIZES = ['15px','17px','19px','21px'];
      window.__biblyFont = function(d){
        var cur = document.documentElement.style.fontSize || '17px';
        var i = SIZES.indexOf(cur); if(i < 0) i = 1;
        i = Math.max(0, Math.min(SIZES.length - 1, i + d));
        document.documentElement.style.fontSize = SIZES[i];
        try{ localStorage.setItem('biblyFont', SIZES[i]); }catch(e){}
      };
      var w = document.createElement('div'); w.id = 'biblyFab';
      w.innerHTML =
        '<div style="position:fixed;left:12px;bottom:calc(14px + env(safe-area-inset-bottom));z-index:60" class="flex items-center gap-0.5 bg-white/95 backdrop-blur border border-ink/10 rounded-full shadow-lg px-1.5 py-1">'
        + '<span style="font-size:11px" class="text-ink/45 px-1 select-none">글자</span>'
        + '<button onclick="__biblyFont(-1)" aria-label="글자 작게" class="rounded-full hover:bg-ink/5 text-ink/60" style="width:34px;height:34px;font-size:13px">가&minus;</button>'
        + '<button onclick="__biblyFont(1)" aria-label="글자 크게" class="rounded-full hover:bg-ink/5 text-ink font-bold" style="width:34px;height:34px;font-size:18px">가&#43;</button>'
        + '</div>'
        + '<div style="position:fixed;right:14px;bottom:calc(18px + env(safe-area-inset-bottom));z-index:60" class="flex flex-col items-end gap-2.5">'
        + '<button id="installBtn" onclick="__biblyOpenInstall()" aria-label="앱 설치" class="inline-flex items-center gap-1.5 bg-ink text-white font-bold rounded-full shadow-xl hover:bg-navy transition" style="display:none;padding:11px 18px;font-size:15px"><span style="font-size:18px">📱</span> 앱 설치</button>'
        + '<a href="' + SUP + '" aria-label="후원하기" class="inline-flex items-center gap-1.5 bg-rose-500 text-white font-bold rounded-full shadow-xl hover:bg-rose-600 transition" style="padding:11px 18px;font-size:15px"><span style="font-size:17px">♥</span> 후원</a>'
        + '<button onclick="__biblyChat()" aria-label="무엇이든 질문하기" class="inline-flex items-center gap-2 bg-gold text-white font-bold rounded-full shadow-xl hover:opacity-95 transition" style="border:none;cursor:pointer">'
        + '<span style="padding:13px 0 13px 18px;font-size:20px">💬</span>'
        + '<span class="hidden sm:inline" style="padding-right:20px;font-size:15px">무엇이든 물어보세요</span>'
        + '<span class="sm:hidden" style="padding-right:16px;font-size:14px">질문</span>'
        + '</button>'
        + '</div>';
      document.body.appendChild(w);

      // ===== PWA 앱 설치 (모든 페이지 공통) =====
      if(!document.getElementById('installModal')){
        var im = document.createElement('div');
        im.id = 'installModal'; im.style.display = 'none';
        im.className = 'fixed inset-0 z-[120] items-center justify-center bg-black/60 p-4';
        im.innerHTML =
            '<div class="bg-white rounded-2xl p-6 max-w-sm w-full shadow-2xl" style="color:#1a1a1a">'
          + '<div class="flex items-center gap-3 mb-4"><img src="/images/icon-192.png" alt="BIBLY" style="width:46px;height:46px;border-radius:13px"/>'
          + '<div><h3 class="font-bold text-lg leading-tight">BIBLY 앱으로 설치</h3><p class="text-xs text-gray-500 mt-0.5">홈 화면에 추가하면 앱처럼 전체화면으로 열려요</p></div></div>'
          + '<div id="installAndroid" style="display:none"><p class="text-sm text-gray-600 mb-4">아래 버튼을 누르면 설치 창이 떠요. <b>‘설치’</b>를 선택하면 끝입니다!</p>'
          + '<button onclick="__biblyPwaInstall()" class="w-full py-3 rounded-xl font-semibold text-sm transition" style="background:#2b3440;color:#f8f9f6">지금 설치하기</button></div>'
          + '<div id="installAndroidManual" style="display:none"><ol class="text-sm text-gray-700 space-y-3">'
          + '<li class="flex gap-2"><span style="color:#2b3440;font-weight:700">1.</span><span>브라우저 오른쪽 위 <b>⋮ 메뉴</b>(점 3개)를 누르세요.</span></li>'
          + '<li class="flex gap-2"><span style="color:#2b3440;font-weight:700">2.</span><span><b>‘앱 설치’</b> 또는 <b>‘홈 화면에 추가’</b>를 누르세요.</span></li>'
          + '<li class="flex gap-2"><span style="color:#2b3440;font-weight:700">3.</span><span><b>‘설치’</b>를 누르면 완료 — 홈 화면에 BIBLY 앱이 생겨요!</span></li>'
          + '</ol><p class="text-xs text-gray-400 mt-3">※ 삼성 인터넷·크롬에서 진행해 주세요.</p></div>'
          + '<div id="installIOS" style="display:none"><ol class="text-sm text-gray-700 space-y-3">'
          + '<li class="flex gap-2"><span style="color:#2b3440;font-weight:700">1.</span><span>화면 아래(또는 위)의 <b>공유 버튼</b>(네모 상자에서 위로 향한 <b>↑ 화살표</b> 모양)을 누르세요.</span></li>'
          + '<li class="flex gap-2"><span style="color:#2b3440;font-weight:700">2.</span><span>메뉴를 아래로 내려 <b>‘홈 화면에 추가’</b>를 누르세요.</span></li>'
          + '<li class="flex gap-2"><span style="color:#2b3440;font-weight:700">3.</span><span>오른쪽 위 <b>‘추가’</b>를 누르면 완료 — 홈 화면에 BIBLY 앱이 생겨요!</span></li>'
          + '</ol><p class="text-xs text-gray-400 mt-3">※ 아이폰은 반드시 <b>사파리(Safari)</b> 브라우저에서 진행해 주세요.</p></div>'
          + '<div id="installOther" style="display:none"><p class="text-sm text-gray-600">브라우저 주소창의 <b>설치 아이콘(⊕)</b>을 누르거나, 메뉴에서 <b>‘앱 설치 / 페이지를 앱으로 설치’</b>를 선택하세요.</p></div>'
          + '<button onclick="document.getElementById(\'installModal\').style.display=\'none\'" class="mt-5 w-full py-2.5 rounded-xl bg-gray-100 hover:bg-gray-200 font-semibold text-sm">닫기</button>'
          + '</div>';
        im.onclick = function(e){ if(e.target === im) im.style.display = 'none'; };
        document.body.appendChild(im);

        var biDP = null;
        var biStandalone = window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone === true;
        var biIOS = /iphone|ipad|ipod/i.test(navigator.userAgent) && !window.MSStream;
        var biAndroid = /android/i.test(navigator.userAgent);
        var __biReveal = function(){ if(biStandalone) return; var b = document.getElementById('installBtn'); if(b) b.style.display = 'inline-flex'; };
        window.addEventListener('beforeinstallprompt', function(e){ e.preventDefault(); biDP = e; __biReveal(); });
        // 앱으로 실행 중(standalone)만 아니면 항상 '앱 설치' 버튼 노출
        // (UA 감지에 의존하지 않음 — 일부 모바일 환경에서 버튼이 안 뜨던 문제 해결)
        if(!biStandalone) __biReveal();
        window.__biblyOpenInstall = function(){
          document.getElementById('installAndroid').style.display = biDP ? 'block' : 'none';
          document.getElementById('installAndroidManual').style.display = (biAndroid && !biDP) ? 'block' : 'none';
          document.getElementById('installIOS').style.display = (biIOS && !biDP) ? 'block' : 'none';
          document.getElementById('installOther').style.display = (!biDP && !biIOS && !biAndroid) ? 'block' : 'none';
          document.getElementById('installModal').style.display = 'flex';
        };
        window.__biblyPwaInstall = function(){
          if(!biDP) return;
          document.getElementById('installModal').style.display = 'none';
          biDP.prompt(); biDP.userChoice.then(function(){ biDP = null; var b = document.getElementById('installBtn'); if(b) b.style.display = 'none'; });
        };
        window.addEventListener('appinstalled', function(){ var b = document.getElementById('installBtn'); if(b) b.style.display = 'none'; var m = document.getElementById('installModal'); if(m) m.style.display = 'none'; });
      }

      // 스크롤 내릴 때 플로팅 버튼 숨김(콘텐츠 가림 방지), 올리거나 상단이면 표시
      (function(){
        var cols = w.children;   // [좌: 글자크기, 우: 설치/후원/질문]
        var lastY = window.pageYOffset || 0, hid = null;
        function setHid(h){
          if(h === hid) return; hid = h;
          for(var i = 0; i < cols.length; i++){
            var c = cols[i];
            c.style.transition = 'transform .28s ease, opacity .28s ease';
            c.style.transform = h ? 'translateY(170%)' : '';
            c.style.opacity = h ? '0' : '';
            c.style.pointerEvents = h ? 'none' : '';
          }
        }
        // 플로팅 버튼은 항상 표시 — 모바일에서 스크롤 시 후원·앱설치·질문 버튼이
        // 사라져 '안 보인다'는 피드백 반영. (작고 모서리에 있어 콘텐츠를 거의 가리지 않음)
        if(hid) setHid(false);
        void lastY; void biNarrow;
      })();
    }
  }catch(e){}

  var el = document.getElementById('authArea');
  if(!el) return;
  function readStored(){
    try{
      for(var i=0;i<localStorage.length;i++){
        var k = localStorage.key(i);
        if(!/auth-token/.test(k)) continue;
        var v = JSON.parse(localStorage.getItem(k));
        var s = (v && v.user) ? v : (v && v.currentSession) ? v.currentSession : null;
        if(s && s.user){ if(s.expires_at && s.expires_at*1000 < Date.now()) return null; return s; }
      }
    }catch(e){}
    return null;
  }
  window.__biblyLogout = function(){
    try{ for(var i=localStorage.length-1;i>=0;i--){ var k=localStorage.key(i); if(/-auth-token/.test(k)) localStorage.removeItem(k); } }catch(e){}
    location.reload();
  };
  function render(){
    var loggedIn = !!readStored();
    var support = '<a href="' + SUP + '" aria-label="후원하기" title="후원하기" class="inline-flex items-center justify-center w-8 h-8 rounded-full bg-rose-500/10 text-rose-500 border border-rose-300 hover:bg-rose-500 hover:text-white transition shrink-0" style="font-size:15px">♥</a>';
    if(loggedIn){
      el.innerHTML =
        '<a href="mylearning.html" class="inline-flex items-center gap-1 bg-gold text-white font-semibold px-3 py-1.5 rounded-full hover:opacity-90 transition text-xs whitespace-nowrap">📚 내 강의실</a>'
      + support
      + '<button onclick="__biblyLogout()" class="text-ink/45 hover:text-gold text-sm whitespace-nowrap">로그아웃</button>';
    } else {
      el.innerHTML =
        '<a href="mylearning.html" class="inline-flex items-center gap-1 border border-gold/45 text-gold font-semibold px-3 py-1.5 rounded-full hover:bg-gold/10 transition text-xs whitespace-nowrap">📚 내 강의실</a>'
      + support
      + '<a href="index.html" class="bg-gold text-white font-semibold px-3 py-1.5 rounded-full hover:opacity-90 transition text-xs whitespace-nowrap">로그인</a>';
    }
  }
  render();
})();
