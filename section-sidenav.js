/* 범용 좌측 사이드바(네이버 카페식 전체 메뉴 트리) — 모든 상위메뉴를 로고 아래에
   세로로 펼쳐 보여준다. 현재 페이지가 속한 섹션은 자동으로 펼쳐지고 강조되며,
   나머지 섹션은 접혀 있고 헤더를 누르면 펼쳐진다.
   메뉴 정의는 content/site.json 의 nav 를 단일 소스로 사용(헤더와 100% 동일).
   데스크톱(>=1024px)에서만 노출되며 본문을 오른쪽으로 밀어 가려지지 않게 한다.
   좁은 화면(<1024px)에서는 상단 드롭다운 메뉴로 대체되므로 숨긴다. */
(function(){
  if(window.__biblySectionNav) return; window.__biblySectionNav = true;

  // site.json nav와 100% 동일하게 유지(불일치 시 깜빡임·엉뚱한 메뉴 노출 방지)
  var FALLBACK = [
    { label:'소개', href:'about.html', children:[
      { label:'우리의 사명·소개', href:'about.html' }, { label:'강사 소개', href:'about.html#instructor' },
      { label:'설립 이야기 · 간증', href:'about.html#story' }, { label:'1기 창립 멤버', href:'founding.html' } ]},
    { label:'강의·커리큘럼', href:'curriculum.html', children:[
      { label:'전체 커리큘럼', href:'curriculum.html' }, { label:'나에게 맞는 강의 찾기', href:'find.html' },
      { label:'무료로 시작하기', href:'welcome.html' } ]},
    { label:'성경', href:'bible.html', children:[
      { label:'성경 읽기', href:'bible.html' }, { label:'매일 말씀과 함께', href:'daily.html' },
      { label:'성경암송 365', href:'memorize.html' }, { label:'성경 통독표 (1년 1독)', href:'bible-plan.html' },
      { label:'바이블 잉글리시', href:'bible-english.html' },
      { label:'성경 번역 이야기', href:'translation-notes.html' },
      { label:'주제별 성경', href:'themes.html' } ]},
    { label:'위대한 믿음', href:'preachers.html', children:[
      { label:'위대한 설교자', href:'preachers.html' }, { label:'위대한 기도자', href:'prayers.html' } ]},
    { label:'소통·나눔', href:'community.html', children:[
      { label:'질문·나눔·기도요청', href:'community.html' }, { label:'신앙상담', href:'counsel.html' },
      { label:'강의 요청·건의함', href:'request.html' }, { label:'자료실', href:'resources.html' },
      { label:'칼럼', href:'column.html' } ]},
    { label:'스토어', href:'booklet.html', children:[
      { label:'PDF 책자·이용권', href:'booklet.html' },
      { label:'고객센터(주문·배송·반품)', href:'store-help.html' }, { label:'내 구매·자료', href:'mylearning.html' } ]},
    { label:'저자의 책', href:'books.html', children:[
      { label:'저자의 책 전체', href:'books.html' },
      { label:'마귀는 거짓말을 하지 않는다 (신간)', href:'books.html#devil' },
      { label:'가이사의 교회, 하나님의 교회', href:'books.html#caesar' },
      { label:'가면의 시대', href:'books.html#mask' },
      { label:'교회를 떠나고서야, 예수를 만났다', href:'books.html#church' },
      { label:'엄마 향기', href:'books.html#mom' } ]},
    { label:'아카데미 인증과정', href:'academy.html', children:[
      { label:'과정 소개', href:'academy.html' }, { label:'급수 패키지·수강료', href:'academy.html#packages' },
      { label:'등록 신청', href:'academy.html#apply' } ]}
  ];

  var page = (location.pathname.split('/').pop() || 'index.html').toLowerCase();
  page = page.split('#')[0].split('?')[0];
  if(!page) page = 'index.html';
  else if(page.indexOf('.') < 0) page += '.html'; // 클린 URL(/column) → column.html 보정

  // 자체 좌측 메뉴가 있는 페이지는 사이드바를 띄우지 않는다.
  var SKIP_PAGES = ['mylearning.html'];
  if(SKIP_PAGES.indexOf(page) >= 0) return;

  function base(h){ return String(h||'').split('#')[0].split('?')[0].toLowerCase(); }
  function hashOf(h){ var i = String(h).indexOf('#'); return i >= 0 ? String(h).slice(i) : ''; }

  // 현재 페이지가 속한 섹션 찾기
  function pickSection(nav){
    for(var i=0;i<nav.length;i++){
      var m = nav[i], kids = m.children || [];
      if(kids.length){ for(var j=0;j<kids.length;j++){ if(base(kids[j].href) === page) return m; } }
      if(base(m.href) === page) return m;
    }
    return null;
  }

  // 섹션 안에서 현재 페이지에 해당하는 자식이 활성인지 판단(같은 페이지 앵커 메뉴 대응)
  function makeIsOn(kids){
    var anchorMode = kids.filter(function(c){ return base(c.href) === page; }).length > 1;
    function anyHashMatch(){ var cur = location.hash || ''; return kids.some(function(k){ return base(k.href) === page && hashOf(k.href) && cur === hashOf(k.href); }); }
    return function(href){
      var cb = base(href), hh = hashOf(href), cur = location.hash || '';
      if(cb !== page) return false;
      if(anchorMode) return hh ? (cur === hh) : !anyHashMatch();
      return true;
    };
  }

  function render(nav){
    if(document.getElementById('bibleSideNav') || document.getElementById('sectionSideNav')) return;
    var curSec = pickSection(nav);
    if(!curSec) return; // 어느 섹션에도 속하지 않는 페이지(홈 등)에는 사이드바 없음
    var W = 216;
    // 왼쪽은 사이드바 폭만큼 항상 비우고, 오른쪽은 화면이 넓어질 때만 같은 폭까지 따라 붙는다.
    var PL = 'max(0px, (100vw - 1360px) / 2) + ' + W + 'px';
    var PR = 'max(0px, (100vw - 1360px) / 2) + min(' + W + 'px, max(24px, 100vw - 1168px))';
    var st = document.createElement('style');
    st.id = '__sectionNavStyle';
    st.textContent =
      '#sectionSideNav{display:none;position:fixed;top:96px;left:0;bottom:0;width:' + W + 'px;z-index:35;'
      + 'background:#fff;border-right:1px solid rgba(33,58,107,.08);flex-direction:column;padding:16px 10px;overflow-y:auto}'
      + '#sectionSideNav .sn-title{font-size:10.5px;font-weight:800;letter-spacing:.16em;color:rgba(33,58,107,.38);padding:2px 10px 12px;text-transform:uppercase}'
      + '#sectionSideNav .sn-grp{margin-bottom:1px}'
      + '#sectionSideNav .sn-hd{display:flex;align-items:center;justify-content:space-between;gap:8px;padding:9px 10px;border-radius:9px;cursor:pointer;font-size:13.5px;font-weight:700;color:#2a3346;text-decoration:none;transition:background .15s,color .15s;letter-spacing:-.01em}'
      + '#sectionSideNav .sn-hd:hover{background:#f4f6fa}'
      + '#sectionSideNav .sn-grp.cur > .sn-hd{color:#00704a}'
      + '#sectionSideNav .chev{width:8px;height:8px;border-right:2px solid rgba(33,58,107,.32);border-bottom:2px solid rgba(33,58,107,.32);transform:rotate(-45deg);transition:transform .18s;flex:none;margin-right:4px}'
      + '#sectionSideNav .sn-grp.open .chev{transform:rotate(45deg)}'
      + '#sectionSideNav .sn-kids{display:none;padding:1px 0 6px}'
      + '#sectionSideNav .sn-grp.open .sn-kids{display:block}'
      + '#sectionSideNav .sn-kids a{display:block;padding:7px 12px 7px 24px;border-radius:8px;font-size:12.8px;font-weight:600;color:#5a6070;text-decoration:none;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;transition:background .15s,transform .15s}'
      + '#sectionSideNav .sn-kids a:hover{background:#f4f6fa;transform:translateX(2px)}'
      + '#sectionSideNav .sn-kids a.on{background:#e7f3ec;color:#0a3d2b;font-weight:800;box-shadow:inset 3px 0 0 #00704a}'
      + '#sectionSideNav .sn-sub{margin:1px 0}'
      + '#sectionSideNav .sn-sub-hd{display:flex;align-items:center;justify-content:space-between;gap:6px;padding:7px 12px 7px 24px;border-radius:8px;cursor:pointer;font-size:12.8px;font-weight:700;color:#3a4358;transition:background .15s}'
      + '#sectionSideNav .sn-sub-hd:hover{background:#f4f6fa}'
      + '#sectionSideNav .chev2{width:7px;height:7px;border-right:2px solid rgba(33,58,107,.3);border-bottom:2px solid rgba(33,58,107,.3);transform:rotate(-45deg);transition:transform .18s;flex:none;margin-right:2px}'
      + '#sectionSideNav .sn-sub.open .chev2{transform:rotate(45deg)}'
      + '#sectionSideNav .sn-gkids{display:none;padding:1px 0 4px}'
      + '#sectionSideNav .sn-sub.open .sn-gkids{display:block}'
      + '#sectionSideNav .sn-gkids a{display:block;padding:6px 12px 6px 38px;border-radius:8px;font-size:12.3px;font-weight:600;color:#6a7080;text-decoration:none;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;transition:background .15s,transform .15s}'
      + '#sectionSideNav .sn-gkids a:hover{background:#f4f6fa;color:#00704a;transform:translateX(2px)}'
      + '#sectionSideNav .foot{margin-top:auto;padding:12px 10px 2px;font-size:10.5px;color:rgba(33,58,107,.4);line-height:1.55;border-top:1px solid rgba(33,58,107,.06)}'
      // 오른쪽 여백: 사이드바 폭을 그대로 마주 비우면 1024~1360px 구간에서 본문이 되레 좁아진다
      // (1024px에서 본문 열이 768px일 때보다 좁아지던 문제). 여유가 생기는 만큼만 대칭을 맞춘다.
      + '@media(min-width:1024px){'
      + 'body{padding-left:calc(' + PL + ');padding-right:calc(' + PR + ')}'
      + '#sectionSideNav{display:flex;left:max(0px, calc((100vw - 1360px) / 2))}'
      + 'body>.bibly-topbar,body>header{margin-left:calc(-1 * (' + PL + '));width:calc(100% + (' + PL + ') + (' + PR + '))}'
      + 'body #biblyRail{display:none}'   // 섹션 사이드바가 뜨는 데스크톱에선 겹치는 빠른이동 레일 숨김(중복·로드순서 무관하게 우선)
      + '}';
    document.head.appendChild(st);

    var rail = document.createElement('nav');
    rail.id = 'sectionSideNav';
    rail.setAttribute('aria-label', '전체 메뉴');

    // 다른 섹션의 하위에 이미 존재하는 링크는 최상위에서 중복 표시하지 않기 위한 집합
    var childBases = {};
    nav.forEach(function(m){ (m.children || []).forEach(function(c){ childBases[base(c.href)] = true; }); });

    var h = '<div class="sn-title">전체 메뉴</div>';
    nav.forEach(function(m){
      var kids = m.children || [];
      var isCur = curSec.label === m.label;
      if(!kids.length){
        // 자식 없는 상위메뉴가 이미 다른 섹션의 하위 항목이면 중복이므로 건너뜀
        //  (예: '성경사전'은 '성경' 하위에 있으므로 별도 최상위로 또 보이지 않게)
        if(childBases[base(m.href)]) return;
        h += '<div class="sn-grp' + (isCur ? ' cur' : '') + '">'
          + '<a class="sn-hd" href="' + m.href + '"><span>' + m.label + '</span></a></div>';
        return;
      }
      var isOn = isCur ? makeIsOn(kids) : function(){ return false; };
      h += '<div class="sn-grp' + (isCur ? ' cur open' : '') + '">'
        + '<div class="sn-hd" role="button" tabindex="0"><span>' + m.label + '</span><span class="chev"></span></div>'
        + '<div class="sn-kids">';
      kids.forEach(function(c){
        var gk = c.children || [];
        if(!gk.length){
          h += '<a href="' + c.href + '" data-h="' + hashOf(c.href) + '" data-b="' + base(c.href) + '" class="' + (isOn(c.href) ? 'on' : '') + '" title="' + c.label + '">' + c.label + '</a>';
          return;
        }
        // 손자 메뉴가 있는 항목(예: 전체 커리큘럼) → 접이식 서브그룹(현재 섹션이면 펼침)
        h += '<div class="sn-sub' + (isCur ? ' open' : '') + '">'
          + '<div class="sn-sub-hd" role="button" tabindex="0"><span>' + c.label + '</span><span class="chev2"></span></div>'
          + '<div class="sn-gkids">'
          + '<a href="' + c.href + '" title="전체 보기">전체 보기</a>'
          + gk.map(function(g){ return '<a href="' + g.href + '" data-b="' + base(g.href) + '" title="' + g.label + '">' + g.label + '</a>'; }).join('')
          + '</div></div>';
      });
      h += '</div></div>';
    });
    h += '<div class="foot">말씀으로 시대를 읽다<br>BIBLY · 바이블 인사이트</div>';
    rail.innerHTML = h;
    document.body.appendChild(rail);

    // 헤더 클릭 → 그룹 펼침/접힘 토글(자식 있는 그룹만)
    rail.querySelectorAll('.sn-grp').forEach(function(grp){
      var hd = grp.querySelector('.sn-hd');
      if(!hd || hd.tagName === 'A') return; // 링크형 헤더는 토글 아님
      hd.addEventListener('click', function(){ grp.classList.toggle('open'); });
      hd.addEventListener('keydown', function(e){ if(e.key === 'Enter' || e.key === ' '){ e.preventDefault(); grp.classList.toggle('open'); } });
    });
    // 손자 서브그룹(전체 커리큘럼 등) 펼침/접힘 토글
    rail.querySelectorAll('.sn-sub-hd').forEach(function(sh){
      var sub = sh.parentElement;
      sh.addEventListener('click', function(){ sub.classList.toggle('open'); });
      sh.addEventListener('keydown', function(e){ if(e.key === 'Enter' || e.key === ' '){ e.preventDefault(); sub.classList.toggle('open'); } });
    });

    // 앵커(#) 이동 시 현재 섹션의 활성 표시 실시간 갱신
    window.addEventListener('hashchange', function(){
      var links = rail.querySelectorAll('.sn-grp.cur .sn-kids a');
      var kids = curSec.children || [];
      var isOn = makeIsOn(kids);
      links.forEach(function(a){ a.classList.toggle('on', isOn(a.getAttribute('href'))); });
    });
  }

  function sig(nav){ try{ return JSON.stringify(nav); }catch(e){ return ''; } }

  function start(){
    // 1) 즉시(동기) 렌더 — 캐시된 nav가 있으면 그것으로, 없으면 내장 FALLBACK으로.
    var rendered = '';
    var cached = null;
    try{ cached = JSON.parse(sessionStorage.getItem('bibly_nav') || 'null'); }catch(e){}
    var nav0 = (cached && cached.length) ? cached : FALLBACK;
    if(pickSection(nav0)){ render(nav0); rendered = sig(nav0); }

    // 2) 백그라운드로 site.json 최신본 반영. 메뉴가 실제로 바뀐 경우에만 재렌더.
    fetch('content/site.json', { cache:'no-cache' })
      .then(function(r){ return r.ok ? r.json() : null; })
      .then(function(d){
        if(!d || !d.nav) return;
        try{ sessionStorage.setItem('bibly_nav', JSON.stringify(d.nav)); }catch(e){}
        if(pickSection(d.nav) && sig(d.nav) !== rendered){
          var st = document.getElementById('__sectionNavStyle');
          var old = document.getElementById('sectionSideNav');
          if(old) old.remove(); if(st) st.remove();
          render(d.nav); rendered = sig(d.nav);
        }
      })
      .catch(function(){});
  }

  if(document.body) start();
  else document.addEventListener('DOMContentLoaded', start);
})();
