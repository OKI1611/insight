/* 공통 헤더 인증 위젯 — #authArea 에 '내 강의실 + 로그인/로그아웃'을 렌더
   라이브러리 불필요(로컬 세션만 읽음). 모든 페이지 헤더에서 동일하게 표시 */
(function(){
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
    if(loggedIn){
      el.innerHTML =
        '<a href="mylearning.html" class="inline-flex items-center gap-1 bg-gold text-white font-semibold px-3 py-1.5 rounded-full hover:opacity-90 transition text-xs whitespace-nowrap">📚 내 강의실</a>'
      + '<button onclick="__biblyLogout()" class="text-ink/45 hover:text-gold text-sm whitespace-nowrap">로그아웃</button>';
    } else {
      el.innerHTML =
        '<a href="mylearning.html" class="inline-flex items-center gap-1 border border-gold/45 text-gold font-semibold px-3 py-1.5 rounded-full hover:bg-gold/10 transition text-xs whitespace-nowrap">📚 내 강의실</a>'
      + '<a href="index.html" class="bg-gold text-white font-semibold px-3 py-1.5 rounded-full hover:opacity-90 transition text-xs whitespace-nowrap">로그인</a>';
    }
  }
  render();
})();
