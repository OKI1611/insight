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
        + '<a href="index.html#support" aria-label="후원하기" class="inline-flex items-center gap-1.5 bg-rose-500 text-white font-bold rounded-full shadow-xl hover:bg-rose-600 transition" style="padding:11px 18px;font-size:15px"><span style="font-size:17px">♥</span> 후원하기</a>'
        + '<a href="community.html?board=qna" aria-label="무엇이든 질문하기" class="inline-flex items-center gap-2 bg-gold text-white font-bold rounded-full shadow-xl hover:opacity-95 transition">'
        + '<span style="padding:13px 0 13px 18px;font-size:20px">💬</span>'
        + '<span class="hidden sm:inline" style="padding-right:20px;font-size:15px">무엇이든 물어보세요</span>'
        + '<span class="sm:hidden" style="padding-right:16px;font-size:14px">질문</span>'
        + '</a>'
        + '</div>';
      document.body.appendChild(w);
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
    var support = '<a href="index.html#support" aria-label="후원하기" title="후원하기" class="inline-flex items-center justify-center w-8 h-8 rounded-full bg-rose-500/10 text-rose-500 border border-rose-300 hover:bg-rose-500 hover:text-white transition shrink-0" style="font-size:15px">♥</a>';
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
