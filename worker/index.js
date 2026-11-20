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
      // 얼리버드는 기수(cohort) 마감 전까지만 서버에서 인정한다 — 화면과 무관하게 여기서 최종 검증(2026-11-21).
      // (이전에는 클라이언트가 earlybird:true를 보내면 마감 후에도 얼리버드 금액이 적용되는 버그가 있었다)
      const cohortOpen = (() => {
        const c = prog.cohort; if (!c || !c.deadline) return false;
        const end = new Date(c.deadline + 'T23:59:59+09:00');          // 마감일 자정(KST)까지 유효 — academy.html과 동일 규칙
        return !isNaN(end) && (end - new Date()) >= 0;
      })();
      const amt = (it.earlybird && r.earlybird && cohortOpen) ? r.earlybird : r.price;
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

// 권한 부여 — ⚠서비스 제공기간은 전자결제 정책상 12개월을 넘길 수 없다(2026-08-13 정비).
// pass(전체 이용권)·cert(인증과정) = 12개월. book(개별 책자)은 PDF 즉시 다운로드 상품이라
// 다운로드본은 영구 소장이며, 온라인 열람 권한만 12개월로 둔다.
async function grant(env, order) {
  const now = new Date();
  const plusYear = () => { const e = new Date(now); e.setFullYear(e.getFullYear() + 1); return e.toISOString(); };
  for (const it of (order.items || [])) {
    if (it.kind === 'pass') {
      // pass-life(평생소장)는 판매 중단 — 혹시 남은 주문이 들어와도 1년으로 부여한다.
      await upsert(env, 'pass_members', { email: order.email, expires_at: plusYear() }, 'email');
    } else if (it.kind === 'book') {
      await upsert(env, 'book_access', { email: order.email, track: it.itemId, expires_at: plusYear() }, 'email,track');
    } else if (it.kind === 'cert') {
      if (order.user_id) await upsert(env, 'cert_access', { user_id: order.user_id, tier: it.tier || 1, expires_at: plusYear() }, 'user_id');
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

// ===== 회원 본인 주문·결제 내역 (/api/pay/my-orders) =====
// orders(카드결제)·course_applications(무통장·송금 주문)는 RLS상 관리자만 읽을 수 있으므로,
// 로그인 토큰을 Supabase로 검증한 뒤 그 회원의 이메일·user_id 에 해당하는 행만 service_role 로 골라 돌려준다.
async function verifyUser(request) {
  const token = (request.headers.get('Authorization') || '').replace(/^Bearer\s+/i, '');
  if (!token) return null;
  try {
    const r = await fetch(SUPABASE_URL + '/auth/v1/user', { headers: { apikey: SUPABASE_ANON, Authorization: 'Bearer ' + token } });
    if (!r.ok) return null;
    const u = await r.json();
    return (u && u.id && u.email) ? u : null;
  } catch (e) { return null; }
}
async function sbGet(env, path) {
  try { const r = await fetch(SUPABASE_URL + '/rest/v1/' + path, { headers: sbH(env) }); return r.ok ? await r.json() : []; } catch (e) { return []; }
}
// 무통장 주문 기록(motivation)의 "상품:이름(₩1,234), 이름2(₩5,678)" 를 항목 배열로
function parseBankItems(s) {
  const m = String(s || '').match(/상품:(.*?)(?:\s\|\s|$)/); if (!m) return [];
  const out = []; const re = /(.+?)\(₩([\d,]+)\)(?:,\s*|$)/g; let x;
  while ((x = re.exec(m[1]))) out.push({ name: x[1].trim(), amount: Number(x[2].replace(/,/g, '')) || 0 });
  return out;
}
function pick(re, s) { const m = String(s || '').match(re); return m ? m[1].trim() : ''; }
async function myOrders(request, env) {
  const u = await verifyUser(request);
  if (!u) return json({ error: '로그인이 필요합니다' }, 401);
  if (!env.SUPABASE_SERVICE_KEY) return json({ error: 'SUPABASE_SERVICE_KEY 환경변수가 설정되지 않았습니다' }, 500);
  const email = u.email.toLowerCase();
  // ilike 로 대소문자만 무시하고, _·% 는 와일드카드가 되지 않게 이스케이프(남의 주문이 섞이지 않도록)
  const enc = (v) => encodeURIComponent(v);
  const em = enc(email.replace(/([\\_%])/g, '\\$1'));
  const [byEmail, byUser, apps, passRows, bookRows] = await Promise.all([
    sbGet(env, 'orders?select=order_id,email,items,amount,status,paid_at,created_at&email=ilike.' + em + '&order=created_at.desc&limit=200'),
    sbGet(env, 'orders?select=order_id,email,items,amount,status,paid_at,created_at&user_id=eq.' + enc(u.id) + '&order=created_at.desc&limit=200'),
    sbGet(env, 'course_applications?select=id,interest,motivation,created_at&email=ilike.' + em + '&interest=like.' + enc('북스토어 주문*') + '&order=created_at.desc&limit=200'),
    sbGet(env, 'pass_members?select=expires_at&email=ilike.' + em),
    sbGet(env, 'book_access?select=track,expires_at&email=ilike.' + em)
  ]);
  const seen = new Set(); const list = [];
  for (const o of [...(byEmail || []), ...(byUser || [])]) {
    if (!o || seen.has(o.order_id)) continue; seen.add(o.order_id);
    // 결제창만 열고 닫은 주문(pending)·승인 실패는 내역에 보이지 않게 한다 — 실제 결제된 건만
    if (o.status !== 'paid' && o.status !== 'canceled' && o.status !== 'refunded') continue;
    list.push({ id: o.order_id, type: 'card', method: '카드결제', status: o.status, amount: Number(o.amount) || 0,
      items: (o.items || []).map(it => ({ kind: it.kind, itemId: it.itemId, name: it.name, amount: Number(it.amount) || 0 })),
      date: o.paid_at || o.created_at });
  }
  const hasPass = (passRows || []).length > 0;
  const tracks = new Set((bookRows || []).map(b => b.track));
  for (const a of (apps || [])) {
    const items = parseBankItems(a.motivation);
    // 입금 확인 = 담당자가 권한을 열어 줬는지로 판단(이용권은 pass_members, 책자는 book_access)
    const granted = items.length > 0 && items.every(it => /이용권/.test(it.name) ? hasPass : tracks.has(it.name));
    list.push({ id: pick(/주문번호:([^|]+)/, a.motivation) || String(a.id).slice(0, 8), type: 'bank',
      method: pick(/결제:([^|]+)/, a.motivation) || '무통장입금', status: granted ? 'paid' : 'waiting',
      amount: items.reduce((s, x) => s + x.amount, 0), items: items.map(it => ({ kind: /이용권/.test(it.name) ? 'pass' : 'book', itemId: it.name, name: it.name, amount: it.amount })),
      date: a.created_at });
  }
  list.sort((a, b) => String(b.date).localeCompare(String(a.date)));
  return json({ ok: true, email: u.email, orders: list });
}
// 카드 매출전표(토스 영수증) 주소 — 본인 주문인지 확인한 뒤 토스에서 조회해 돌려준다
async function myReceipt(request, env) {
  const u = await verifyUser(request);
  if (!u) return json({ error: '로그인이 필요합니다' }, 401);
  const orderId = new URL(request.url).searchParams.get('orderId') || '';
  const os = await sbGet(env, 'orders?select=order_id,email,user_id,payment_key,status&order_id=eq.' + encodeURIComponent(orderId));
  const o = Array.isArray(os) ? os[0] : null;
  const mine = o && (o.user_id === u.id || String(o.email || '').toLowerCase() === u.email.toLowerCase());
  if (!mine) return json({ error: '주문을 찾을 수 없습니다' }, 404);
  if (!o.payment_key) return json({ error: '결제 정보가 없습니다' }, 404);
  try {
    const secret = env.TOSS_SECRET_KEY || TOSS_TEST_SECRET;
    const r = await fetch('https://api.tosspayments.com/v1/payments/' + encodeURIComponent(o.payment_key), { headers: { Authorization: 'Basic ' + btoa(secret + ':') } });
    const t = await r.json();
    const url = t && t.receipt && t.receipt.url;
    if (!url) return json({ error: '영수증을 찾지 못했습니다' }, 404);
    return json({ ok: true, url, status: t.status || '' });
  } catch (e) { return json({ error: '영수증 조회 오류' }, 502); }
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
    // 1만 미만은 10 단위 내림 — 100 단위면 며칠씩 같은 숫자로 보여 '갱신이 안 된다'는 인상을 준다
    if (subsN) out.subscribers = ytFmtPlus(subsN, subsN < 10000 ? 10 : 100);
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

// ===== 강의별 메타 주입 (/watch?v=<유튜브ID>) =====
// watch.html은 클라이언트 렌더라 title·og:*가 329편 모두 공통값이었다(카톡·네이버 공유 카드가 전부 같고, 검색엔진엔 한 페이지로 뭉침).
// 여기서 course.json을 읽어 해당 강의의 제목·소개·썸네일로 <head>를 고쳐 보낸다. 못 찾으면 원본 그대로 통과.
let COURSE_CACHE = { t: 0, data: null };
async function courseJson(env, origin) {
  if (COURSE_CACHE.data && Date.now() - COURSE_CACHE.t < 600000) return COURSE_CACHE.data;   // 10분 메모리 캐시
  const d = await assetJson(env, origin, '/content/course.json');
  if (d) COURSE_CACHE = { t: Date.now(), data: d };
  return d || COURSE_CACHE.data;
}
// course.json의 youtube 필드는 URL 또는 맨 11자 ID(43편) 두 형태가 섞여 있다 — watch.html의 ytId와 같은 규칙
function ytIdOf(u) { u = String(u || '').trim(); const m = u.match(/(?:v=|youtu\.be\/|embed\/|shorts\/)([\w-]{11})/); return m ? m[1] : (/^[\w-]{11}$/.test(u) ? u : ''); }
function attr(s) { return String(s || '').replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }
function isoDuration(s) {   // "12:34" / "1:02:03" → PT12M34S / PT1H2M3S
  const p = String(s || '').split(':').map(Number);
  if (!p.length || p.some(isNaN)) return null;
  const [h, m, sec] = p.length === 3 ? p : p.length === 2 ? [0, p[0], p[1]] : [0, 0, p[0]];
  return 'PT' + (h ? h + 'H' : '') + (m ? m + 'M' : '') + (sec ? sec + 'S' : '');
}
async function watchMeta(request, env, url) {
  const res = await env.ASSETS.fetch(request);
  if (!res.ok || !(res.headers.get('Content-Type') || '').includes('text/html')) return res;
  const vid = (url.searchParams.get('v') || '').trim();
  if (!/^[\w-]{11}$/.test(vid)) return res;
  const course = await courseJson(env, url.origin);
  let lesson = null, track = '', ti = -1;
  ((course && course.levels) || []).some((lv, i) => {
    const f = (lv.lessons || []).find(l => ytIdOf(l.youtube) === vid);
    if (f) { lesson = f; track = lv.name || ''; ti = i; return true; }
    return false;
  });
  if (!lesson) return res;
  const title = String(lesson.title || '').trim();
  const desc = String(lesson.summary || '').replace(/\s+/g, ' ').trim().slice(0, 160) || ('무료 강의 · ' + track + ' · 영상+요약노트+진단평가');
  const canon = 'https://biblynote.com/watch?v=' + vid;
  const thumb = 'https://i.ytimg.com/vi/' + vid + '/maxresdefault.jpg';
  const video = { '@context': 'https://schema.org', '@type': 'VideoObject', name: title, description: desc, thumbnailUrl: [thumb, 'https://i.ytimg.com/vi/' + vid + '/hqdefault.jpg'],
    embedUrl: 'https://www.youtube.com/embed/' + vid, url: canon, inLanguage: 'ko', isAccessibleForFree: true,
    publisher: { '@type': 'Organization', name: 'BIBLY 바이블 인사이트', url: 'https://biblynote.com' } };
  if (lesson.added) video.uploadDate = lesson.added;
  const dur = isoDuration(lesson.duration); if (dur) video.duration = dur;
  const crumb = { '@context': 'https://schema.org', '@type': 'BreadcrumbList', itemListElement: [
    { '@type': 'ListItem', position: 1, name: '홈', item: 'https://biblynote.com/' },
    { '@type': 'ListItem', position: 2, name: '커리큘럼', item: 'https://biblynote.com/curriculum' },
    { '@type': 'ListItem', position: 3, name: track, item: 'https://biblynote.com/curriculum?track=' + ti },
    { '@type': 'ListItem', position: 4, name: title, item: canon }
  ] };
  const ld = s => '<script type="application/ld+json">' + JSON.stringify(s).replace(/<\//g, '<\\/') + '</script>';
  const extra = `<meta property="og:url" content="${attr(canon)}" /><meta property="og:video" content="https://www.youtube.com/embed/${vid}" /><meta property="og:video:type" content="text/html" /><meta property="og:video:width" content="1280" /><meta property="og:video:height" content="720" />` + ld(video) + ld(crumb);
  const out = new HTMLRewriter()
    .on('title', { element(e) { e.setInnerContent(title + ' · 바이블 인사이트'); } })
    .on('meta[name="description"]', { element(e) { e.setAttribute('content', desc); } })
    .on('meta[property="og:title"]', { element(e) { e.setAttribute('content', title); } })
    .on('meta[property="og:description"]', { element(e) { e.setAttribute('content', desc); } })
    .on('meta[property="og:image"]', { element(e) { e.setAttribute('content', thumb); } })
    .on('meta[name="twitter:image"]', { element(e) { e.setAttribute('content', thumb); } })
    .on('link[rel="canonical"]', { element(e) { e.setAttribute('href', canon); } })
    .on('head', { element(e) { e.append(extra, { html: true }); } })
    .transform(res);
  const h = new Headers(out.headers);
  h.set('Cache-Control', 'public, max-age=600');
  return new Response(out.body, { status: out.status, headers: h });
}

// ═══════════════════════════════════════════════════════════════════
// A.W.F 자동수익 퍼널 — 리드 수집 + 이메일 자동 육성(7번의 법칙) (2026-11-21)
// 테이블: marketing_leads, email_queue (tools/sql/funnel_tables.sql 로 생성)
// 발송: Resend — RESEND_API_KEY 시크릿이 등록된 경우에만 발송(없으면 조용히 대기)
// ═══════════════════════════════════════════════════════════════════
const SITE = 'https://www.biblynote.com';
const EMAIL_FROM_DEFAULT = 'BIBLY 바이블 인사이트 <news@biblynote.com>';

function rndToken() {
  const a = new Uint8Array(16); crypto.getRandomValues(a);
  return [...a].map(b => b.toString(16).padStart(2, '0')).join('');
}
function kstDate(s) { return new Date(s + 'T23:59:59+09:00'); }

// 육성 시퀀스 일정(옵트인 시각 기준 지연 일수) — #7(마감 임박)은 cohort.deadline-3일로 동적 계산
const NURTURE_STEPS = [
  { step: 1, days: 0 }, { step: 2, days: 1 }, { step: 3, days: 3 },
  { step: 4, days: 5 }, { step: 5, days: 8 }, { step: 6, days: 12 }
];

// POST /api/lead — 옵트인(start)·상담 신청(consult) 리드 기록 + 육성 메일 예약
async function leadCreate(request, env) {
  let b; try { b = await request.json(); } catch (e) { return json({ error: 'bad json' }, 400); }
  const email = String((b && b.email) || '').trim().toLowerCase();
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return json({ error: '이메일이 올바르지 않습니다' }, 400);
  if (!env.SUPABASE_SERVICE_KEY) return json({ ok: false, error: 'no service key' }, 200);
  const kind = (b.kind === 'consult') ? 'consult' : 'optin';
  const row = {
    email,
    name: String(b.name || '').slice(0, 60) || null,
    topic: String(b.topic || '').slice(0, 40) || null,
    src: String(b.src || '').slice(0, 60) || null,
    kind,
    note: b.note ? String(typeof b.note === 'string' ? b.note : JSON.stringify(b.note)).slice(0, 4000) : null,
    status: 'active'
  };
  // 이미 있는 리드인지 확인(재옵트인 시 메일 중복 예약 방지)
  let existing = null;
  try {
    const r = await fetch(SUPABASE_URL + '/rest/v1/marketing_leads?select=id,unsub_token,status,kind&email=eq.' + encodeURIComponent(email), { headers: sbH(env) });
    const rows = r.ok ? await r.json() : [];
    existing = Array.isArray(rows) ? rows[0] : null;
  } catch (e) {}
  let leadId = existing && existing.id;
  if (!existing) {
    row.unsub_token = rndToken();
    const ins = await fetch(SUPABASE_URL + '/rest/v1/marketing_leads', { method: 'POST', headers: { ...sbH(env), Prefer: 'return=representation' }, body: JSON.stringify(row) });
    if (!ins.ok) return json({ ok: false, error: 'lead insert 실패', detail: (await ins.text()).slice(0, 180) }, 200);
    const rows = await ins.json(); leadId = rows[0] && rows[0].id;
  } else if (kind === 'consult') {
    // 기존 리드가 상담을 신청하면 kind·메모만 승격
    await fetch(SUPABASE_URL + '/rest/v1/marketing_leads?id=eq.' + existing.id, { method: 'PATCH', headers: { ...sbH(env), Prefer: 'return=minimal' }, body: JSON.stringify({ kind: 'consult', note: row.note, name: row.name || undefined }) });
  }
  if (!leadId) return json({ ok: false }, 200);

  // 메일 예약 — 옵트인: 육성 7단 / 상담: 접수 확인 1통(즉시)
  const now = Date.now();
  const queue = [];
  if (kind === 'consult') {
    queue.push({ lead_id: leadId, step: 'c1', due_at: new Date(now).toISOString() });
  } else if (!existing) {
    for (const s of NURTURE_STEPS) queue.push({ lead_id: leadId, step: 'n' + s.step, due_at: new Date(now + s.days * 86400000).toISOString() });
    // #7 기수 마감 임박(D-3) — program.json 의 cohort.deadline 기준, 과거면 생략
    try {
      const prog = await assetJson(env, new URL(request.url).origin, '/content/program.json');
      const dl = prog && prog.cohort && prog.cohort.deadline && kstDate(prog.cohort.deadline);
      if (dl && !isNaN(dl)) {
        const d3 = dl.getTime() - 3 * 86400000;
        if (d3 > now) queue.push({ lead_id: leadId, step: 'n7', due_at: new Date(d3).toISOString() });
      }
    } catch (e) {}
  }
  if (queue.length) {
    await fetch(SUPABASE_URL + '/rest/v1/email_queue', { method: 'POST', headers: { ...sbH(env), Prefer: 'return=minimal' }, body: JSON.stringify(queue) }).catch(() => {});
  }
  return json({ ok: true });
}

// GET /api/lead/unsub?t=토큰 — 수신거부(정보통신망법) : 한 번의 클릭으로 모든 발송 중단
async function leadUnsub(request, env) {
  const t = new URL(request.url).searchParams.get('t') || '';
  const page = (msg) => new Response(
    '<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
    + '<body style="font-family:sans-serif;display:flex;align-items:center;justify-content:center;min-height:90vh;text-align:center;color:#213a6b">'
    + '<div><h2 style="margin:0 0 10px">' + msg + '</h2><p style="color:#889;font-size:14px">BIBLY 바이블 인사이트 · biblynote.com</p></div></body>',
    { headers: { 'Content-Type': 'text/html; charset=utf-8' } });
  if (!/^[0-9a-f]{32}$/.test(t) || !env.SUPABASE_SERVICE_KEY) return page('잘못된 요청입니다');
  const r = await fetch(SUPABASE_URL + '/rest/v1/marketing_leads?unsub_token=eq.' + t, {
    method: 'PATCH', headers: { ...sbH(env), Prefer: 'return=representation' }, body: JSON.stringify({ status: 'unsubscribed' })
  });
  const rows = r.ok ? await r.json() : [];
  return page(rows.length ? '수신거부가 완료되었습니다. 더 이상 메일을 보내지 않습니다.' : '잘못된 요청입니다');
}

// ── 육성 메일 본문(7단) — 모든 제목에 (광고), 하단에 수신거부 링크(정보통신망법 준수) ──
function mailLayout(bodyHtml, unsubUrl) {
  return '<div style="max-width:560px;margin:0 auto;font-family:-apple-system,\'Malgun Gothic\',sans-serif;color:#1c2b45;line-height:1.75;font-size:15px">'
    + '<p style="font-weight:800;color:#00704a;font-size:13px;letter-spacing:.1em">BIBLY 바이블 인사이트</p>'
    + bodyHtml
    + '<hr style="border:none;border-top:1px solid #e5e9f0;margin:28px 0 14px">'
    + '<p style="font-size:11.5px;color:#9aa3b2">본 메일은 biblynote.com에서 무료 자료·특강을 신청하신 분께 발송되는 광고성 정보입니다.<br>'
    + 'BIBLY 바이블 인사이트 · 문의 biblynote.com/counsel<br>'
    + '<a href="' + unsubUrl + '" style="color:#9aa3b2">수신거부 Unsubscribe</a></p></div>';
}
function btn(href, label) {
  return '<p style="margin:22px 0"><a href="' + href + '" style="background:#00704a;color:#fff;text-decoration:none;font-weight:700;padding:13px 26px;border-radius:12px;display:inline-block">' + label + '</a></p>';
}
function buildMail(step, lead, ctx) {
  const t = lead.topic ? '&t=' + encodeURIComponent(lead.topic) : '';
  const nm = lead.name ? lead.name + '님' : '성도님';
  const cohort = ctx.cohortName || '이번 기수';
  const M = {
    n1: {
      subject: '(광고) 신청하신 무료 자료와 특강 입장 안내입니다',
      body: '<h2 style="font-size:20px">' + nm + ', 환영합니다 🙂</h2>'
        + '<p>신청하신 무료 자료를 바로 받아보실 수 있습니다.</p>'
        + btn(SITE + (ctx.leadFile || '/files/종말핵심-한눈에-보기.pdf'), '📄 무료 PDF 내려받기')
        + '<p>그리고 하나 더 — 흩어진 종말 예언을 50분에 하나로 꿰어 드리는 <b>온라인 특강</b>을 준비해 두었습니다. 지금 바로 보실 수 있습니다.</p>'
        + btn(SITE + '/seminar.html?src=em1' + t, '▶ 무료 특강 바로 보기')
    },
    n2: {
      subject: '(광고) 어제 특강, 끝까지 보셨나요? 핵심 3가지만 다시 짚어드립니다',
      body: '<h2 style="font-size:20px">특강 핵심 3가지</h2>'
        + '<p>① 예언은 공포가 아니라 <b>소망의 지도</b>입니다 — 순서를 알면 두렵지 않습니다.<br>'
        + '② 흩어진 구절이 아니라 <b>성경 전체의 흐름</b>으로 읽어야 합니다.<br>'
        + '③ 분별력은 타고나는 것이 아니라 <b>단계를 밟아 길러지는 것</b>입니다.</p>'
        + '<p>아직 다 못 보셨다면 이어서 보세요. 보던 자리에서 다시 시작됩니다.</p>'
        + btn(SITE + '/seminar.html?src=em2' + t, '▶ 특강 이어 보기')
    },
    n3: {
      subject: '(광고) 흔들리지 않는 분별력은 이렇게 길러집니다',
      body: '<h2 style="font-size:20px">듣는 공부에서, 답하는 공부로</h2>'
        + '<p>설교를 많이 들어도 종말의 순서가 늘 헷갈리는 이유는 간단합니다 — 흩어진 조각으로만 들었기 때문입니다. 순서대로, 본문의 맥락대로 밟아 가면 누구든 꿰어집니다.</p>'
        + '<p>바이블 인사이트에는 그 순서를 따라 설계된 <b>370편 이상의 강의가 전부 무료</b>로 열려 있습니다. 먼저 내 수준이 어디쯤인지 가볍게 확인해 보세요.</p>'
        + btn(SITE + '/level.html?src=em3', '내 성경 이해 진단받기 (3분)')
    },
    n4: {
      subject: '(광고) 내 성경 이해, 몇 급일까요? — 3분 진단',
      body: '<h2 style="font-size:20px">' + nm + '의 분별력은 지금 몇 급일까요?</h2>'
        + '<p>10문항 · 3분이면 끝납니다. 점수에 따라 지금 바로 시작할 과정을 맞춤으로 추천해 드립니다.</p>'
        + btn(SITE + '/level.html?src=em4', '무료 진단 시작하기')
        + '<p style="font-size:13.5px;color:#66708a">진단은 무료이고, 결과 화면에서 맞춤 학습 로드맵을 바로 확인하실 수 있습니다.</p>'
    },
    n5: {
      subject: '(광고) ' + cohort + ' 등록 안내 — 수료증이 나오는 성경 인증과정',
      body: '<h2 style="font-size:20px">강의는 평생 무료, 인증은 ' + cohort + '부터</h2>'
        + '<p>바이블 인사이트의 모든 강의는 무료입니다. 유료인 것은 단 하나 — 강의마다 시험을 치르고 학점을 쌓아 <b>급수 수료증</b>으로 증명하는 인증과정입니다.</p>'
        + '<p>5급(29,000원대)부터 1급까지, 지금은 ' + cohort + ' 모집 중입니다. 5일 무료체험으로 먼저 경험해 보세요.</p>'
        + btn(SITE + '/academy.html?src=em5', cohort + ' 자세히 보기')
    },
    n6: {
      subject: '(광고) "강의가 전부 무료인데, 왜 등록하나요?" — 가장 많이 받는 질문',
      body: '<h2 style="font-size:20px">자주 묻는 질문</h2>'
        + '<p><b>Q. 강의가 무료인데 인증과정은 왜 필요한가요?</b><br>듣기만 한 공부는 흩어집니다. 시험으로 확인하고 수료증으로 증명할 때 분별력이 내 것이 됩니다. 교회에서 가르치는 분들이 특히 많이 등록하십니다.</p>'
        + '<p><b>Q. 나이가 많아도 따라갈 수 있나요?</b><br>수강생의 다수가 40~60대이십니다. 영상 1편 + 요약노트 + 20문항 시험의 단순한 반복이라 스마트폰만 있으면 됩니다.</p>'
        + '<p><b>Q. 어렵지 않을까요?</b><br>5급은 신앙의 기초부터 시작합니다. 진단 결과에 맞는 급수부터 시작하면 됩니다.</p>'
        + btn(SITE + '/academy.html?src=em6', '내게 맞는 급수 보기')
    },
    n7: {
      subject: '(광고) [마감 D-3] ' + cohort + ' 등록이 곧 마감됩니다',
      body: '<h2 style="font-size:20px">' + cohort + ' 마감이 사흘 앞으로 왔습니다</h2>'
        + '<p>' + (ctx.deadline ? ctx.deadline + ' 자정(한국시간)에 등록이 마감' : '곧 등록이 마감') + '되고, 다음 기수는 등록가가 달라질 수 있습니다.</p>'
        + '<p>고민되신다면 5일 무료체험부터 시작하셔도 좋습니다 — 체험 중 등록하면 그대로 이어집니다.</p>'
        + btn(SITE + '/academy.html?src=em7', '마감 전에 등록하기')
    },
    c1: {
      subject: '[BIBLY] 심화 과정 상담 신청이 접수되었습니다',
      body: '<h2 style="font-size:20px">' + nm + ', 신청서를 잘 받았습니다</h2>'
        + '<p>작성해 주신 내용을 대표강사가 직접 검토한 뒤 <b>24시간 안에</b> 안내드리겠습니다. 정원이 있는 과정이라 모든 분을 모시지 못하는 점은 양해 부탁드립니다.</p>'
        + (ctx.bookingUrl ? ('<p>검토를 기다리는 동안, 아래에서 편하신 <b>15분 전화 상담 시간</b>을 먼저 골라 두셔도 좋습니다.</p>' + btn(ctx.bookingUrl, '상담 시간 예약하기')) : '')
        + '<p style="font-size:13.5px;color:#66708a">그동안 무료 특강을 아직 안 보셨다면 먼저 보고 오시면 상담이 훨씬 빨라집니다 → <a href="' + SITE + '/seminar.html?src=c1" style="color:#00704a">특강 보기</a></p>'
    }
  };
  return M[step] || null;
}

// cron 디스패처 — 매시간: 발송 시각이 된 큐를 꺼내 Resend 로 발송
async function processEmailQueue(env) {
  if (!env.SUPABASE_SERVICE_KEY || !env.RESEND_API_KEY) return;   // 키가 없으면 조용히 대기(등록 즉시 작동 시작)
  const nowIso = new Date().toISOString();
  const qR = await fetch(SUPABASE_URL + '/rest/v1/email_queue?select=id,lead_id,step,tries&sent_at=is.null&tries=lt.3&due_at=lte.' + encodeURIComponent(nowIso) + '&order=due_at.asc&limit=40', { headers: sbH(env) });
  const q = qR.ok ? await qR.json() : [];
  if (!Array.isArray(q) || !q.length) return;
  const ids = [...new Set(q.map(x => x.lead_id))];
  const lR = await fetch(SUPABASE_URL + '/rest/v1/marketing_leads?select=id,email,name,topic,status,unsub_token&id=in.(' + ids.join(',') + ')', { headers: sbH(env) });
  const leads = lR.ok ? await lR.json() : [];
  const byId = {}; for (const l of leads) byId[l.id] = l;
  // 발송 문맥(기수·예약 링크·리드마그넷)은 자산에서 1회 로드
  const prog = await assetJson(env, SITE, '/content/program.json');
  const consult = await assetJson(env, SITE, '/content/consult.json');
  const site = await assetJson(env, SITE, '/content/site.json');
  const ctx = {
    cohortName: prog && prog.cohort && prog.cohort.name,
    deadline: prog && prog.cohort && prog.cohort.deadline,
    bookingUrl: consult && consult.bookingUrl,
    leadFile: site && site.leadmagnet && site.leadmagnet.file
  };
  for (const item of q) {
    const lead = byId[item.lead_id];
    const mark = (patch) => fetch(SUPABASE_URL + '/rest/v1/email_queue?id=eq.' + item.id, { method: 'PATCH', headers: { ...sbH(env), Prefer: 'return=minimal' }, body: JSON.stringify(patch) }).catch(() => {});
    if (!lead || lead.status !== 'active') { await mark({ sent_at: nowIso, skipped: true }); continue; }
    const m = buildMail(item.step, lead, ctx);
    if (!m) { await mark({ sent_at: nowIso, skipped: true }); continue; }
    const unsubUrl = SITE + '/api/lead/unsub?t=' + lead.unsub_token;
    try {
      const r = await fetch('https://api.resend.com/emails', {
        method: 'POST', headers: { Authorization: 'Bearer ' + env.RESEND_API_KEY, 'Content-Type': 'application/json' },
        body: JSON.stringify({ from: env.RESEND_FROM || EMAIL_FROM_DEFAULT, to: [lead.email], subject: m.subject, html: mailLayout(m.body, unsubUrl) })
      });
      if (r.ok) await mark({ sent_at: new Date().toISOString() });
      else await mark({ tries: (item.tries || 0) + 1, last_error: (await r.text()).slice(0, 300) });
    } catch (e) { await mark({ tries: (item.tries || 0) + 1, last_error: String(e && e.message || e).slice(0, 300) }); }
  }
}

// GET /api/admin/funnel — 퍼널 계기판(관리자): 방문→옵트인→상담→결제 단계별 숫자
async function adminFunnel(request, env) {
  if (!(await verifyAdmin(request))) return json({ error: '관리자 인증 실패' }, 403);
  if (!env.SUPABASE_SERVICE_KEY) return json({ error: 'SUPABASE_SERVICE_KEY 없음' }, 500);
  const since = new Date(Date.now() - 30 * 86400000).toISOString();
  const cnt = async (path) => {
    try {
      const r = await fetch(SUPABASE_URL + '/rest/v1/' + path, { method: 'HEAD', headers: { ...sbH(env), Prefer: 'count=exact' } });
      const m = (r.headers.get('content-range') || '').match(/\/(\d+)/); return m ? Number(m[1]) : 0;
    } catch (e) { return 0; }
  };
  const [visits, srcRows, leads, consults, unsubs, queued, sent, orders] = await Promise.all([
    cnt('site_visits?select=id&created_at=gte.' + since),
    sbGet(env, 'site_visits?select=path&created_at=gte.' + since + '&path=like.' + encodeURIComponent('*src=*') + '&limit=5000'),
    cnt('marketing_leads?select=id&created_at=gte.' + since),
    cnt('marketing_leads?select=id&kind=eq.consult&created_at=gte.' + since),
    cnt('marketing_leads?select=id&status=eq.unsubscribed'),
    cnt('email_queue?select=id&sent_at=is.null'),
    cnt('email_queue?select=id&sent_at=not.is.null&due_at=gte.' + since),
    sbGet(env, 'orders?select=amount,status,items,created_at&created_at=gte.' + since + '&order=created_at.desc&limit=500')
  ]);
  const bySrc = {};
  for (const v of (srcRows || [])) { const m = String(v.path || '').match(/src=([\w-]+)/); if (m) bySrc[m[1]] = (bySrc[m[1]] || 0) + 1; }
  const paid = (orders || []).filter(o => o.status === 'paid');
  return json({
    ok: true, since,
    visits, bySrc, leads, consults, unsubs,
    emails: { queued, sent30d: sent },
    orders: { paid: paid.length, revenue: paid.reduce((s, o) => s + (Number(o.amount) || 0), 0) }
  });
}

export default {
  async scheduled(event, env, ctx) { ctx.waitUntil(processEmailQueue(env)); },
  async fetch(request, env) {
    const url = new URL(request.url);
    const p = url.pathname;
    if (p === '/api/yt/stats') return ytStats(env);
    if (p === '/api/lead' && request.method === 'OPTIONS') return new Response(null, { headers: { 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Methods': 'POST,OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type' } });
    if (p === '/api/lead' && request.method === 'POST') return leadCreate(request, env);
    if (p === '/api/lead/unsub') return leadUnsub(request, env);
    if (p === '/api/admin/funnel') return adminFunnel(request, env);
    if ((p === '/watch' || p === '/watch.html') && request.method === 'GET' && url.searchParams.get('v')) return watchMeta(request, env, url);
    if (p === '/api/admin/notice' && request.method === 'POST') return adminNotice(request, env);
    if (p.startsWith('/api/pay/')) {
      if (request.method === 'OPTIONS') return new Response(null, { headers: { 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Methods': 'GET,POST,OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type, Authorization' } });
      if (p === '/api/pay/ping') return ping(env);
      if (p === '/api/pay/my-orders') return myOrders(request, env);
      if (p === '/api/pay/my-receipt') return myReceipt(request, env);
      if (p === '/api/pay/create-order' && request.method === 'POST') return createOrder(request, env);
      if (p === '/api/pay/confirm' && request.method === 'POST') return confirmPay(request, env);
      if (p === '/api/pay/admin/orders') return adminOrders(request, env);
      return json({ error: 'not found' }, 404);
    }
    // 그 외 모든 요청 → 정적 자산(사이트)
    return env.ASSETS.fetch(request);
  }
};
