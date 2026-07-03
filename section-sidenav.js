/* 범용 좌측 섹션 사이드바 — 모든 상위메뉴(성경·소통나눔·강의·스토어·위대한믿음·BIBLY이야기)에서
   현재 페이지가 속한 섹션의 하위메뉴를 좌측 세로 메뉴로 자동 생성한다.
   메뉴 정의는 content/site.json 의 nav 를 단일 소스로 사용(헤더와 100% 동일).
   데스크톱(>=1024px)에서만 노출되며 본문을 오른쪽으로 밀어 가려지지 않게 한다.
   좁은 화면(<1024px)에서는 상단 드롭다운 메뉴로 대체되므로 숨긴다. */
(function(){
  if(window.__biblySectionNav) return; window.__biblySectionNav = true;

  // 아이콘 없이 타이포그래피 중심의 깔끔한 메뉴(이모지 제거 — 현재 항목은 골드 알약으로 강조)
  // site.json 로드 실패 시 사용할 내장 백업(헤더 DEFAULT_MENU와 동일 구조)
  var FALLBACK = [
    { label:'BIBLY 이야기', href:'about.html', children:[
      { label:'우리의 사명·소개', href:'about.html' }, { label:'무료로 시작하기', href:'welcome.html' }, { label:'1기 창립 멤버', href:'founding.html' } ]},
    { label:'강의·커리큘럼', href:'curriculum.html', children:[
      { label:'전체 커리큘럼', href:'curriculum.html' }, { label:'정규 심화 과정(아카데미)', href:'academy.html' },
      { label:'나에게 맞는 강의 찾기', href:'find.html' } ]},
    { label:'스토어', href:'booklet.html', children:[
      { label:'PDF 책자·이용권', href:'booklet.html' }, { label:'선물·후원 좌석', href:'gift.html' },
      { label:'고객센터(주문·배송·반품)', href:'store-help.html' }, { label:'내 구매·자료', href:'mylearning.html' } ]},
    { label:'성경', href:'bible.html', children:[
      { label:'성경 읽기', href:'bible.html' }, { label:'매일 말씀과 함께', href:'daily.html' },
      { label:'성경암송 365', href:'memorize.html' }, { label:'성경 통독표 (1년 1독)', href:'bible-plan.html' },
      { label:'주제별 성경', href:'themes.html' }, { label:'성경사전', href:'dictionary.html' } ]},
    { label:'위대한 믿음', href:'preachers.html', children:[
      { label:'위대한 설교자', href:'preachers.html' }, { label:'위대한 기도자', href:'prayers.html' } ]},
    { label:'소통·나눔', href:'community.html', children:[
      { label:'질문·나눔·기도요청', href:'community.html' }, { label:'신앙상담', href:'counsel.html' },
      { label:'강의 요청·건의함', href:'request.html' }, { label:'자료실', href:'resources.html' },
      { label:'칼럼', href:'column.html' } ]}
  ];

  var page = (location.pathname.split('/').pop() || 'index.html').toLowerCase();
  page = page.split('#')[0].split('?')[0];
  if(!page) page = 'index.html';
  else if(page.indexOf('.') < 0) page += '.html'; // 클린 URL(/column) → column.html 보정

  // 자체 좌측 메뉴가 있는 페이지는 섹션 사이드바를 띄우지 않는다(스토어 하위메뉴가 잘못 보이던 문제).
  var SKIP_PAGES = ['mylearning.html'];
  if(SKIP_PAGES.indexOf(page) >= 0) return;

  function base(h){ return String(h||'').split('#')[0].split('?')[0].toLowerCase(); }

  function pickSection(nav){
    for(var i=0;i<nav.length;i++){
      var m = nav[i], kids = m.children || [];
      if(!kids.length) continue;
      for(var j=0;j<kids.length;j++){ if(base(kids[j].href) === page) return m; }
      if(base(m.href) === page) return m; // 섹션 대표 페이지(자식에 없을 때)
    }
    return null;
  }

  function render(sec){
    if(document.getElementById('bibleSideNav') || document.getElementById('sectionSideNav')) return;
    var W = 212;
    var st = document.createElement('style');
    st.textContent =
      '#sectionSideNav{display:none;position:fixed;top:96px;left:0;bottom:0;width:' + W + 'px;z-index:35;'
      + 'background:#fff;border-right:1px solid rgba(33,58,107,.08);'
      + 'flex-direction:column;padding:18px 12px;overflow-y:auto}'
      + '#sectionSideNav .hd{position:relative;font-size:15px;font-weight:800;color:#171717;letter-spacing:-.01em;padding:4px 10px 14px;margin-bottom:8px}'
      + '#sectionSideNav .hd:after{content:"";position:absolute;left:10px;bottom:0;width:20px;height:2px;background:#b8923f;border-radius:2px}'
      + '#sectionSideNav a{display:block;padding:10px 14px;border-radius:10px;'
      + 'text-decoration:none;margin-bottom:2px;white-space:nowrap;transition:background .15s,transform .15s}'
      + '#sectionSideNav .lbl{font-size:13.5px}'
      + '#sectionSideNav a.on{background:#f7f1e3;box-shadow:inset 3px 0 0 #b8923f}'
      + '#sectionSideNav a.on .lbl{color:#5a4423;font-weight:800}'
      + '#sectionSideNav a:not(.on) .lbl{color:#4a4a4a;font-weight:600}'
      + '#sectionSideNav a:not(.on):hover{background:#f4f6fa;transform:translateX(2px)}'
      + '#sectionSideNav .foot{margin-top:auto;padding:12px 10px 2px;font-size:10.5px;color:rgba(33,58,107,.4);line-height:1.55;border-top:1px solid rgba(33,58,107,.06)}'
      + '@media(min-width:1024px){'
      // 좌우 대칭 패딩 → 본문이 화면 정중앙에 오도록(좌측 메뉴로 인한 우측 쏠림 방지)
      + 'body{padding-left:calc(max(0px, (100vw - 1360px) / 2) + ' + W + 'px);padding-right:calc(max(0px, (100vw - 1360px) / 2) + ' + W + 'px)}'
      + '#sectionSideNav{display:flex;left:max(0px, calc((100vw - 1360px) / 2))}'
      + 'body>.bibly-topbar,body>header{margin-left:calc(-1 * (max(0px, (100vw - 1360px) / 2) + ' + W + 'px));width:calc(100% + 2 * (max(0px, (100vw - 1360px) / 2) + ' + W + 'px))}'
      + '}';
    document.head.appendChild(st);

    var rail = document.createElement('nav');
    rail.id = 'sectionSideNav';
    rail.setAttribute('aria-label', sec.label + ' 메뉴');
    // 같은 페이지 앵커(#) 메뉴는 전부 base가 같아 모두 '활성'이 되던 버그 방지:
    //  - 해시 링크는 현재 location.hash와 일치할 때만 활성(초기엔 아무것도 활성 아님)
    //  - 일반 링크는 현재 페이지와 일치할 때 활성
    var kids = sec.children || [];
    // 같은 페이지를 가리키는 하위 항목이 2개 이상이면 '앵커 메뉴'로 간주한다.
    //  - 현재 해시(#)와 일치하는 항목만 활성
    //  - 일치가 없으면 해시 없는 대표 항목이 활성(기본 랜딩)
    //  → 예전엔 about.html 하위 3개가 모두 활성(골드)이 되던 버그를 해결.
    function hashOf(href){ var i = String(href).indexOf('#'); return i >= 0 ? String(href).slice(i) : ''; }
    var anchorMode = kids.filter(function(c){ return base(c.href) === page; }).length > 1;
    function anyHashMatch(){ var cur = location.hash || ''; return kids.some(function(k){ return base(k.href) === page && hashOf(k.href) && cur === hashOf(k.href); }); }
    function isOn(href){
      var cb = base(href), hh = hashOf(href), cur = location.hash || '';
      if(anchorMode){
        if(cb !== page) return false;
        return hh ? (cur === hh) : !anyHashMatch();
      }
      return cb === page;
    }
    var h = '<div class="hd">' + sec.label + '</div>';
    kids.forEach(function(c){
      h += '<a href="' + c.href + '" data-h="' + hashOf(c.href) + '" data-b="' + base(c.href) + '" class="' + (isOn(c.href) ? 'on' : '') + '" title="' + c.label + '">'
        + '<span class="lbl">' + c.label + '</span></a>';
    });
    h += '<div class="foot">말씀으로 시대를 읽다<br>BIBLY · 바이블 인사이트</div>';
    rail.innerHTML = h;
    document.body.appendChild(rail);
    // 앵커 이동 시 활성 표시 실시간 갱신
    if(anchorMode){
      window.addEventListener('hashchange', function(){
        var cur = location.hash || '', links = rail.querySelectorAll('a'), any = false;
        links.forEach(function(a){ if(a.getAttribute('data-b') === page && a.getAttribute('data-h') && cur === a.getAttribute('data-h')) any = true; });
        links.forEach(function(a){
          var cb = a.getAttribute('data-b'), hh = a.getAttribute('data-h'), on;
          if(cb !== page) on = false; else on = hh ? (cur === hh) : !any;
          a.classList.toggle('on', on);
        });
      });
    }
  }

  function start(){
    fetch('content/site.json', { cache:'no-cache' })
      .then(function(r){ return r.ok ? r.json() : null; })
      .then(function(d){
        var nav = (d && d.nav) ? d.nav : FALLBACK;
        var sec = pickSection(nav) || pickSection(FALLBACK);
        if(sec) render(sec);
      })
      .catch(function(){ var sec = pickSection(FALLBACK); if(sec) render(sec); });
  }

  if(document.body) start();
  else document.addEventListener('DOMContentLoaded', start);
})();
