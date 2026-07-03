// 결제 승인 — 토스페이먼츠 최종 승인 후, 대기주문과 금액을 대조하고 이용권/수강권을 부여한다.
// 라우트: POST /api/pay/confirm  body: { paymentKey, orderId, amount }
// 필수 환경변수: SUPABASE_SERVICE_KEY (필수), TOSS_SECRET_KEY (없으면 토스 문서 테스트키 사용)
const SUPABASE_URL = 'https://bmxkndkwefdgsomlznoo.supabase.co';
const TOSS_TEST_SECRET = 'test_sk_zXLkKEypNArWmo50nX3lmeaxYG5R'; // 토스 공식 문서 테스트 시크릿키(실결제 전용 아님)

function json(obj, status = 200) {
  return new Response(JSON.stringify(obj), { status, headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' } });
}
function sbHeaders(env) {
  return { apikey: env.SUPABASE_SERVICE_KEY, Authorization: 'Bearer ' + env.SUPABASE_SERVICE_KEY, 'Content-Type': 'application/json' };
}
async function upsert(env, table, row, onConflict) {
  try {
    const r = await fetch(SUPABASE_URL + '/rest/v1/' + table + '?on_conflict=' + onConflict, {
      method: 'POST',
      headers: { ...sbHeaders(env), Prefer: 'resolution=merge-duplicates,return=minimal' },
      body: JSON.stringify(row)
    });
    return r.ok;
  } catch (e) { return false; }
}
async function grant(env, order) {
  const now = new Date();
  for (const it of (order.items || [])) {
    if (it.kind === 'pass') {
      const e = new Date(now);
      if (it.itemId === 'pass-life') e.setFullYear(e.getFullYear() + 100); else e.setFullYear(e.getFullYear() + 1);
      await upsert(env, 'pass_members', { email: order.email, expires_at: e.toISOString() }, 'email');
    } else if (it.kind === 'book') {
      const e = new Date(now); e.setFullYear(e.getFullYear() + 100); // 개별 책자 = 영구 소장
      await upsert(env, 'book_access', { email: order.email, track: it.itemId, expires_at: e.toISOString() }, 'email,track');
    } else if (it.kind === 'cert') {
      const e = new Date(now); e.setMonth(e.getMonth() + 18); // 인증과정 수강기간 18개월
      if (order.user_id) await upsert(env, 'cert_access', { user_id: order.user_id, tier: it.tier || 1, expires_at: e.toISOString() }, 'user_id');
    }
  }
}

export async function onRequestOptions() {
  return new Response(null, { headers: {
    'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Methods': 'POST,OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type'
  }});
}

export async function onRequestPost({ request, env }) {
  let b;
  try { b = await request.json(); } catch (e) { return json({ error: 'bad json' }, 400); }
  const { paymentKey, orderId, amount } = b || {};
  if (!paymentKey || !orderId || amount == null) return json({ error: '필수 파라미터 누락' }, 400);
  if (!env.SUPABASE_SERVICE_KEY) return json({ error: 'SUPABASE_SERVICE_KEY 환경변수가 설정되지 않았습니다' }, 500);

  // 1) 대기주문 조회
  const oR = await fetch(SUPABASE_URL + '/rest/v1/orders?order_id=eq.' + encodeURIComponent(orderId) + '&select=*', { headers: sbHeaders(env) });
  const os = await oR.json().catch(() => []);
  const order = Array.isArray(os) ? os[0] : null;
  if (!order) return json({ error: '주문을 찾을 수 없습니다' }, 404);
  if (order.status === 'paid') return json({ ok: true, already: true, amount: order.amount, items: order.items });
  if (order.status !== 'pending') return json({ error: '결제할 수 없는 주문 상태입니다' }, 400);
  if (Number(order.amount) !== Number(amount)) return json({ error: '결제 금액이 주문 금액과 일치하지 않습니다' }, 400);

  // 2) 토스페이먼츠 최종 승인
  const secret = env.TOSS_SECRET_KEY || TOSS_TEST_SECRET;
  let toss;
  try {
    const tR = await fetch('https://api.tosspayments.com/v1/payments/confirm', {
      method: 'POST',
      headers: { Authorization: 'Basic ' + btoa(secret + ':'), 'Content-Type': 'application/json' },
      body: JSON.stringify({ paymentKey, orderId, amount })
    });
    toss = await tR.json();
    if (!tR.ok || toss.status !== 'DONE') {
      await fetch(SUPABASE_URL + '/rest/v1/orders?order_id=eq.' + encodeURIComponent(orderId), {
        method: 'PATCH', headers: { ...sbHeaders(env), Prefer: 'return=minimal' }, body: JSON.stringify({ status: 'failed' })
      });
      return json({ error: (toss && toss.message) || '결제 승인에 실패했습니다', code: toss && toss.code }, 402);
    }
  } catch (e) {
    return json({ error: '결제 승인 통신 오류: ' + String(e.message || e) }, 502);
  }

  // 3) 이용권/수강권 부여 + 주문 완료 기록
  await grant(env, order);
  await fetch(SUPABASE_URL + '/rest/v1/orders?order_id=eq.' + encodeURIComponent(orderId), {
    method: 'PATCH', headers: { ...sbHeaders(env), Prefer: 'return=minimal' },
    body: JSON.stringify({ status: 'paid', payment_key: paymentKey, paid_at: new Date().toISOString() })
  });

  return json({
    ok: true,
    amount: order.amount,
    method: (toss && toss.method) || '카드',
    receipt: (toss && toss.receipt && toss.receipt.url) || null,
    items: order.items
  });
}
