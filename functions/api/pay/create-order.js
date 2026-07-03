// 결제 전(前) — 서버에서 "정품 금액"을 재계산하고 대기(pending) 주문을 만든다.
// 클라이언트가 보낸 금액은 절대 신뢰하지 않는다(위변조 방지). 금액은 오직 여기서 산정한 값만 사용.
// 라우트: POST /api/pay/create-order
const SUPABASE_URL = 'https://bmxkndkwefdgsomlznoo.supabase.co';

function json(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' }
  });
}
async function jget(origin, path) {
  try { const r = await fetch(origin + path); return r.ok ? await r.json() : null; } catch (e) { return null; }
}

export async function onRequestOptions() {
  return new Response(null, { headers: {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'POST,OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type'
  }});
}

export async function onRequestPost({ request, env }) {
  let body;
  try { body = await request.json(); } catch (e) { return json({ error: 'bad json' }, 400); }
  const { items, email, userId } = body || {};
  if (!Array.isArray(items) || !items.length) return json({ error: '주문 항목이 없습니다' }, 400);
  if (!env.SUPABASE_SERVICE_KEY) return json({ error: 'SUPABASE_SERVICE_KEY 환경변수가 설정되지 않았습니다' }, 500);

  const origin = new URL(request.url).origin;
  const prices = (await jget(origin, '/content/booklet-prices.json')) || {};
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
      if (!course) course = (await jget(origin, '/content/course.json')) || { levels: [] };
      const tracks = (course.levels || []).map(l => ({ name: l.name || l.title, lessons: (l.lessons || []).length }));
      const t = tracks.find(x => x.name === id);
      if (!t) return json({ error: '잘못된 책자: ' + id }, 400);
      const ov = overrides[t.name] || {};
      const pages = ov.pages || Math.max(8, Math.round(t.lessons * 2.6) + 3);
      let price = (typeof ov.price === 'number') ? ov.price : tiers[tiers.length - 1][1];
      if (typeof ov.price !== 'number') { for (const [mx, pr] of tiers) { if (pages <= mx) { price = pr; break; } } }
      resolved.push({ kind, itemId: id, name: t.name + ' PDF 교재', amount: Number(price) });
    } else if (kind === 'cert') {
      if (!prog) prog = (await jget(origin, '/content/program.json')) || { ranks: [] };
      const r = (prog.ranks || []).find(x => String(x.rank) === String(id) || String(x.tier) === String(id) || x.name === id);
      if (!r) return json({ error: '잘못된 급수: ' + id }, 400);
      const amt = (it.earlybird && r.earlybird) ? r.earlybird : r.price;
      resolved.push({ kind, itemId: String(r.rank), name: '바이블 인사이트 ' + r.name + ' (' + r.rank + ')', amount: Number(amt), tier: Number(r.tier) || 0 });
    } else {
      return json({ error: '알 수 없는 상품 유형: ' + kind }, 400);
    }
  }

  const amount = resolved.reduce((s, x) => s + (Number(x.amount) || 0), 0);
  if (!(amount > 0)) return json({ error: '결제 금액이 0원입니다' }, 400);
  const first = resolved[0];
  const orderName = resolved.length > 1 ? (first.name + ' 외 ' + (resolved.length - 1) + '건') : first.name;
  const orderId = 'BIBLY-' + Date.now() + '-' + Math.random().toString(36).slice(2, 8);

  const ins = await fetch(SUPABASE_URL + '/rest/v1/orders', {
    method: 'POST',
    headers: {
      apikey: env.SUPABASE_SERVICE_KEY,
      Authorization: 'Bearer ' + env.SUPABASE_SERVICE_KEY,
      'Content-Type': 'application/json',
      Prefer: 'return=minimal'
    },
    body: JSON.stringify({ order_id: orderId, email: email || null, user_id: userId || null, items: resolved, amount, status: 'pending' })
  });
  if (!ins.ok) return json({ error: '주문 생성 실패', detail: (await ins.text()).slice(0, 200) }, 500);

  return json({ orderId, amount, orderName });
}
