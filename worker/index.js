// Cloudflare Worker — 정적 자산(사이트) 서빙 + 결제 API(/api/pay/*)
// 정적 자산은 [assets] 바인딩(env.ASSETS)이 처리하고, 이 Worker는 /api/pay/* 만 담당한다.
// 필수 환경변수(Worker Settings → Variables and secrets): SUPABASE_SERVICE_KEY (필수), TOSS_SECRET_KEY (실결제 시)
const SUPABASE_URL = 'https://bmxkndkwefdgsomlznoo.supabase.co';
const SUPABASE_ANON = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJteGtuZGt3ZWZkZ3NvbWx6bm9vIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODA1NzAwODIsImV4cCI6MjA5NjE0NjA4Mn0.l1yHhMVYwMqYSL8ub9PtrJPOl7CYr7yqstG2AER1EaU';
const ADMIN_EMAIL = 'josephoh1611@gmail.com';
const TOSS_TEST_SECRET = 'test_sk_zXLkKEypNArWmo50nX3lmeaxYG5R'; // 토스 문서 테스트 시크릿(실결제 아님)

function json(o, s = 200) {
  return new Response(JSON.stringify(o), { status: s, headers: { 'Content-Type': 'application/json; charset=utf-8', 'Access-Control-Allow-Origin': '*' } });
}
function sbH(env) { return { apikey: env.SUPABASE_SERVICE_KEY, Authorization: 'Bearer ' + env.SUPABASE_SERVICE_KEY, 'Content-Type': 'application/json' }; }
async function assetJson(env, origin, path) {
  try { const r = await env.ASSETS.fetch(new Request(origin + path)); return r.ok ? await r.json() : null; } catch (e) { return null; }
}
async function upsert(env, table, row, oc) {
  try {
    const r = await fetch(SUPABASE_URL + '/rest/v1/' + table + '?on_conflict=' + oc, { method: 'POST', headers: { ...sbH(env), Prefer: 'resolution=merge-duplicates,return=minimal' }, body: JSON.stringify(row) });
    return r.ok;
  } catch (e) { return false; }
}

function ping(env) {
  return json({ ok: true, mode: 'worker', hasServiceKey: !!env.SUPABASE_SERVICE_KEY, hasTossSecret: !!env.TOSS_SECRET_KEY, time: new Date().toISOString() });
}

// 관리자 인증: 요청의 Bearer 토큰을 Supabase로 검증해 이메일이 관리자와 일치하는지 확인
async function verifyAdmin(request) {
  const token = (request.headers.get('Authorization') || '').replace(/^Bearer\s+/i, '');
  if (!token) return null;
  try {
    const r = await fetch(SUPABASE_URL + '/auth/v1/user', { headers: { apikey: SUPABASE_ANON, Authorization: 'Bearer ' + token } });
    if (!r.ok) return null;
    const u = await r.json();
    return (u && u.email && u.email.toLowerCase() === ADMIN_EMAIL) ? u : null;
  } catch (e) { return null; }
}

// 관리자 전용 주문 장부 조회(카드결제 orders 테이블) — service_role로 읽어 안전하게 반환
async function adminOrders(request, env) {
  if (!(await verifyAdmin(request))) return json({ error: '관리자 인증 실패' }, 403);
  if (!env.SUPABASE_SERVICE_KEY) return json({ error: 'SUPABASE_SERVICE_KEY 환경변수가 설정되지 않았습니다' }, 500);
  const url = new URL(request.url);
  const limit = Math.min(500, Number(url.searchParams.get('limit')) || 200);
  const r = await fetch(SUPABASE_URL + '/rest/v1/orders?select=*&order=created_at.desc&limit=' + limit, { headers: sbH(env) });
  if (!r.ok) return json({ error: '주문 조회 실패', detail: (await r.text()).slice(0, 200) }, 500);
  return json({ ok: true, orders: await r.json() });
}

async function createOrder(request, env) {
  let body; try { body = await request.json(); } catch (e) { return json({ error: 'bad json' }, 400); }
  const { items, email, userId } = body || {};
  if (!Array.isArray(items) || !items.length) return json({ error: '주문 항목이 없습니다' }, 400);
  if (!env.SUPABASE_SERVICE_KEY) return json({ error: 'SUPABASE_SERVICE_KEY 환경변수가 설정되지 않았습니다' }, 500);
  const origin = new URL(request.url).origin;
  const prices = (await assetJson(env, origin, '/content/booklet-prices.json')) || {};
  const passes = prices.passes || [];
  const tiers = prices.tiers || [[12, 2900], [24, 4900], [40, 7900], [70, 12900], [100000, 17900]];
  const overrides = prices.overrides || {};
  let course = null, prog = null;
  const resolved = [];
  for (const it of items) {
    const kind = it.kind, id = it.itemId;
    if (kind === 'pass') {
      const p = passes.find(x => x.id === id);
      if (!p) return json({ error: '잘못된 이용권: ' + id }, 400);
      resolved.push({ kind, itemId: id, name: p.name, amount: Number(p.price) });
    } else if (kind === 'book') {
      if (!course) course = (await assetJson(env, origin, '/content/course.json')) || { levels: [] };
      const tracks = (course.levels || []).map(l => ({ name: l.name || l.title, lessons: (l.lessons || []).length }));
      const t = tracks.find(x => x.name === id);
      if (!t) return json({ error: '잘못된 책자: ' + id }, 400);
      const ov = overrides[t.name] || {};
      const pages = ov.pages || Math.max(8, Math.round(t.lessons * 2.6) + 3);
      let price = (typeof ov.price === 'number') ? ov.price : tiers[tiers.length - 1][1];
      if (typeof ov.price !== 'number') { for (const [mx, pr] of tiers) { if (pages <= mx) { price = pr; break; } } }
      resolved.push({ kind, itemId: id, name: t.name + ' PDF 교재', amount: Number(price) });
    } else if (kind === 'cert') {
      if (!prog) prog = (await assetJson(env, origin, '/content/program.json')) || { ranks: [] };
      const r = (prog.ranks || []).find(x => String(x.rank) === String(id) || String(x.tier) === String(id) || x.name === id);
      if (!r) return json({ error: '잘못된 급수: ' + id }, 400);
      const amt = (it.earlybird && r.earlybird) ? r.earlybird : r.price;
      resolved.push({ kind, itemId: String(r.rank), name: '바이블 인사이트 ' + r.name + ' (' + r.rank + ')', amount: Number(amt), tier: Number(r.tier) || 0 });
    } else return json({ error: '알 수 없는 상품 유형: ' + kind }, 400);
  }
  const amount = resolved.reduce((s, x) => s + (Number(x.amount) || 0), 0);
  if (!(amount > 0)) return json({ error: '결제 금액이 0원입니다' }, 400);
  const first = resolved[0];
  const orderName = resolved.length > 1 ? (first.name + ' 외 ' + (resolved.length - 1) + '건') : first.name;
  const orderId = 'BIBLY-' + Date.now() + '-' + Math.random().toString(36).slice(2, 8);
  const ins = await fetch(SUPABASE_URL + '/rest/v1/orders', {
    method: 'POST', headers: { ...sbH(env), Prefer: 'return=minimal' },
    body: JSON.stringify({ order_id: orderId, email: email || null, user_id: userId || null, items: resolved, amount, status: 'pending' })
  });
  if (!ins.ok) return json({ error: '주문 생성 실패', detail: (await ins.text()).slice(0, 200) }, 500);
  return json({ orderId, amount, orderName });
}

async function grant(env, order) {
  const now = new Date();
  for (const it of (order.items || [])) {
    if (it.kind === 'pass') {
      const e = new Date(now); if (it.itemId === 'pass-life') e.setFullYear(e.getFullYear() + 100); else e.setFullYear(e.getFullYear() + 1);
      await upsert(env, 'pass_members', { email: order.email, expires_at: e.toISOString() }, 'email');
    } else if (it.kind === 'book') {
      const e = new Date(now); e.setFullYear(e.getFullYear() + 100);
      await upsert(env, 'book_access', { email: order.email, track: it.itemId, expires_at: e.toISOString() }, 'email,track');
    } else if (it.kind === 'cert') {
      const e = new Date(now); e.setMonth(e.getMonth() + 18);
      if (order.user_id) await upsert(env, 'cert_access', { user_id: order.user_id, tier: it.tier || 1, expires_at: e.toISOString() }, 'user_id');
    }
  }
}

async function confirmPay(request, env) {
  let b; try { b = await request.json(); } catch (e) { return json({ error: 'bad json' }, 400); }
  const { paymentKey, orderId, amount } = b || {};
  if (!paymentKey || !orderId || amount == null) return json({ error: '필수 파라미터 누락' }, 400);
  if (!env.SUPABASE_SERVICE_KEY) return json({ error: 'SUPABASE_SERVICE_KEY 환경변수가 설정되지 않았습니다' }, 500);
  const oR = await fetch(SUPABASE_URL + '/rest/v1/orders?order_id=eq.' + encodeURIComponent(orderId) + '&select=*', { headers: sbH(env) });
  const os = await oR.json().catch(() => []);
  const order = Array.isArray(os) ? os[0] : null;
  if (!order) return json({ error: '주문을 찾을 수 없습니다' }, 404);
  if (order.status === 'paid') return json({ ok: true, already: true, amount: order.amount, items: order.items });
  if (order.status !== 'pending') return json({ error: '결제할 수 없는 주문 상태입니다' }, 400);
  if (Number(order.amount) !== Number(amount)) return json({ error: '결제 금액이 주문 금액과 일치하지 않습니다' }, 400);
  const secret = env.TOSS_SECRET_KEY || TOSS_TEST_SECRET;
  let toss;
  try {
    const tR = await fetch('https://api.tosspayments.com/v1/payments/confirm', {
      method: 'POST', headers: { Authorization: 'Basic ' + btoa(secret + ':'), 'Content-Type': 'application/json' },
      body: JSON.stringify({ paymentKey, orderId, amount })
    });
    toss = await tR.json();
    if (!tR.ok || toss.status !== 'DONE') {
      await fetch(SUPABASE_URL + '/rest/v1/orders?order_id=eq.' + encodeURIComponent(orderId), { method: 'PATCH', headers: { ...sbH(env), Prefer: 'return=minimal' }, body: JSON.stringify({ status: 'failed' }) });
      return json({ error: (toss && toss.message) || '결제 승인에 실패했습니다', code: toss && toss.code }, 402);
    }
  } catch (e) { return json({ error: '결제 승인 통신 오류: ' + String(e.message || e) }, 502); }
  await grant(env, order);
  await fetch(SUPABASE_URL + '/rest/v1/orders?order_id=eq.' + encodeURIComponent(orderId), { method: 'PATCH', headers: { ...sbH(env), Prefer: 'return=minimal' }, body: JSON.stringify({ status: 'paid', payment_key: paymentKey, paid_at: new Date().toISOString() }) });
  return json({ ok: true, amount: order.amount, method: (toss && toss.method) || '카드', receipt: (toss && toss.receipt && toss.receipt.url) || null, items: order.items });
}

// ===== 유튜브 채널 실적 실시간 조회 (/api/yt/stats) =====
// API 키 없이 채널 페이지를 서버에서 읽어 파싱한다(키 노출 없음).
// 엣지에서 10분 캐시하므로 방문자가 많아도 유튜브 요청은 10분에 1회 수준.
const YT_CHANNEL_ID = 'UC82IOMnZud8NNt3BYzAxTMg';
function ytFmtPlus(n, step) { return (Math.floor(n / step) * step).toLocaleString('en-US') + '+'; }
function ytFmtMan(n) { return n >= 10000 ? Math.floor(n / 10000) + '만+' : ytFmtPlus(n, 100); }
function ytParseSubs(text) {
  const m = text.match(/"subscriberCountText":"구독자\s*([\d.]+)\s*(천|만)?\s*명"/);
  if (!m) return null;
  let v = parseFloat(m[1]);
  if (m[2] === '만') v *= 10000; else if (m[2] === '천') v *= 1000;
  return Math.round(v);
}
async function ytStats(env) {
  try {
    const r = await fetch('https://www.youtube.com/channel/' + YT_CHANNEL_ID + '/about', {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36',
        'Accept-Language': 'ko-KR,ko',
        'Cookie': 'CONSENT=YES+cb'
      },
      cf: { cacheTtl: 600, cacheEverything: true }   // 엣지 10분 캐시
    });
    if (!r.ok) return json({ ok: false }, 200);
    const html = await r.text();
    const subsN = ytParseSubs(html);
    const mv = html.match(/"viewCountText":"조회수\s*([\d,]+)회"/);
    const md = html.match(/"videoCountText":"동영상\s*([\d,]+)개"/);
    const out = { ok: true };
    if (subsN) out.subscribers = ytFmtPlus(subsN, 100);
    if (mv) out.views = ytFmtMan(parseInt(mv[1].replace(/,/g, ''), 10));
    if (md) out.videos = ytFmtPlus(parseInt(md[1].replace(/,/g, ''), 10), 10);
    if (!out.subscribers && !out.views && !out.videos) return json({ ok: false }, 200);
    return new Response(JSON.stringify(out), {
      headers: {
        'Content-Type': 'application/json; charset=utf-8',
        'Access-Control-Allow-Origin': '*',
        'Cache-Control': 'public, max-age=300, s-maxage=600'   // 브라우저 5분 · 엣지 10분
      }
    });
  } catch (e) { return json({ ok: false }, 200); }
}

// ── 관리자 공지 작성 API ─────────────────────────────────────
// notices 테이블은 RLS로 관리자 JWT만 쓰기 가능 → 운영 자동화를 위해
// 토큰(X-Admin-Token) 검증 후 service_role로 대신 씀.
// 코드에는 토큰의 SHA-256 해시만 둔다(원문 토큰은 로컬 운영도구에만 보관).
const ADMIN_TOKEN_SHA256 = 'f790dff64b077b5cbdbb829e5ef0c785c1b288d7f8d63f92f649adff40cb1893';
async function adminNotice(request, env) {
  const tok = request.headers.get('X-Admin-Token') || '';
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(tok));
  const hex = [...new Uint8Array(buf)].map(b => b.toString(16).padStart(2, '0')).join('');
  if (hex !== ADMIN_TOKEN_SHA256) return json({ error: '인증 실패' }, 403);
  if (!env.SUPABASE_SERVICE_KEY) return json({ error: 'SUPABASE_SERVICE_KEY 환경변수가 설정되지 않았습니다' }, 500);
  let body; try { body = await request.json(); } catch (e) { return json({ error: 'bad json' }, 400); }
  const { id, kind, title, pinned } = body || {};
  if (!title || !body.body) return json({ error: 'title/body 필수' }, 400);
  const row = { kind: kind === 'event' ? 'event' : 'notice', title: String(title).slice(0, 200), body: String(body.body), pinned: !!pinned };
  // id가 오면 해당 글 수정(PATCH), 없으면 새 글 작성(POST)
  const url = SUPABASE_URL + '/rest/v1/notices' + (id ? '?id=eq.' + Number(id) : '');
  const r = await fetch(url, {
    method: id ? 'PATCH' : 'POST', headers: { ...sbH(env), Prefer: 'return=representation' }, body: JSON.stringify(row)
  });
  if (!r.ok) return json({ error: '작성 실패', detail: (await r.text()).slice(0, 200) }, 500);
  const rows = await r.json();
  return json({ ok: true, id: rows[0] && rows[0].id });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const p = url.pathname;
    if (p === '/api/yt/stats') return ytStats(env);
    if (p === '/api/admin/notice' && request.method === 'POST') return adminNotice(request, env);
    if (p.startsWith('/api/pay/')) {
      if (request.method === 'OPTIONS') return new Response(null, { headers: { 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Methods': 'GET,POST,OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type' } });
      if (p === '/api/pay/ping') return ping(env);
      if (p === '/api/pay/create-order' && request.method === 'POST') return createOrder(request, env);
      if (p === '/api/pay/confirm' && request.method === 'POST') return confirmPay(request, env);
      if (p === '/api/pay/admin/orders') return adminOrders(request, env);
      return json({ error: 'not found' }, 404);
    }
    // 그 외 모든 요청 → 정적 자산(사이트)
    return env.ASSETS.fetch(request);
  }
};
