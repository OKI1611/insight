// 오광일 인사이트 브리핑 — 서비스 워커 (PWA)
// 전략: HTML은 항상 네트워크(최신 유지), 정적자원만 캐시. 오프라인 시 폴백.
const CACHE = 'bibleinsight-v100';
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
  if (url.origin !== location.origin) return; // 외부(유튜브·Supabase·CDN)는 통과

  // HTML/문서: 항상 네트워크 최신 (캐시 저장 안 함, 오프라인만 폴백)
  const isDoc = req.mode === 'navigate' || url.pathname === '/' || url.pathname.endsWith('.html');
  if (isDoc) {
    // HTTP 캐시까지 우회해 항상 최신 문서 — 오프라인이면 캐시 폴백
    e.respondWith(fetch(req, { cache: 'no-store' }).catch(() => caches.match(req).then((r) => r || caches.match('/index.html'))));
    return;
  }

  // 공유 스크립트(.js): 항상 최신으로 받음(HTTP 캐시까지 우회), 오프라인이면 캐시 폴백
  if (url.pathname.endsWith('.js')) {
    e.respondWith(fetch(req, { cache: 'no-store' }).then((res) => { const copy = res.clone(); caches.open(CACHE).then((c) => c.put(req, copy)).catch(() => {}); return res; }).catch(() => caches.match(req)));
    return;
  }

  // 그 외 정적 자원: 네트워크 우선 + 캐시 갱신
  e.respondWith(
    fetch(req)
      .then((res) => { const copy = res.clone(); caches.open(CACHE).then((c) => c.put(req, copy)).catch(() => {}); return res; })
      .catch(() => caches.match(req))
  );
});
