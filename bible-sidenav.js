/* 성경 섹션 왼쪽 사이드 선택 메뉴 — 성경 관련 페이지(읽기·매일말씀·암송·통독·주제·사전)에서
   좌측에 라벨이 보이는 세로 메뉴를 항상 띄우고, 본문이 가려지지 않도록 페이지를 오른쪽으로 민다.
   데스크톱(>=1100px)에서만 노출, 좁은 화면은 상단 '성경' 드롭다운으로 대체. */
(function(){
  if(window.__biblySideNav) return; window.__biblySideNav = true;
  var ITEMS = [
    { l:'성경 읽기',        h:'bible.html',      i:'' },
    { l:'매일 말씀과 함께', h:'daily.html',      i:'' },
    { l:'성경암송 365',     h:'memorize.html',   i:'' },
    { l:'성경 통독표',      h:'bible-plan.html', i:'' },
    { l:'주제별 성경',      h:'themes.html',     i:'' },
    { l:'성경사전',         h:'dictionary.html', i:'' }
  ];
  var page = (location.pathname.split('/').pop() || 'index.html').toLowerCase() || 'index.html';
  if(page === '') page = 'index.html';
  if(ITEMS.map(function(x){ return x.h; }).indexOf(page) < 0) return;

  function build(){
    if(document.getElementById('bibleSideNav')) return;
    var W = 210; // 사이드바 폭
    var st = document.createElement('style');
    st.textContent =
      '#bibleSideNav{display:none;position:fixed;top:0;left:0;bottom:0;width:' + W + 'px;z-index:45;'
      + 'background:#fff;border-right:1px solid rgba(33,58,107,.1);box-shadow:2px 0 18px -10px rgba(21,32,58,.18);'
      + 'flex-direction:column;padding:14px 12px;overflow-y:auto}'
      + '#bibleSideNav .hd{font-size:12px;font-weight:800;color:#0f766e;letter-spacing:.04em;padding:6px 8px 10px;display:flex;align-items:center;gap:7px}'
      + '#bibleSideNav .hd b{color:#171717;font-size:14px}'
      + '#bibleSideNav a{display:flex;align-items:center;gap:10px;padding:11px 12px;border-radius:11px;'
      + 'text-decoration:none;margin-bottom:3px;white-space:nowrap;transition:background .15s}'
      + '#bibleSideNav .ic{font-size:17px;flex:0 0 auto;width:22px;text-align:center}'
      + '#bibleSideNav .lbl{font-size:13.5px}'
      + '#bibleSideNav a.on{background:#0f766e}#bibleSideNav a.on .lbl{color:#fff;font-weight:700}'
      + '#bibleSideNav a:not(.on) .lbl{color:rgba(33,58,107,.82);font-weight:600}'
      + '#bibleSideNav a:not(.on):hover{background:rgba(15,118,110,.1)}'
      + '#bibleSideNav .foot{margin-top:auto;padding:10px 8px 4px;font-size:10.5px;color:rgba(33,58,107,.35);line-height:1.5}'
      + '@media(min-width:1024px){body{padding-left:' + W + 'px}#bibleSideNav{display:flex}}';
    document.head.appendChild(st);

    var rail = document.createElement('nav');
    rail.id = 'bibleSideNav';
    rail.setAttribute('aria-label', '성경 메뉴');
    var h = '<div class="hd"><b>성경</b></div>';
    ITEMS.forEach(function(x){
      var on = (x.h === page);
      h += '<a href="' + x.h + '" class="' + (on ? 'on' : '') + '" title="' + x.l + '">'
        + '<span class="ic">' + x.i + '</span><span class="lbl">' + x.l + '</span></a>';
    });
    h += '<div class="foot">말씀으로 시대를 읽다<br>BIBLY</div>';
    rail.innerHTML = h;
    document.body.appendChild(rail);
  }

  if(document.body) build();
  else document.addEventListener('DOMContentLoaded', build);
})();
