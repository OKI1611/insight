// ?ㅺ킅???몄궗?댄듃 釉뚮━?????쒕퉬???뚯빱 (PWA)
// ?꾨왂: HTML? ??긽 ?ㅽ듃?뚰겕(理쒖떊 ?좎?), ?뺤쟻?먯썝留?罹먯떆. ?ㅽ봽?쇱씤 ???대갚.
const CACHE = 'bibleinsight-v237';
const SHELL = ['/manifest.json'];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).catch(() => {}));
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))));
  self.clients.claim();
});

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== location.origin) return; // ?몃?(?좏뒠釉뙿톁upabase쨌CDN)???듦낵

  // HTML/臾몄꽌: ??긽 ?ㅽ듃?뚰겕 理쒖떊 (罹먯떆 ??????? ?ㅽ봽?쇱씤留??대갚)
  const isDoc = req.mode === 'navigate' || url.pathname === '/' || url.pathname.endsWith('.html');
  if (isDoc) {
    // HTTP 罹먯떆源뚯? ?고쉶????긽 理쒖떊 臾몄꽌 ???ㅽ봽?쇱씤?대㈃ 罹먯떆 ?대갚
    e.respondWith(fetch(req, { cache: 'no-store' }).catch(() => caches.match(req).then((r) => r || caches.match('/index.html'))));
    return;
  }

  // 怨듭쑀 ?ㅽ겕由쏀듃(.js): ??긽 理쒖떊?쇰줈 諛쏆쓬(HTTP 罹먯떆源뚯? ?고쉶), ?ㅽ봽?쇱씤?대㈃ 罹먯떆 ?대갚
  if (url.pathname.endsWith('.js')) {
    e.respondWith(fetch(req, { cache: 'no-store' }).then((res) => { const copy = res.clone(); caches.open(CACHE).then((c) => c.put(req, copy)).catch(() => {}); return res; }).catch(() => caches.match(req)));
    return;
  }

  // 洹????뺤쟻 ?먯썝: ?ㅽ듃?뚰겕 ?곗꽑 + 罹먯떆 媛깆떊
  e.respondWith(
    fetch(req)
      .then((res) => { const copy = res.clone(); caches.open(CACHE).then((c) => c.put(req, copy)).catch(() => {}); return res; })
      .catch(() => caches.match(req))
  );
});
