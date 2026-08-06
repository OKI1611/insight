/* pager.js — 목록 페이지 번호(공용)
   글이 10개를 넘으면 페이지를 나누고 번호로 이동한다. 모든 목록 화면이 이 파일 하나를 쓴다.

   사용법
     <script src="/pager.js?v=1"></script>
     <div id="myPager"></div>

     const rows = BiblyPager.slice(ALL, PAGE);          // 현재 페이지 항목만
     BiblyPager.render(document.getElementById('myPager'), {
       total: ALL.length, page: PAGE,
       onGo: function(p){ PAGE = p; renderList(); }      // 번호를 누르면 호출
     });

   옵션
     per      한 페이지 개수(기본 10)
     scrollTo 이동 후 맨 위로 올릴 요소(생략하면 페이저 기준으로 목록 상단을 찾아 올림)
   되돌려 주는 값: 전체 페이지 수 */
(function(){
  var PER = 10;

  function styleOnce(){
    if(document.getElementById('__biblyPagerStyle')) return;
    var st = document.createElement('style');
    st.id = '__biblyPagerStyle';
    st.textContent =
      '.biblyPager{display:flex;align-items:center;justify-content:center;gap:6px;flex-wrap:wrap;margin-top:22px}'
      + '.biblyPager button{min-width:34px;height:34px;padding:0 9px;border-radius:9px;font-size:13px;font-weight:600;'
      + 'color:rgba(33,58,107,.62);background:#fff;border:1px solid rgba(33,58,107,.09);cursor:pointer;'
      + 'transition:border-color .12s,color .12s,background .12s;font-variant-numeric:tabular-nums}'
      + '.biblyPager button:hover:not(:disabled):not([aria-current]){border-color:rgba(0,112,74,.42);color:#00704a}'
      + '.biblyPager button:disabled{opacity:.32;cursor:default}'
      + '.biblyPager button[aria-current]{background:#00704a;color:#fff;border-color:#00704a}'
      + '.biblyPager .gap{color:rgba(33,58,107,.25);padding:0 2px;user-select:none}'
      + '.biblyPager .pgInfo{width:100%;text-align:center;font-size:12px;color:rgba(33,58,107,.42);margin-top:4px}';
    document.head.appendChild(st);
  }

  function btn(label, p, cur, dis, aria){
    return '<button type="button" data-p="' + p + '"' + (cur ? ' aria-current="page"' : '')
      + (dis ? ' disabled' : '') + (aria ? ' aria-label="' + aria + '"' : '') + '>' + label + '</button>';
  }

  function pages(total, per){ return Math.max(1, Math.ceil((total || 0) / (per || PER))); }

  // 현재 페이지에 해당하는 항목만 잘라 준다
  function slice(rows, page, per){
    per = per || PER;
    rows = rows || [];
    var p = Math.min(Math.max(1, page || 1), pages(rows.length, per));
    var s = (p - 1) * per;
    return rows.slice(s, s + per);
  }

  // 목록에서의 표시 번호(최신 글이 가장 큰 번호). i 는 현재 페이지 안에서의 순번(0부터)
  function no(total, page, i, per){
    per = per || PER;
    return total - ((Math.max(1, page) - 1) * per) - i;
  }

  function render(el, o){
    if(!el) return 1;
    o = o || {};
    styleOnce();
    var per = o.per || PER;
    var n = pages(o.total, per);
    var page = Math.min(Math.max(1, o.page || 1), n);

    if(n <= 1){ el.innerHTML = ''; el.__onGo = o.onGo; return n; }

    var win = 2, s = Math.max(1, page - win), e = Math.min(n, page + win);
    var h = btn('‹', page - 1, false, page <= 1, '이전 페이지');
    if(s > 1){ h += btn(1, 1, false, false); if(s > 2) h += '<span class="gap">…</span>'; }
    for(var i = s; i <= e; i++) h += btn(i, i, i === page, false);
    if(e < n){ if(e < n - 1) h += '<span class="gap">…</span>'; h += btn(n, n, false, false); }
    h += btn('›', page + 1, false, page >= n, '다음 페이지');
    h += '<span class="pgInfo">' + page + ' / ' + n + ' 쪽 · 전체 ' + (o.total || 0) + '개</span>';

    el.className = (el.className || '').replace(/\bbiblyPager\b/g, '').trim();
    el.className = (el.className ? el.className + ' ' : '') + 'biblyPager';
    el.innerHTML = h;

    el.__onGo = o.onGo;
    el.__scrollTo = o.scrollTo || null;
    if(!el.__wired){
      el.__wired = true;
      el.addEventListener('click', function(ev){
        var b = ev.target.closest ? ev.target.closest('button[data-p]') : null;
        if(!b || b.disabled) return;
        var p = Number(b.getAttribute('data-p'));
        if(typeof el.__onGo === 'function') el.__onGo(p);
        var t = el.__scrollTo;
        if(t === false) return;                       // scrollTo:false → 스크롤 이동 안 함
        if(typeof t === 'string') t = document.querySelector(t);
        if(!t){                                        // 지정이 없으면 페이저 바로 앞 목록을 찾는다
          t = el.previousElementSibling || el.parentElement;
        }
        if(t && t.scrollIntoView){
          try{ t.scrollIntoView({ behavior:'smooth', block:'start' }); }catch(e){ t.scrollIntoView(); }
        }
      });
    }
    return n;
  }

  window.BiblyPager = { PER: PER, render: render, slice: slice, pages: pages, no: no };
})();
