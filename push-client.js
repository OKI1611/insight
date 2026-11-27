/* push-client.js — 앱(html.app)에서 「새 강의·새 글 알림」 켜기 (Web Push 구독)
   - 앱 홈 「질문방」 카드 아래에 알림 켜기 카드를 보여 준다(지원 안 되는 기기·이미 켠 기기·'나중에' 7일 동안은 숨김)
   - 단추를 누르면(사용자 손짓이 있어야 아이폰도 허락 창을 띄움) 권한 요청 → 서버 공개키로 구독 → /api/push/subscribe
   - 이미 허락된 기기는 하루 한 번 구독을 서버와 맞춘다(구독 주소가 바뀌는 경우 대비)
   - 알림 표시·누르면 이동은 sw.js 의 push · notificationclick
   - 불러오는 곳: app-shell.js(앱 화면 공통) */
(function(){
  if(window.__biblyPush) return;
  var root = document.documentElement;
  var ok = 'serviceWorker' in navigator && 'PushManager' in window && 'Notification' in window;
  var api = window.__biblyPush = { supported: ok };
  if(!ok) return;
  var LATER = 'bibly_push_later', SYNC = 'bibly_push_sync';
  function ls(k, v){ try{ if(v === undefined) return localStorage.getItem(k); if(v === null) localStorage.removeItem(k); else localStorage.setItem(k, v); }catch(e){ return null; } }
  function u8(b64){ b64 = b64.replace(/-/g, '+').replace(/_/g, '/'); while(b64.length % 4) b64 += '='; var s = atob(b64), a = new Uint8Array(s.length); for(var i = 0; i < s.length; i++) a[i] = s.charCodeAt(i); return a; }
  function lang(){ return root.getAttribute('data-ui') || 'ko'; }

  async function reg(){ return navigator.serviceWorker.ready; }
  async function current(){ try{ var r = await reg(); return await r.pushManager.getSubscription(); }catch(e){ return null; } }
  async function send(sub){
    var r = await fetch('/api/push/subscribe', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ sub: sub.toJSON(), lang: lang() }) });
    var d = await r.json().catch(function(){ return {}; });
    if(d.ok) ls(SYNC, String(Date.now()));
    return !!d.ok;
  }
  api.enable = async function(){
    var p = await Notification.requestPermission();
    if(p !== 'granted') return p;
    var k = await fetch('/api/push/key').then(function(r){ return r.json(); }).catch(function(){ return {}; });
    if(!k.ok || !k.key) return 'server';
    var r = await reg();
    var sub = await r.pushManager.getSubscription();
    if(!sub) sub = await r.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: u8(k.key) });
    return (await send(sub)) ? 'granted' : 'server';
  };
  api.disable = async function(){
    var sub = await current(); if(!sub) return;
    fetch('/api/push/unsubscribe', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ endpoint: sub.endpoint }) }).catch(function(){});
    try{ await sub.unsubscribe(); }catch(e){}
  };

  // ── 앱 홈 카드 ──
  function css(){
    if(document.getElementById('pushCss')) return;
    var s = document.createElement('style'); s.id = 'pushCss';
    s.textContent = '#pushCard{display:flex;align-items:center;gap:12px;margin:12px 0 0;padding:14px 14px 14px 16px;border:1.5px solid #cfe7dc;border-radius:16px;background:#f1f9f5}'
      + '#pushCard .pc-i{flex:none;width:42px;height:42px;border-radius:12px;background:#0b7d53;color:#fff;display:flex;align-items:center;justify-content:center}'
      + '#pushCard .pc-i svg{width:24px;height:24px;fill:none;stroke:#fff;stroke-width:1.9;stroke-linecap:round;stroke-linejoin:round}'
      + '#pushCard .pc-t{flex:1;min-width:0}#pushCard b{display:block;font-size:16px;font-weight:800;color:#111827;letter-spacing:-.02em}'
      + '#pushCard .pc-s{display:block;margin-top:2px;font-size:13.5px;color:#374151;line-height:1.45}'
      + '#pushCard .pc-b{display:flex;flex-direction:column;gap:4px;flex:none}'
      + '#pushCard button{min-height:44px;padding:0 14px;border:0;border-radius:12px;font:800 14.5px Pretendard,system-ui,sans-serif;cursor:pointer}'
      + '#pushCard .pc-on{background:#0b7d53;color:#fff}#pushCard .pc-later{min-height:32px;background:none;color:#4b5563;font-size:13px;font-weight:700}';
    document.head.appendChild(s);
  }
  var BELL = '<svg viewBox="0 0 24 24"><path d="M6 9.5a6 6 0 0 1 12 0c0 4.2 1.6 6.1 2.4 6.9H3.6C4.4 15.6 6 13.7 6 9.5z"/><path d="M10 19.5a2.1 2.1 0 0 0 4 0"/></svg>';
  async function card(){
    if(!document.body.hasAttribute('data-app-home')) return;
    if(document.getElementById('pushCard')) return;
    if(Notification.permission === 'denied') return;
    if(Notification.permission === 'granted' && await current()) return;
    var later = +ls(LATER) || 0; if(Date.now() - later < 7 * 86400000) return;
    var anchor = document.querySelector('a.promo[href*="p=board"]'); if(!anchor) return;
    css();
    var c = document.createElement('div'); c.id = 'pushCard';
    c.innerHTML = '<span class="pc-i">' + BELL + '</span><span class="pc-t"><b>새 강의·새 글 알림 받기</b><span class="pc-s">새 강의나 새 글이 올라오면 휴대폰 알림으로 알려 드려요.</span></span>'
      + '<span class="pc-b"><button type="button" class="pc-on">알림 켜기</button><button type="button" class="pc-later">나중에</button></span>';
    anchor.insertAdjacentElement('afterend', c);
    c.querySelector('.pc-later').onclick = function(){ ls(LATER, String(Date.now())); c.remove(); };
    c.querySelector('.pc-on').onclick = async function(){
      var b = this; b.disabled = true;
      var res = 'server'; try{ res = await api.enable(); }catch(e){}
      if(res === 'granted'){ c.querySelector('.pc-t').innerHTML = '<b>알림이 켜졌어요</b><span class="pc-s">새 강의·새 글이 올라오면 알려 드릴게요.</span>'; c.querySelector('.pc-b').remove(); setTimeout(function(){ c.remove(); }, 4000); }
      else if(res === 'denied'){ c.querySelector('.pc-s').textContent = '휴대폰 설정에서 이 앱의 알림을 허용해 주세요.'; b.disabled = false; }
      else { c.querySelector('.pc-s').textContent = '지금은 알림을 켤 수 없어요. 잠시 뒤 다시 시도해 주세요.'; b.disabled = false; }
    };
  }
  // 이미 허락된 기기: 하루 한 번 서버와 맞추기
  async function resync(){
    if(Notification.permission !== 'granted') return;
    if(Date.now() - (+ls(SYNC) || 0) < 86400000) return;
    var sub = await current();
    if(sub) send(sub).catch(function(){});
    else api.enable().catch(function(){});
  }
  function start(){ if(!root.classList.contains('app')) return; card(); resync(); }
  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
})();
