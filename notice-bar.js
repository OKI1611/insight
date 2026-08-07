// 공지 바 — 전 페이지 헤더 아래 상시 노출 (2026-08-08, A+B안의 A)
// · 고정 공지(pinned) 우선, 없으면 최신 공지(14일 이내)
// · 새 글(7일 이내)은 NEW 배지 + 은은한 반짝(shimmer) 효과로 시선 유도
// · ✕ 닫으면 그 공지 id는 다시 안 뜸 — 새 공지가 오면 다시 나타남
// 로드: site-header.js가 자동 주입(서브 페이지 전체) + index.html 직접 포함
(function () {
  if (/notices\.html/.test(location.pathname)) return;            // 게시판 자체에는 불필요
  var SB = 'https://bmxkndkwefdgsomlznoo.supabase.co';
  var KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJteGtuZGt3ZWZkZ3NvbWx6bm9vIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODA1NzAwODIsImV4cCI6MjA5NjE0NjA4Mn0.l1yHhMVYwMqYSL8ub9PtrJPOl7CYr7yqstG2AER1EaU';
  var DKEY = 'bibly_notice_bar_dismiss';

  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }

  function render(n) {
    var isNew = (Date.now() - new Date(n.created_at).getTime()) < 7 * 864e5;
    var css = document.createElement('style');
    css.textContent =
      '#biblyNoticeBar{position:relative;background:linear-gradient(90deg,#0a3d2b,#00704a);color:#fff;overflow:hidden;}' +
      '#biblyNoticeBar .nbIn{max-width:72rem;margin:0 auto;padding:9px 20px;display:flex;align-items:center;gap:11px;font-size:13.5px;font-family:Pretendard,system-ui,sans-serif;}' +
      '#biblyNoticeBar a{color:#fff;text-decoration:none;}' +
      '#biblyNoticeBar .nbPill{background:#fff;color:#00704a;font-weight:800;font-size:10.5px;padding:2.5px 9px;border-radius:999px;flex-shrink:0;display:flex;align-items:center;gap:5px;}' +
      '#biblyNoticeBar .nbDot{width:6px;height:6px;border-radius:999px;background:#e0442c;animation:nbPing 1.4s cubic-bezier(0,0,.2,1) infinite;}' +
      '@keyframes nbPing{0%{box-shadow:0 0 0 0 rgba(224,68,44,.55)}70%{box-shadow:0 0 0 6px rgba(224,68,44,0)}100%{box-shadow:0 0 0 0 rgba(224,68,44,0)}}' +
      '#biblyNoticeBar .nbTitle{font-weight:600;flex:1;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}' +
      '#biblyNoticeBar .nbNew{flex-shrink:0;background:#ffd76a;color:#5a4000;font-weight:800;font-size:10px;padding:2px 7px;border-radius:999px;animation:nbGlow 1.6s ease-in-out infinite;}' +
      '@keyframes nbGlow{0%,100%{transform:scale(1);box-shadow:0 0 0 0 rgba(255,215,106,.0)}50%{transform:scale(1.08);box-shadow:0 0 12px 2px rgba(255,215,106,.55)}}' +
      '#biblyNoticeBar .nbMore{flex-shrink:0;font-size:12px;font-weight:700;color:#d9f2e6;}' +
      '#biblyNoticeBar .nbX{flex-shrink:0;background:none;border:none;color:rgba(255,255,255,.55);font-size:15px;cursor:pointer;padding:2px 4px;line-height:1;}' +
      '#biblyNoticeBar .nbX:hover{color:#fff;}' +
      '#biblyNoticeBar .nbShimmer{position:absolute;top:0;bottom:0;width:45%;background:linear-gradient(105deg,transparent,rgba(255,255,255,.16),transparent);animation:nbSweep 2.6s ease-in-out .6s 3;pointer-events:none;transform:translateX(-130%);}' +
      '@keyframes nbSweep{to{transform:translateX(330%)}}';
    document.head.appendChild(css);

    var bar = document.createElement('div');
    bar.id = 'biblyNoticeBar';
    bar.innerHTML =
      (isNew ? '<div class="nbShimmer"></div>' : '') +
      '<div class="nbIn">' +
      '<span class="nbPill">' + (isNew ? '<span class="nbDot"></span>' : '') + '공지</span>' +
      '<a class="nbTitle" href="/notices.html">' + esc(n.title) + '</a>' +
      (isNew ? '<span class="nbNew">NEW</span>' : '') +
      '<a class="nbMore" href="/notices.html">자세히 →</a>' +
      '<button class="nbX" aria-label="공지 닫기">✕</button>' +
      '</div>';
    bar.querySelector('.nbX').addEventListener('click', function () {
      try { localStorage.setItem(DKEY, String(n.id)); } catch (e) {}
      bar.remove();
    });

    var anchor = document.querySelector('#siteHeader') || document.querySelector('header');
    if (anchor) anchor.insertAdjacentElement('afterend', bar);
    else document.body.insertAdjacentElement('afterbegin', bar);
  }

  function go() {
    fetch(SB + '/rest/v1/notices?select=id,title,created_at,pinned&kind=eq.notice&order=pinned.desc,created_at.desc&limit=1',
      { headers: { apikey: KEY, Authorization: 'Bearer ' + KEY } })
      .then(function (r) { return r.ok ? r.json() : []; })
      .then(function (rows) {
        var n = rows && rows[0];
        if (!n) return;
        var fresh = (Date.now() - new Date(n.created_at).getTime()) < 14 * 864e5;
        if (!n.pinned && !fresh) return;                           // 오래된 일반 글이면 숨김
        try { if (localStorage.getItem(DKEY) === String(n.id)) return; } catch (e) {}
        render(n);
      }).catch(function () {});
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', go);
  else go();
})();
