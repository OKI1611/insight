/* 성경 섹션 왼쪽 사이드 선택 메뉴 — 성경 관련 페이지(읽기·매일말씀·암송·통독·주제·사전)에서
   좌측에 세로 메뉴를 띄워 서로 전환할 수 있게 한다.
   좁은 여백에서도 항상 보이도록: 평소엔 아이콘 막대로 접혀 있고, 마우스를 올리면 라벨이 펼쳐진다.
   데스크톱(>=1200px)에서만 노출, 좁은 화면은 상단 드롭다운/햄버거로 대체. */
(function(){
  if(window.__biblySideNav) return; window.__biblySideNav = true;
  var ITEMS = [
    { l:'성경 읽기',        h:'bible.html',      i:'📖' },
    { l:'매일 말씀과 함께', h:'daily.html',      i:'🌅' },
    { l:'성경암송 365',     h:'memorize.html',   i:'✨' },
    { l:'성경 통독표',      h:'bible-plan.html', i:'📅' },
    { l:'주제별 성경',      h:'themes.html',     i:'📚' },
    { l:'성경사전',         h:'dictionary.html', i:'🔎' }
  ];
  var page = (location.pathname.split('/').pop() || 'index.html').toLowerCase() || 'index.html';
  if(page === '') page = 'index.html';
  if(ITEMS.map(function(x){ return x.h; }).indexOf(page) < 0) return;

  function build(){
    if(document.getElementById('bibleSideNav')) return;
    var st = document.createElement('style');
    st.textContent =
      '#bibleSideNav{position:fixed;left:10px;top:50%;transform:translateY(-50%);z-index:30;display:none}'
      + '@media(min-width:1200px){#bibleSideNav{display:block}}'
      + '#bibleSideNav .rail{width:54px;overflow:hidden;background:#fff;border:1px solid rgba(33,58,107,.1);'
      + 'border-radius:16px;box-shadow:0 10px 34px -18px rgba(21,32,58,.3);padding:7px;transition:width .2s ease}'
      + '#bibleSideNav:hover .rail{width:172px}'
      + '#bibleSideNav .hd{font-size:11px;font-weight:800;color:rgba(33,58,107,.42);letter-spacing:.06em;'
      + 'padding:4px 0 6px;text-align:center;white-space:nowrap}'
      + '#bibleSideNav:hover .hd{text-align:left;padding-left:10px}'
      + '#bibleSideNav a{display:flex;align-items:center;gap:9px;padding:9px 0;border-radius:11px;'
      + 'text-decoration:none;margin-bottom:2px;white-space:nowrap;justify-content:center;transition:background .15s}'
      + '#bibleSideNav:hover a{justify-content:flex-start;padding-left:10px;padding-right:10px}'
      + '#bibleSideNav .ic{font-size:18px;flex:0 0 auto;width:24px;text-align:center}'
      + '#bibleSideNav .lbl{font-size:13px;opacity:0;transition:opacity .15s}'
      + '#bibleSideNav:hover .lbl{opacity:1}'
      + '#bibleSideNav a.on{background:#b8923f}#bibleSideNav a.on .lbl{color:#fff;font-weight:700}'
      + '#bibleSideNav a:not(.on) .lbl{color:rgba(33,58,107,.78);font-weight:500}'
      + '#bibleSideNav a:not(.on):hover{background:rgba(184,146,63,.1)}';
    document.head.appendChild(st);

    var rail = document.createElement('nav');
    rail.id = 'bibleSideNav';
    rail.setAttribute('aria-label', '성경 메뉴');
    var h = '<div class="rail"><p class="hd">📖 성경</p>';
    ITEMS.forEach(function(x){
      var on = (x.h === page);
      h += '<a href="' + x.h + '" class="' + (on ? 'on' : '') + '" title="' + x.l + '">'
        + '<span class="ic">' + x.i + '</span><span class="lbl">' + x.l + '</span></a>';
    });
    h += '</div>';
    rail.innerHTML = h;
    document.body.appendChild(rail);
  }

  if(document.body) build();
  else document.addEventListener('DOMContentLoaded', build);
})();
