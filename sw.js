// 오광일 인사이트 브리핑 — 서비스 워커 (PWA)
// 전략: HTML은 항상 네트워크(최신 유지), 정적자원만 캐시. 오프라인 시 폴백.
const CACHE = 'bibleinsight-v400';
const SHELL = ['/manifest.json', '/app', '/app.html', '/app-menu', '/app-menu.html', '/content/app-books.json', '/app.css?v=20261108f', '/app-shell.js?v=20261108f', '/app-mode.js?v=20261107a', '/content/app-verses.json', '/bible/books.json', '/images/icon-192.png?v=8'];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).catch(() => {}));
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))));
  self.clients.claim();
});

// 캐시에 저장하면서 응답 반환
function putAndReturn(req, res) {
  if (res && (res.ok || res.type === 'opaque')) { const copy = res.clone(); caches.open(CACHE).then((c) => c.put(req, copy)).catch(() => {}); }
  return res;
}
// 캐시 먼저 즉시 응답 + 뒤에서 네트워크로 갱신(다음 방문에 반영) — 배포 시 sw 버전 +1로 전체 캐시가 비워지므로 신선도 보장
function staleWhileRevalidate(e, req) {
  e.respondWith(caches.match(req).then((cached) => {
    const refresh = fetch(req).then((res) => putAndReturn(req, res));
    // 캐시가 있으면 즉시 응답(뒤에서 갱신), 없으면 네트워크 — 둘 다 실패하면 마지막으로 한 번 더 시도
    return cached || refresh.catch(() => caches.match(req).then((c2) => c2 || fetch(req)));
  }));
}

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);

  // 외부(CDN·Supabase·유튜브)는 가로채지 않음 — opaque 응답은 깨진 사본이 캐시되면 복구가 안 되므로
  // 브라우저 HTTP 캐시에 맡긴다 (preconnect로 연결만 선행)
  if (url.origin !== location.origin) return;

  // 결제·데이터 API는 절대 캐시하지 않음
  if (url.pathname.startsWith('/api/')) return;

  // HTML/문서: 네트워크 우선(조건부 요청 허용 → 304면 빠름), 4초 안에 안 오면 캐시로 즉시 — 오프라인 폴백 포함
  const isDoc = req.mode === 'navigate' || url.pathname === '/' || url.pathname.endsWith('.html');
  if (isDoc) {
    e.respondWith((async () => {
      const cached = await caches.match(req);
      try {
        const net = fetch(req, { cache: 'no-cache' }).then((res) => putAndReturn(req, res));
        if (!cached) return await net;
        const timeout = new Promise((r) => setTimeout(() => r(null), 4000));
        return (await Promise.race([net, timeout])) || cached;
      } catch (err) { return cached || caches.match('/index.html'); }
    })());
    return;
  }

  // ?v= 버전이 붙은 자원(공용 js·css·아이콘): 내용이 바뀌면 v도 바뀌므로 캐시 우선 = 즉시 응답
  if (url.search.includes('v=')) {
    e.respondWith(caches.match(req).then((cached) => cached || fetch(req).then((res) => putAndReturn(req, res))));
    return;
  }

  // 그 외 정적 자원(이미지·폰트·JSON·버전 없는 js): 캐시 먼저 보여주고 뒤에서 갱신
  staleWhileRevalidate(e, req);
});
