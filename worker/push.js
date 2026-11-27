// worker/push.js — 앱(홈 화면 앱·플레이 스토어 앱) 「새 강의 · 새 글」 푸시 알림 (Web Push, 무료)
//   표준: RFC 8030(전송) · RFC 8291(aes128gcm 암호화) · RFC 8292(VAPID). 외부 라이브러리 없이 WebCrypto 로만 만든다.
//   VAPID 열쇠는 서버가 처음 쓸 때 스스로 만들어 Supabase notify_kv(서버 전용)에 둔다 — 비밀키는 밖으로 나가지 않는다.
//   구독: 앱 화면이 POST /api/push/subscribe → push_subs 표(서버 전용). 404/410 응답이 오면 구독을 지운다.
//   보낼 거리(크론, 5분마다): ① content/course.json 에 새로 생긴 강의(유튜브 id 기준) ② 칼럼(columns) 새 글 ③ 공지(notices) 새 글
//     처음 한 번은 '지금까지 본 것'만 기록하고 보내지 않는다. 받는 사람이 많으면 한 번에 PUSH_BATCH 명씩 나눠 보낸다(다음 크론이 이어서).
import { kvGet, kvSet } from './notify.js';

const SUPABASE_URL = 'https://bmxkndkwefdgsomlznoo.supabase.co';
const SITE = 'https://www.biblynote.com';
const PUSH_BATCH = 30;
const PUSH_HOSTS = /^https:\/\/([a-z0-9-]+\.)*(fcm\.googleapis\.com|push\.apple\.com|push\.services\.mozilla\.com|notify\.windows\.com|wns2-[a-z0-9-]+\.notify\.windows\.com)\//i;

function json(o, s = 200) {
  return new Response(JSON.stringify(o), { status: s, headers: { 'Content-Type': 'application/json; charset=utf-8', 'Access-Control-Allow-Origin': '*' } });
}
function sbH(env) { return { apikey: env.SUPABASE_SERVICE_KEY, Authorization: 'Bearer ' + env.SUPABASE_SERVICE_KEY, 'Content-Type': 'application/json' }; }
const enc = new TextEncoder();
function b64u(buf) { let s = ''; const a = new Uint8Array(buf); for (let i = 0; i < a.length; i++) s += String.fromCharCode(a[i]); return btoa(s).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, ''); }
function unb64u(s) { s = String(s).replace(/-/g, '+').replace(/_/g, '/'); while (s.length % 4) s += '='; const b = atob(s); const a = new Uint8Array(b.length); for (let i = 0; i < b.length; i++) a[i] = b.charCodeAt(i); return a; }
function cat(...parts) { const n = parts.reduce((s, p) => s + p.length, 0); const o = new Uint8Array(n); let i = 0; for (const p of parts) { o.set(p, i); i += p.length; } return o; }

// ── VAPID 열쇠(서버가 만들고 보관) ──
let VAPID = null;   // 한 번 읽으면 같은 실행 안에서 재사용(외부 요청 수 절약)
async function vapid(env) {
  if (VAPID) return VAPID;
  let pub = await kvGet(env, 'vapid_pub'), jwk = await kvGet(env, 'vapid_jwk');
  if (pub && jwk) return (VAPID = { pub, jwk: JSON.parse(jwk) });
  const kp = await crypto.subtle.generateKey({ name: 'ECDSA', namedCurve: 'P-256' }, true, ['sign', 'verify']);
  pub = b64u(await crypto.subtle.exportKey('raw', kp.publicKey));
  const priv = await crypto.subtle.exportKey('jwk', kp.privateKey);
  await kvSet(env, 'vapid_jwk', JSON.stringify(priv));
  await kvSet(env, 'vapid_pub', pub);
  // 동시에 두 곳에서 만들었을 수 있으니 저장된 값을 다시 읽어 쓴다
  return (VAPID = { pub: await kvGet(env, 'vapid_pub'), jwk: JSON.parse(await kvGet(env, 'vapid_jwk')) });
}
async function vapidHeader(env, endpoint) {
  const { pub, jwk } = await vapid(env);
  const key = await crypto.subtle.importKey('jwk', jwk, { name: 'ECDSA', namedCurve: 'P-256' }, false, ['sign']);
  const head = b64u(enc.encode(JSON.stringify({ typ: 'JWT', alg: 'ES256' })));
  const body = b64u(enc.encode(JSON.stringify({ aud: new URL(endpoint).origin, exp: Math.floor(Date.now() / 1000) + 12 * 3600, sub: 'mailto:contact@biblynote.com' })));
  const sig = await crypto.subtle.sign({ name: 'ECDSA', hash: 'SHA-256' }, key, enc.encode(head + '.' + body));   // WebCrypto 는 r||s(64바이트) — JWS 형식 그대로
  return 'vapid t=' + head + '.' + body + '.' + b64u(sig) + ', k=' + pub;
}

// ── 본문 암호화(RFC 8291 aes128gcm) ──
async function hkdf(salt, ikm, info, len) {
  const k = await crypto.subtle.importKey('raw', ikm, 'HKDF', false, ['deriveBits']);
  return new Uint8Array(await crypto.subtle.deriveBits({ name: 'HKDF', hash: 'SHA-256', salt, info }, k, len * 8));
}
async function encrypt(sub, payload) {
  const uaPub = unb64u(sub.p256dh), auth = unb64u(sub.auth);
  const as = await crypto.subtle.generateKey({ name: 'ECDH', namedCurve: 'P-256' }, true, ['deriveBits']);
  const asPub = new Uint8Array(await crypto.subtle.exportKey('raw', as.publicKey));
  const uaKey = await crypto.subtle.importKey('raw', uaPub, { name: 'ECDH', namedCurve: 'P-256' }, false, []);
  const shared = new Uint8Array(await crypto.subtle.deriveBits({ name: 'ECDH', public: uaKey }, as.privateKey, 256));
  const ikm = await hkdf(auth, shared, cat(enc.encode('WebPush: info\0'), uaPub, asPub), 32);
  const salt = crypto.getRandomValues(new Uint8Array(16));
  const cek = await hkdf(salt, ikm, enc.encode('Content-Encoding: aes128gcm\0'), 16);
  const nonce = await hkdf(salt, ikm, enc.encode('Content-Encoding: nonce\0'), 12);
  const key = await crypto.subtle.importKey('raw', cek, 'AES-GCM', false, ['encrypt']);
  const ct = new Uint8Array(await crypto.subtle.encrypt({ name: 'AES-GCM', iv: nonce }, key, cat(enc.encode(payload), new Uint8Array([2]))));
  const rs = new Uint8Array([0, 0, 16, 0]);   // 레코드 크기 4096
  return cat(salt, rs, new Uint8Array([asPub.length]), asPub, ct);
}
// 구독 하나에 보낸다 → 'ok' | 'gone'(구독 만료: 지움) | 'fail'
async function pushOne(env, sub, msg) {
  try {
    const body = await encrypt(sub, JSON.stringify(msg));
    const r = await fetch(sub.endpoint, {
      method: 'POST',
      headers: { Authorization: await vapidHeader(env, sub.endpoint), TTL: '86400', Urgency: 'normal', 'Content-Encoding': 'aes128gcm', 'Content-Type': 'application/octet-stream' },
      body
    });
    if (r.status === 404 || r.status === 410) {
      await fetch(SUPABASE_URL + '/rest/v1/push_subs?endpoint=eq.' + encodeURIComponent(sub.endpoint), { method: 'DELETE', headers: sbH(env) }).catch(() => {});
      return 'gone';
    }
    return r.ok ? 'ok' : 'fail';
  } catch (e) { return 'fail'; }
}

// ── 화면에서 부르는 API ──
export async function pushKey(env) {
  if (!env.SUPABASE_SERVICE_KEY) return json({ ok: false, reason: 'not-configured' });
  try { const v = await vapid(env); if (!v.pub) { VAPID = null; return json({ ok: false, reason: 'no-table' }); } return json({ ok: true, key: v.pub }); } catch (e) { VAPID = null; return json({ ok: false, reason: 'no-table' }); }
}
export async function pushSubscribe(request, env) {
  let b = {}; try { b = await request.json(); } catch (e) {}
  const s = b.sub || {}, keys = s.keys || {};
  if (!PUSH_HOSTS.test(String(s.endpoint || '')) || !keys.p256dh || !keys.auth) return json({ ok: false, reason: 'bad-sub' }, 400);
  const row = { endpoint: s.endpoint, p256dh: keys.p256dh, auth: keys.auth, lang: /^(ko|en|es|ja|zh)$/.test(b.lang) ? b.lang : 'ko', ua: String(request.headers.get('User-Agent') || '').slice(0, 160), updated_at: new Date().toISOString() };
  const r = await fetch(SUPABASE_URL + '/rest/v1/push_subs?on_conflict=endpoint', { method: 'POST', headers: { ...sbH(env), Prefer: 'resolution=merge-duplicates,return=minimal' }, body: JSON.stringify(row) });
  return json({ ok: r.ok });
}
export async function pushUnsubscribe(request, env) {
  let b = {}; try { b = await request.json(); } catch (e) {}
  if (!b.endpoint) return json({ ok: false }, 400);
  const r = await fetch(SUPABASE_URL + '/rest/v1/push_subs?endpoint=eq.' + encodeURIComponent(b.endpoint), { method: 'DELETE', headers: sbH(env) });
  return json({ ok: r.ok });
}

// ── 관리자: 상태 · 시험 발송(관리자 기기만이 아니라 전체에 가므로 문구를 '안내'로) ──
export async function pushAdmin(request, env, action, verifyAdmin) {
  if (!(await verifyAdmin(request))) return json({ error: '관리자 인증 실패' }, 403);
  const head = await fetch(SUPABASE_URL + '/rest/v1/push_subs?select=endpoint', { method: 'HEAD', headers: { ...sbH(env), Prefer: 'count=exact' } });
  const total = Number(((head.headers.get('content-range') || '').split('/')[1]) || 0);
  if (action === 'status') {
    const q = await kvGet(env, 'push_queue');
    return json({ ok: true, hasTable: head.ok, subscribers: total, queue: q ? JSON.parse(q) : null });
  }
  if (action === 'send') {   // 관리자가 직접 쓰는 알림(제목·내용·링크)
    let b = {}; try { b = await request.json(); } catch (e) {}
    const title = String(b.title || '').slice(0, 60), text = String(b.body || '').slice(0, 140);
    if (!title) return json({ error: '제목을 입력하세요' }, 400);
    const url = /^\/[^\s]*$/.test(b.url || '') ? b.url : '/app';
    await enqueue(env, { title, body: text, url, tag: 'admin-' + Date.now() });
    await drain(env);
    return json({ ok: true, subscribers: total });
  }
  return json({ error: 'not found' }, 404);
}

// ── 보낼 줄(queue): [{msg, after}] — after = 이 endpoint 다음부터(정렬 기준) ──
async function enqueue(env, msg) {
  const q = JSON.parse((await kvGet(env, 'push_queue')) || '[]');
  q.push({ msg, after: '' });
  await kvSet(env, 'push_queue', JSON.stringify(q.slice(-10)));
}
async function drain(env) {
  let q = JSON.parse((await kvGet(env, 'push_queue')) || '[]');
  if (!q.length) return;
  let budget = PUSH_BATCH;
  while (q.length && budget > 0) {
    const job = q[0];
    const r = await fetch(SUPABASE_URL + '/rest/v1/push_subs?select=endpoint,p256dh,auth,lang&order=endpoint.asc&limit=' + budget + (job.after ? '&endpoint=gt.' + encodeURIComponent(job.after) : ''), { headers: sbH(env) });
    const subs = r.ok ? await r.json() : [];
    for (const s of subs) await pushOne(env, s, job.msg);
    budget -= subs.length;
    if (subs.length && budget <= 0) { job.after = subs[subs.length - 1].endpoint; break; }   // 다음 크론이 이어서
    q.shift();                                                                                // 이 알림은 모두 보냄
  }
  await kvSet(env, 'push_queue', JSON.stringify(q));
}

// ── 크론: 새 강의 · 새 칼럼 · 새 공지 찾기 → 줄 세우기 → 보내기 ──
function ytId(u) { const m = String(u || '').match(/(?:youtu\.be\/|v=|embed\/|shorts\/)([\w-]{11})/); return m ? m[1] : ''; }
export async function pushSweep(env) {
  if (!env.SUPABASE_SERVICE_KEY) return;
  if (!(await fetch(SUPABASE_URL + '/rest/v1/push_subs?select=endpoint&limit=1', { headers: sbH(env) })).ok) return;   // 표가 아직 없음
  // ① 새 강의
  try {
    const r = await env.ASSETS.fetch(new Request(SITE + '/content/course.json'));
    if (r.ok) {
      const d = await r.json(), now = [];
      (d.levels || []).forEach(lv => (lv.lessons || []).forEach(l => { const id = ytId(l.youtube); if (id) now.push({ id, title: l.title, track: lv.name }); }));
      const seenRaw = await kvGet(env, 'push_seen_lectures');
      const seen = new Set(seenRaw ? JSON.parse(seenRaw) : []);
      const fresh = seenRaw ? now.filter(x => !seen.has(x.id)) : [];
      if (fresh.length === 1) await enqueue(env, { title: '🎬 새 강의가 올라왔어요', body: fresh[0].title.slice(0, 120), url: '/watch?v=' + fresh[0].id, tag: 'lec-' + fresh[0].id });
      else if (fresh.length > 1) await enqueue(env, { title: '🎬 새 강의 ' + fresh.length + '편이 올라왔어요', body: fresh.map(x => x.title).join(' · ').slice(0, 120), url: '/curriculum', tag: 'lec-' + Date.now() });
      if (!seenRaw || fresh.length) await kvSet(env, 'push_seen_lectures', JSON.stringify([...new Set(now.map(x => x.id))]));
    }
  } catch (e) {}
  // ② 칼럼 · ③ 공지 (created_at 기준)
  const since = await kvGet(env, 'push_seen_posts_at'), stamp = new Date().toISOString();
  if (since) {
    try {
      const c = await fetch(SUPABASE_URL + '/rest/v1/columns?select=id,title,created_at&created_at=gt.' + encodeURIComponent(since) + '&order=created_at.asc&limit=5', { headers: sbH(env) });
      for (const x of (c.ok ? await c.json() : [])) await enqueue(env, { title: '✍️ 새 글: ' + String(x.title || '').slice(0, 40), body: '오광일의 인사이트 칼럼에 새 글이 올라왔어요.', url: '/column#col-' + x.id, tag: 'col-' + x.id });
    } catch (e) {}
    try {
      const n = await fetch(SUPABASE_URL + '/rest/v1/notices?select=id,title,created_at,kind&created_at=gt.' + encodeURIComponent(since) + '&order=created_at.asc&limit=5', { headers: sbH(env) });
      for (const x of (n.ok ? await n.json() : [])) await enqueue(env, { title: x.kind === 'event' ? '🎁 새 이벤트' : '📢 새 공지', body: String(x.title || '').slice(0, 120), url: '/app-menu?p=' + (x.kind === 'event' ? 'events' : 'notices'), tag: 'ntc-' + x.id });
    } catch (e) {}
  }
  await kvSet(env, 'push_seen_posts_at', stamp);
  await drain(env);
}

