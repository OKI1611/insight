/* 성경 섹션 왼쪽 사이드 선택 메뉴 — 성경 관련 페이지(읽기·매일말씀·암송·통독·주제·사전)에서
   좌측 여백에 세로 메뉴를 띄워 서로 전환할 수 있게 한다. 넓은 화면(>=1400px)에서만 노출,
   좁은 화면은 상단 드롭다운/햄버거로 대체. */
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
  var pages = ITEMS.map(function(x){ return x.h; });
  if(pages.indexOf(page) < 0) return;

  function build(){
    if(document.getElementById('bibleSideNav')) return;
    var st = document.createElement('style');
    st.textContent = '#bibleSideNav{display:none}@media(min-width:1400px){#bibleSideNav{display:block}}'
      + '#bibleSideNav a{transition:background .15s}';
    document.head.appendChild(st);

    var rail = document.createElement('nav');
    rail.id = 'bibleSideNav';
    rail.setAttribute('aria-label', '성경 메뉴');
    rail.style.cssText = 'position:fixed;left:24px;top:50%;transform:translateY(-50%);width:158px;z-index:30';

    var h = '<div style="background:#fff;border:1px solid rgba(33,58,107,.1);border-radius:16px;'
      + 'box-shadow:0 10px 34px -18px rgba(21,32,58,.3);padding:9px;">'
      + '<p style="font-size:11px;font-weight:800;color:rgba(33,58,107,.42);letter-spacing:.1em;padding:6px 8px 6px;margin:0;">📖 성경</p>';
    ITEMS.forEach(function(x){
      var on = (x.h === page);
      h += '<a href="' + x.h + '" '
        + 'style="display:flex;align-items:center;gap:8px;padding:9px 10px;border-radius:11px;'
        + 'font-size:13px;line-height:1.2;text-decoration:none;margin-bottom:2px;'
        + (on ? 'background:#b8923f;color:#fff;font-weight:700;'
              : 'color:rgba(33,58,107,.78);font-weight:500;')
        + '" '
        + (on ? '' : 'onmouseover="this.style.background=\'rgba(184,146,63,.1)\'" onmouseout="this.style.background=\'transparent\'"')
        + '><span style="font-size:15px;flex:0 0 auto">' + x.i + '</span><span>' + x.l + '</span></a>';
    });
    h += '</div>';
    rail.innerHTML = h;
    document.body.appendChild(rail);
  }

  if(document.body) build();
  else document.addEventListener('DOMContentLoaded', build);
})();
