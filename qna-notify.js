/* qna-notify.js — 수강생 질문방 「새 글 알림」(네이버 블로그 새글 알림처럼 🔔 + 빨간 N)
   - 언어 단추 자리(#biblyLangSlot · .biblyLangSlot) 바로 옆에 종 단추를 붙인다 → 웹 상단 띠·홈·앱 홈·앱 상단바 공통
   - 질문방(community_posts, board='qna') 최근 15개를 읽어, 이 기기에서 마지막으로 열어 본 뒤 올라온 글이 있으면 N 표시
   - 종을 누르면 최근 글 목록이 펼쳐지고, 연 순간 '읽음'으로 처리(localStorage bibly_qna_seen = 가장 최근 글 시각)
   - 비공개 글은 Supabase 정책(RLS)이 막으므로 여기서 따로 거르지 않는다
   - 불러오는 곳: site-header.js(웹 전 페이지) · app-shell.js(앱 화면) · index.html
   - 앱 홈의 「질문방」 카드(.promo .bd2)에도 같은 N 을 붙인다 */
(function(){
  if(window.__biblyQnaBell) return; window.__biblyQnaBell = true;
  var SB = 'https://bmxkndkwefdgsomlznoo.supabase.co';
  var AK = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJteGtuZGt3ZWZkZ3NvbWx6bm9vIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODA1NzAwODIsImV4cCI6MjA5NjE0NjA4Mn0.l1yHhMVYwMqYSL8ub9PtrJPOl7CYr7yqstG2AER1EaU';
  var KEY = 'bibly_qna_seen', FIRST_DAYS = 3, REFRESH = 5 * 60 * 1000;
  var root = document.documentElement;
  var isApp = function(){ return root.classList.contains('app'); };
  var posts = [], seen = 0, panel = null, openBtn = null;

  function getSeen(){
    try{ var v = +localStorage.getItem(KEY) || 0; if(v) return v;
      v = Date.now() - FIRST_DAYS * 86400000; localStorage.setItem(KEY, String(v)); return v;   // 처음 온 기기: 최근 3일 글만 '새 글'
    }catch(e){ return Date.now() - FIRST_DAYS * 86400000; }
  }
  function setSeen(t){ seen = t; try{ localStorage.setItem(KEY, String(t)); }catch(e){} }
  function esc(s){ return String(s == null ? '' : s).replace(/[&<>"']/g, function(c){ return { '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' }[c]; }); }
  function plain(h){ var d = document.createElement('div'); d.innerHTML = String(h || '').replace(/<\/(p|div|li)>/gi, '\n').replace(/<br\s*\/?>/gi, '\n'); return (d.textContent || '').trim(); }
  function title(p){ var t = plain(p.content).replace(/^\[[^\]]+\]\s*/, ''); return (t.split('\n')[0] || '').slice(0, 70) || '(제목 없음)'; }
  function ago(t){ var s = (Date.now() - new Date(t)) / 1000;
    if(s < 60) return '방금'; if(s < 3600) return Math.floor(s / 60) + '분 전'; if(s < 86400) return Math.floor(s / 3600) + '시간 전';
    if(s < 604800) return Math.floor(s / 86400) + '일 전'; var d = new Date(t); return (d.getMonth() + 1) + '.' + d.getDate(); }
  function link(p){ return isApp() ? '/app-menu?p=board&id=' + encodeURIComponent(p.id) : '/qna-board?post=' + encodeURIComponent(p.id); }
  function boardUrl(){ return isApp() ? '/app-menu?p=board' : '/qna-board'; }
  function newCount(){ var n = 0; posts.forEach(function(p){ if(new Date(p.created_at).getTime() > seen) n++; }); return n; }

  // ── 모양 ──
  function css(){
    if(document.getElementById('qBellCss')) return;
    var s = document.createElement('style'); s.id = 'qBellCss';
    s.textContent = ''
      + '.qBell{position:relative;flex:none;display:inline-flex;align-items:center;justify-content:center;width:36px;height:36px;margin-left:4px;border:0;border-radius:999px;background:none;color:inherit;cursor:pointer;padding:0;-webkit-tap-highlight-color:transparent}'
      + '.qBell:hover{background:rgba(127,127,127,.14)}'
      + '#biblyLangSlot+.qBell{color:#fff}'   // 웹 상단 남색 띠
      + '.qBell svg{width:21px;height:21px;fill:none;stroke:currentColor;stroke-width:1.9;stroke-linecap:round;stroke-linejoin:round}'
      + 'html.app .qBell,.hd2 .qBell{width:44px;height:44px;margin-left:0;color:#111827}'
      + 'html.app .qBell svg{width:25px;height:25px;stroke-width:1.8}'
      + '.qBell .qN,.qNB{position:absolute;top:3px;right:2px;min-width:17px;height:17px;padding:0 4px;border-radius:999px;background:#e5322d;color:#fff;font:800 10.5px/17px Pretendard,system-ui,sans-serif;text-align:center;box-shadow:0 0 0 2px #fff;display:none}'
      + 'html.app .qBell .qN{top:6px;right:5px}'
      + '.qBell.has .qN{display:block}'
      + '.qNB{position:static;display:inline-block;margin-left:6px;vertical-align:1px;box-shadow:none}'
      + '#qBellPanel{position:fixed;z-index:2147482990;width:min(360px,calc(100vw - 20px));max-height:min(70vh,560px);display:flex;flex-direction:column;background:#fff;color:#111827;border:1px solid rgba(33,58,107,.14);border-radius:16px;box-shadow:0 18px 48px -12px rgba(21,32,58,.35);font-family:Pretendard,system-ui,sans-serif;overflow:hidden}'
      + '#qBellPanel .qh{display:flex;align-items:center;gap:8px;padding:14px 14px 10px 16px;border-bottom:1px solid #eef1f5}'
      + '#qBellPanel .qh b{flex:1;font-size:16px;font-weight:800;letter-spacing:-.02em}'
      + '#qBellPanel .qh button{width:36px;height:36px;border:0;background:none;border-radius:10px;font-size:20px;color:#4b5563;cursor:pointer}'
      + '#qBellPanel .ql{overflow-y:auto;-webkit-overflow-scrolling:touch}'
      + '#qBellPanel .qi{display:block;padding:12px 16px;text-decoration:none;color:inherit;border-bottom:1px solid #f1f3f7}'
      + '#qBellPanel .qi:hover{background:#f6f8fb}'
      + '#qBellPanel .qi.nw{background:#fff8f7}'
      + '#qBellPanel .qt{font-size:15px;font-weight:700;line-height:1.45;color:#111827;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}'
      + '#qBellPanel .qt i{font-style:normal;display:inline-block;min-width:17px;height:17px;margin-right:6px;border-radius:999px;background:#e5322d;color:#fff;font-size:10.5px;font-weight:800;line-height:17px;text-align:center;vertical-align:2px}'
      + '#qBellPanel .qm{margin-top:4px;font-size:12.5px;color:#4b5563;font-weight:600}'
      + '#qBellPanel .qm em{font-style:normal;color:#0b7d53;font-weight:800}'
      + '#qBellPanel .qe{padding:28px 16px;text-align:center;color:#4b5563;font-size:14px}'
      + '#qBellPanel .qf{display:block;padding:13px 16px;text-align:center;font-size:14.5px;font-weight:800;color:#0b7d53;text-decoration:none;border-top:1px solid #eef1f5;background:#fafbfc}';
    document.head.appendChild(s);
  }
  var BELL = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 9.5a6 6 0 0 1 12 0c0 4.2 1.6 6.1 2.4 6.9H3.6C4.4 15.6 6 13.7 6 9.5z"/><path d="M10 19.5a2.1 2.1 0 0 0 4 0"/></svg>';

  // ── 단추 붙이기(언어 단추 자리 옆) ──
  function mount(){
    css();
    var slots = document.querySelectorAll('#biblyLangSlot, .biblyLangSlot');
    for(var i = 0; i < slots.length; i++){
      var sl = slots[i], nx = sl.nextElementSibling;
      if(nx && nx.classList.contains('qBell')) continue;
      var b = document.createElement('button');
      b.type = 'button'; b.className = 'qBell'; b.setAttribute('aria-label', '질문방 새 글 알림'); b.title = '질문방 새 글';
      b.innerHTML = BELL + '<span class="qN">N</span>';
      b.addEventListener('click', function(e){ e.stopPropagation(); toggle(this); });
      sl.parentNode.insertBefore(b, sl.nextSibling);
    }
    paint();
  }
  function paint(){
    var n = newCount();
    var bs = document.querySelectorAll('.qBell');
    for(var i = 0; i < bs.length; i++){ bs[i].classList.toggle('has', n > 0); bs[i].title = n ? '질문방 새 글 ' + n + '개' : '질문방 새 글'; }
    // 앱 홈 「질문방」 카드
    var card = document.querySelector('a.promo[href*="p=board"] .bd2');
    if(card){ var t = card.querySelector('.qNB'); if(n && !t){ t = document.createElement('span'); t.className = 'qNB'; t.textContent = 'N'; card.appendChild(t); } if(t) t.style.display = n ? 'inline-block' : 'none'; }
    window.__biblyQnaNew = n;
  }

  // ── 목록 ──
  function close(){ if(panel){ panel.remove(); panel = null; openBtn = null; } }
  function place(){
    if(!panel || !openBtn) return;
    var r = openBtn.getBoundingClientRect(), w = panel.offsetWidth, vw = document.documentElement.clientWidth;
    var left = Math.min(Math.max(10, r.right - w), vw - w - 10);
    panel.style.left = left + 'px'; panel.style.top = (r.bottom + 6) + 'px';
  }
  function toggle(btn){
    if(panel && openBtn === btn){ close(); return; }
    close(); openBtn = btn;
    var before = seen;
    panel = document.createElement('div'); panel.id = 'qBellPanel'; panel.setAttribute('role', 'dialog'); panel.setAttribute('aria-label', '질문방 새 글');
    var items = posts.map(function(p){
      var nw = new Date(p.created_at).getTime() > before;
      return '<a class="qi' + (nw ? ' nw' : '') + '" href="' + esc(link(p)) + '"><div class="qt">' + (nw ? '<i>N</i>' : '') + '<span data-noi18n="1">' + esc(title(p)) + '</span></div>'
        + '<div class="qm"><span data-noi18n="1">' + esc(p.author_name || '회원') + '</span> · <span>' + esc(ago(p.created_at)) + '</span>' + (p.answered ? ' · <em>답변 완료</em>' : '') + '</div></a>';
    }).join('');
    panel.innerHTML = '<div class="qh"><b>질문방 새 글</b><button type="button" aria-label="닫기">×</button></div>'
      + '<div class="ql">' + (items || '<div class="qe">아직 올라온 글이 없어요.</div>') + '</div>'
      + '<a class="qf" href="' + boardUrl() + '">질문방 전체 보기 →</a>';
    panel.querySelector('.qh button').onclick = close;
    panel.addEventListener('click', function(e){ e.stopPropagation(); });
    document.body.appendChild(panel); place();
    if(posts.length) setSeen(Math.max(before, new Date(posts[0].created_at).getTime()));
    paint();
  }
  document.addEventListener('click', function(){ close(); });
  document.addEventListener('keydown', function(e){ if(e.key === 'Escape') close(); });
  addEventListener('resize', place);
  addEventListener('scroll', function(){ if(panel && !isApp()) place(); }, { passive: true });

  // ── 불러오기 ──
  function load(){
    return fetch(SB + '/rest/v1/community_posts?select=id,author_name,content,created_at,answered&board=eq.qna&order=created_at.desc&limit=15',
      { headers: { apikey: AK, Authorization: 'Bearer ' + AK } })
      .then(function(r){ return r.ok ? r.json() : []; })
      .then(function(rows){ posts = Array.isArray(rows) ? rows : []; paint(); })
      .catch(function(){});
  }

  function start(){
    seen = getSeen();
    mount();
    // 머리글·앱 상단바는 나중에 그려지므로 몇 초간 다시 붙여 본다
    var tries = 0, t = setInterval(function(){ mount(); if(++tries > 16) clearInterval(t); }, 500);
    load();
    setInterval(function(){ if(!document.hidden) load(); }, REFRESH);
    document.addEventListener('visibilitychange', function(){ if(!document.hidden) load(); });
    // 다른 탭에서 읽으면 이 탭의 N 도 지운다
    addEventListener('storage', function(e){ if(e.key === KEY){ seen = +e.newValue || seen; paint(); } });
  }
  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
})();
