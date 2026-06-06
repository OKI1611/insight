// 오광일 인사이트 브리핑 — 서비스 워커 (PWA)
// 전략: 네트워크 우선, 실패 시 캐시(오프라인 대비). 콘텐츠는 항상 최신 유지.
const CACHE = 'bibleinsight-v1';
const SHELL = ['/', '/index.html', '/watch.html', '/community.html', '/resources.html', '/manifest.json'];

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
  // 외부(유튜브·Supabase·CDN)는 그대로 통과
  if (new URL(req.url).origin !== location.origin) return;
  e.respondWith(
    fetch(req)
      .then((res) => {
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(req, copy)).catch(() => {});
        return res;
      })
      .catch(() => caches.match(req).then((r) => r || caches.match('/index.html')))
  );
});
