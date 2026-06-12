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
    var support = '<a href="index.html#support" class="hidden sm:inline-flex items-center gap-1 text-ink/55 hover:text-gold font-semibold text-xs whitespace-nowrap" title="후원">♥ 후원</a>';
    if(loggedIn){
      el.innerHTML = support
      + '<a href="mylearning.html" class="inline-flex items-center gap-1 bg-gold text-white font-semibold px-3 py-1.5 rounded-full hover:opacity-90 transition text-xs whitespace-nowrap">📚 내 강의실</a>'
      + '<button onclick="__biblyLogout()" class="text-ink/45 hover:text-gold text-sm whitespace-nowrap">로그아웃</button>';
    } else {
      el.innerHTML = support
      + '<a href="mylearning.html" class="inline-flex items-center gap-1 border border-gold/45 text-gold font-semibold px-3 py-1.5 rounded-full hover:bg-gold/10 transition text-xs whitespace-nowrap">📚 내 강의실</a>'
      + '<a href="index.html" class="bg-gold text-white font-semibold px-3 py-1.5 rounded-full hover:opacity-90 transition text-xs whitespace-nowrap">로그인</a>';
    }
  }
  render();
})();
