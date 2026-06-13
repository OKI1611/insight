/* 공통 헤더 인증 위젯 — #authArea 에 '내 강의실 + 로그인/로그아웃'을 렌더
   라이브러리 불필요(로컬 세션만 읽음). 모든 페이지 헤더에서 동일하게 표시 */
(function(){
  // 간단한 방문 통계 — 세션당 1회, 비로그인 포함 (Supabase REST, 비차단)
  try{
    if(!sessionStorage.getItem('_bv')){
      sessionStorage.setItem('_bv','1');
      var SB='https://bmxkndkwefdgsomlznoo.supabase.co';
      var AK='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJteGtuZGt3ZWZkZ3NvbWx6bm9vIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODA1NzAwODIsImV4cCI6MjA5NjE0NjA4Mn0.l1yHhMVYwMqYSL8ub9PtrJPOl7CYr7yqstG2AER1EaU';
      fetch(SB+'/rest/v1/site_visits',{method:'POST',headers:{apikey:AK,'Content-Type':'application/json',Prefer:'return=minimal'},body:JSON.stringify({path:location.pathname})}).catch(function(){});
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
        '<div style="position:fixed;left:12px;bottom:12px;z-index:55" class="flex items-center gap-0.5 bg-white/95 backdrop-blur border border-ink/10 rounded-full shadow-lg px-1.5 py-1">'
        + '<span style="font-size:11px" class="text-ink/45 px-1 select-none">글자</span>'
        + '<button onclick="__biblyFont(-1)" aria-label="글자 작게" class="rounded-full hover:bg-ink/5 text-ink/60" style="width:34px;height:34px;font-size:13px">가&minus;</button>'
        + '<button onclick="__biblyFont(1)" aria-label="글자 크게" class="rounded-full hover:bg-ink/5 text-ink font-bold" style="width:34px;height:34px;font-size:18px">가&#43;</button>'
        + '</div>'
        + '<div style="position:fixed;right:14px;bottom:14px;z-index:55" class="flex flex-col items-end gap-2.5">'
        + '<button id="installBtn" onclick="__biblyOpenInstall()" aria-label="앱 설치" class="inline-flex items-center gap-1.5 bg-ink text-white font-bold rounded-full shadow-xl hover:bg-navy transition" style="display:none;padding:11px 18px;font-size:15px"><span style="font-size:18px">📱</span> 앱 설치</button>'
        + '<a href="' + SUP + '" aria-label="후원하기" class="inline-flex items-center gap-1.5 bg-rose-500 text-white font-bold rounded-full shadow-xl hover:bg-rose-600 transition" style="padding:11px 18px;font-size:15px"><span style="font-size:17px">♥</span> 후원하기</a>'
        + '<a href="community.html?board=qna" aria-label="무엇이든 질문하기" class="inline-flex items-center gap-2 bg-gold text-white font-bold rounded-full shadow-xl hover:opacity-95 transition">'
        + '<span style="padding:13px 0 13px 18px;font-size:20px">💬</span>'
        + '<span class="hidden sm:inline" style="padding-right:20px;font-size:15px">무엇이든 물어보세요</span>'
        + '<span class="sm:hidden" style="padding-right:16px;font-size:14px">질문</span>'
        + '</a>'
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
          + '<button onclick="__biblyPwaInstall()" class="w-full py-3 rounded-xl font-semibold text-sm transition" style="background:#15203a;color:#fcfaf6">지금 설치하기</button></div>'
          + '<div id="installIOS" style="display:none"><ol class="text-sm text-gray-700 space-y-3">'
          + '<li class="flex gap-2"><span style="color:#15203a;font-weight:700">1.</span><span>화면 아래(또는 위)의 <b>공유 버튼</b>(네모 상자에서 위로 향한 <b>↑ 화살표</b> 모양)을 누르세요.</span></li>'
          + '<li class="flex gap-2"><span style="color:#15203a;font-weight:700">2.</span><span>메뉴를 아래로 내려 <b>‘홈 화면에 추가’</b>를 누르세요.</span></li>'
          + '<li class="flex gap-2"><span style="color:#15203a;font-weight:700">3.</span><span>오른쪽 위 <b>‘추가’</b>를 누르면 완료 — 홈 화면에 BIBLY 앱이 생겨요!</span></li>'
          + '</ol><p class="text-xs text-gray-400 mt-3">※ 아이폰은 반드시 <b>사파리(Safari)</b> 브라우저에서 진행해 주세요.</p></div>'
          + '<div id="installOther" style="display:none"><p class="text-sm text-gray-600">브라우저 주소창의 <b>설치 아이콘(⊕)</b>을 누르거나, 메뉴에서 <b>‘앱 설치 / 페이지를 앱으로 설치’</b>를 선택하세요.</p></div>'
          + '<button onclick="document.getElementById(\'installModal\').style.display=\'none\'" class="mt-5 w-full py-2.5 rounded-xl bg-gray-100 hover:bg-gray-200 font-semibold text-sm">닫기</button>'
          + '</div>';
        im.onclick = function(e){ if(e.target === im) im.style.display = 'none'; };
        document.body.appendChild(im);

        var biDP = null;
        var biStandalone = window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone === true;
        var biIOS = /iphone|ipad|ipod/i.test(navigator.userAgent) && !window.MSStream;
        var __biReveal = function(){ if(biStandalone) return; var b = document.getElementById('installBtn'); if(b) b.style.display = 'inline-flex'; };
        window.addEventListener('beforeinstallprompt', function(e){ e.preventDefault(); biDP = e; __biReveal(); });
        if(biIOS && !biStandalone) __biReveal();   // iOS는 beforeinstallprompt 미발생
        window.__biblyOpenInstall = function(){
          document.getElementById('installAndroid').style.display = biDP ? 'block' : 'none';
          document.getElementById('installIOS').style.display = (biIOS && !biDP) ? 'block' : 'none';
          document.getElementById('installOther').style.display = (!biDP && !biIOS) ? 'block' : 'none';
          document.getElementById('installModal').style.display = 'flex';
        };
        window.__biblyPwaInstall = function(){
          if(!biDP) return;
          document.getElementById('installModal').style.display = 'none';
          biDP.prompt(); biDP.userChoice.then(function(){ biDP = null; var b = document.getElementById('installBtn'); if(b) b.style.display = 'none'; });
        };
        window.addEventListener('appinstalled', function(){ var b = document.getElementById('installBtn'); if(b) b.style.display = 'none'; var m = document.getElementById('installModal'); if(m) m.style.display = 'none'; });
      }
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
