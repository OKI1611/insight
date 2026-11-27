// worker/notify.js — 수강생 질문방 새 질문 → 강사 카카오톡 「나와의 채팅」 알림 (카카오 「나에게 보내기」 API, 무료)
//   준비(한 번): ① db/kakao_notify.sql 실행  ② 카카오 개발자 앱에 '카카오톡 메시지' 동의항목·Redirect URI 등록
//                ③ Cloudflare 시크릿 KAKAO_REST_KEY(REST API 키) [+ 클라이언트 시크릿을 켰다면 KAKAO_CLIENT_SECRET]
//                ④ 관리자 페이지 › 커뮤니티 관리 › 「카카오톡 연결하기」 (관리자 로그인 + 강사 카카오 계정 동의)
//   흐름: 질문 등록 직후 화면이 POST /api/notify/qna {id} → 서버가 글을 직접 확인(질문방·15분 이내·처음)해 발송.
//         놓친 글은 5분마다 크론이 최근 2시간분을 다시 훑는다. 같은 글은 notify_log 로 한 번만 보낸다.
//   토큰은 Supabase notify_kv 표(서비스 키로만 접근)에 둔다 — 리프레시 토큰이 갱신되면 새 값으로 바꿔 저장.
const SUPABASE_URL = 'https://bmxkndkwefdgsomlznoo.supabase.co';
const KAKAO_AUTH = 'https://kauth.kakao.com', KAKAO_API = 'https://kapi.kakao.com';

function json(o, s = 200) {
  return new Response(JSON.stringify(o), { status: s, headers: { 'Content-Type': 'application/json; charset=utf-8', 'Access-Control-Allow-Origin': '*' } });
}
function sbH(env) { return { apikey: env.SUPABASE_SERVICE_KEY, Authorization: 'Bearer ' + env.SUPABASE_SERVICE_KEY, 'Content-Type': 'application/json' }; }
function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])); }

export async function kvGet(env, k) {
  try {
    const r = await fetch(SUPABASE_URL + '/rest/v1/notify_kv?select=v&k=eq.' + encodeURIComponent(k), { headers: sbH(env) });
    if (!r.ok) return null; const a = await r.json(); return a && a[0] ? a[0].v : null;
  } catch (e) { return null; }
}
export async function kvSet(env, k, v) {
  try {
    const r = await fetch(SUPABASE_URL + '/rest/v1/notify_kv?on_conflict=k', { method: 'POST', headers: { ...sbH(env), Prefer: 'resolution=merge-duplicates,return=minimal' }, body: JSON.stringify({ k, v: String(v), updated_at: new Date().toISOString() }) });
    return r.ok;
  } catch (e) { return false; }
}
async function hmacHex(key, msg) {
  const k = await crypto.subtle.importKey('raw', new TextEncoder().encode(key), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  const sig = await crypto.subtle.sign('HMAC', k, new TextEncoder().encode(msg));
  return [...new Uint8Array(sig)].map(b => b.toString(16).padStart(2, '0')).join('');
}
const redirectUri = origin => origin + '/api/notify/kakao/callback';

async function kakaoToken(env, params) {
  const body = new URLSearchParams({ client_id: env.KAKAO_REST_KEY, ...params });
  if (env.KAKAO_CLIENT_SECRET) body.set('client_secret', env.KAKAO_CLIENT_SECRET);
  const r = await fetch(KAKAO_AUTH + '/oauth/token', { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8' }, body });
  const d = await r.json().catch(() => ({}));
  if (!r.ok || !d.access_token) throw new Error('카카오 토큰 실패: ' + (d.error_description || d.error || r.status));
  return d;
}
async function saveTokens(env, d) {
  await kvSet(env, 'kakao_access', d.access_token);
  await kvSet(env, 'kakao_access_exp', Date.now() + (Number(d.expires_in) || 3600) * 1000);
  if (d.refresh_token) await kvSet(env, 'kakao_refresh', d.refresh_token);   // 만료 1달 전부터는 새 리프레시 토큰이 함께 온다
}
async function accessToken(env) {
  const tok = await kvGet(env, 'kakao_access'), exp = Number(await kvGet(env, 'kakao_access_exp')) || 0;
  if (tok && exp - 120000 > Date.now()) return tok;
  const rt = await kvGet(env, 'kakao_refresh');
  if (!rt) throw new Error('카카오톡이 아직 연결되지 않았습니다');
  const d = await kakaoToken(env, { grant_type: 'refresh_token', refresh_token: rt });
  await saveTokens(env, d);
  return d.access_token;
}
async function memo(env, text, link, button) {
  const at = await accessToken(env);
  const tpl = { object_type: 'text', text: String(text).slice(0, 200), link: { web_url: link, mobile_web_url: link }, button_title: button || '자세히 보기' };
  const r = await fetch(KAKAO_API + '/v2/api/talk/memo/default/send', {
    method: 'POST', headers: { Authorization: 'Bearer ' + at, 'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8' },
    body: new URLSearchParams({ template_object: JSON.stringify(tpl) })
  });
  if (!r.ok) throw new Error('카카오톡 발송 실패: ' + (await r.text()).slice(0, 160));
  return true;
}
function plain(h) {
  return String(h || '').replace(/<br\s*\/?>/gi, '\n').replace(/<\/(p|div|li)>/gi, '\n').replace(/<[^>]+>/g, '')
    .replace(/&nbsp;/g, ' ').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&amp;/g, '&')
    .replace(/\n{3,}/g, '\n\n').trim();
}

// 글 하나를 처음일 때만 보낸다
async function sendForPost(env, post, origin) {
  if (!post || post.board !== 'qna') return 'skip';
  if (/^\s*\[공지\]/.test(plain(post.content))) return 'skip';   // 강사가 올린 공지는 알리지 않는다
  // 기록부터 넣는다(동시에 두 번 불려도 한 번만) — 이미 있으면 0행
  const ins = await fetch(SUPABASE_URL + '/rest/v1/notify_log?on_conflict=post_id', {
    method: 'POST', headers: { ...sbH(env), Prefer: 'resolution=ignore-duplicates,return=representation' },
    body: JSON.stringify({ post_id: post.id, channel: 'kakao' })
  });
  if (!ins.ok) return 'log-fail';
  const rows = await ins.json().catch(() => []);
  if (!rows.length) return 'dup';
  const body = plain(post.content);
  const text = '📮 질문방 새 질문\n' + (post.author_name || '회원') + ' 님\n\n' + body.slice(0, 150) + (body.length > 150 ? '…' : '');
  try { await memo(env, text, origin + '/qna-board?post=' + encodeURIComponent(post.id), '질문 보러 가기'); return 'sent'; }
  catch (e) {   // 실패하면 기록을 지워 다음 크론이 다시 시도하게
    await fetch(SUPABASE_URL + '/rest/v1/notify_log?post_id=eq.' + encodeURIComponent(post.id), { method: 'DELETE', headers: sbH(env) }).catch(() => {});
    return 'error: ' + e.message;
  }
}

// 질문 등록 직후 화면이 부른다(누구나 부를 수 있으나 서버가 글을 직접 확인하므로 안전)
export async function notifyQna(request, env) {
  if (!env.SUPABASE_SERVICE_KEY || !env.KAKAO_REST_KEY) return json({ ok: false, reason: 'not-configured' });
  let id = ''; try { id = String((await request.json()).id || ''); } catch (e) {}
  if (!/^[0-9a-f-]{36}$/i.test(id)) return json({ ok: false, reason: 'bad-id' }, 400);
  const r = await fetch(SUPABASE_URL + '/rest/v1/community_posts?select=id,board,author_name,content,created_at&id=eq.' + id, { headers: sbH(env) });
  const post = r.ok ? (await r.json())[0] : null;
  if (!post) return json({ ok: false, reason: 'not-found' }, 404);
  if (Date.now() - new Date(post.created_at).getTime() > 15 * 60000) return json({ ok: false, reason: 'old' });   // 옛 글로 알림 남발 방지
  const res = await sendForPost(env, post, new URL(request.url).origin);
  return json({ ok: res === 'sent' || res === 'dup', result: res.startsWith('error') ? 'error' : res });
}

// 크론: 최근 2시간 질문 중 아직 안 보낸 것
export async function sweepQna(env) {
  if (!env.SUPABASE_SERVICE_KEY || !env.KAKAO_REST_KEY) return;
  if (!(await kvGet(env, 'kakao_refresh'))) return;
  const since = new Date(Date.now() - 2 * 3600000).toISOString();
  const r = await fetch(SUPABASE_URL + '/rest/v1/community_posts?select=id,board,author_name,content,created_at&board=eq.qna&created_at=gte.' + since + '&order=created_at.asc&limit=10', { headers: sbH(env) });
  if (!r.ok) return;
  for (const p of await r.json()) await sendForPost(env, p, 'https://www.biblynote.com');
}

// 관리자: 연결 상태 · 연결 시작 · 테스트 (verifyAdmin 은 index.js 의 것을 넘겨받는다)
export async function kakaoAdmin(request, env, action, verifyAdmin) {
  if (!(await verifyAdmin(request))) return json({ error: '관리자 인증 실패' }, 403);
  const origin = new URL(request.url).origin;
  if (action === 'status') {
    const hasTable = env.SUPABASE_SERVICE_KEY ? (await fetch(SUPABASE_URL + '/rest/v1/notify_kv?select=k&limit=1', { headers: sbH(env) })).ok : false;
    return json({
      ok: true, hasKey: !!env.KAKAO_REST_KEY, hasTable,
      connected: !!(hasTable && await kvGet(env, 'kakao_refresh')),
      connectedAt: hasTable ? await kvGet(env, 'kakao_connected_at') : null,
      redirectUri: redirectUri(origin)
    });
  }
  if (!env.KAKAO_REST_KEY) return json({ error: 'Cloudflare 에 KAKAO_REST_KEY 시크릿이 없습니다' }, 400);
  if (action === 'start') {
    const ts = String(Date.now()), state = ts + '.' + (await hmacHex(env.SUPABASE_SERVICE_KEY, 'kakao:' + ts)).slice(0, 32);
    const u = new URL(KAKAO_AUTH + '/oauth/authorize');
    u.searchParams.set('client_id', env.KAKAO_REST_KEY); u.searchParams.set('redirect_uri', redirectUri(origin));
    u.searchParams.set('response_type', 'code'); u.searchParams.set('scope', 'talk_message'); u.searchParams.set('state', state);
    return json({ ok: true, url: u.toString() });
  }
  if (action === 'test') {
    try { await memo(env, '✅ 바이블 인사이트 질문방 알림 테스트입니다.\n새 질문이 올라오면 이렇게 알려 드려요.', origin + '/qna-board', '질문방 열기'); return json({ ok: true }); }
    catch (e) { return json({ ok: false, error: e.message }); }
  }
  return json({ error: 'not found' }, 404);
}

function page(title, msg, ok) {
  return new Response('<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>' + esc(title) + '</title>'
    + '<body style="font-family:Pretendard,system-ui,sans-serif;max-width:480px;margin:60px auto;padding:0 20px;text-align:center;color:#111827">'
    + '<p style="font-size:44px;margin:0">' + (ok ? '✅' : '⚠️') + '</p><h1 style="font-size:21px">' + esc(title) + '</h1>'
    + '<p style="font-size:16px;line-height:1.6;color:#4b5563">' + esc(msg) + '</p>'
    + '<p><a href="/admin" style="display:inline-block;margin-top:14px;padding:12px 22px;border-radius:12px;background:#0b7d53;color:#fff;font-weight:800;text-decoration:none">관리자 페이지로</a></p></body>',
    { headers: { 'Content-Type': 'text/html; charset=utf-8' } });
}
export async function kakaoCallback(request, env, url) {
  if (url.searchParams.get('error')) return page('연결이 취소됐어요', '카카오 동의 화면에서 취소했거나 오류가 났습니다: ' + (url.searchParams.get('error_description') || ''), false);
  const code = url.searchParams.get('code'), state = url.searchParams.get('state') || '';
  const [ts, sig] = state.split('.');
  const good = !!(ts && sig && env.SUPABASE_SERVICE_KEY && Date.now() - Number(ts) < 15 * 60000
    && (await hmacHex(env.SUPABASE_SERVICE_KEY, 'kakao:' + ts)).slice(0, 32) === sig);
  if (!code || !good) return page('연결할 수 없어요', '관리자 페이지에서 「카카오톡 연결하기」를 다시 눌러 주세요(15분 동안만 유효합니다).', false);
  try {
    const d = await kakaoToken(env, { grant_type: 'authorization_code', redirect_uri: redirectUri(url.origin), code });
    if (d.scope && !String(d.scope).includes('talk_message')) return page('메시지 권한이 빠졌어요', '카카오 동의 화면에서 「카카오톡 메시지 전송」에 동의해야 알림을 보낼 수 있습니다.', false);
    await saveTokens(env, d);
    await kvSet(env, 'kakao_connected_at', new Date().toISOString());
    try { await memo(env, '✅ 카카오톡 연결 완료!\n이제 수강생 질문방에 새 질문이 올라오면 이 채팅으로 알려 드려요.', url.origin + '/qna-board', '질문방 열기'); } catch (e) {}
    return page('카카오톡 연결 완료', '카카오톡 「나와의 채팅」에 확인 메시지를 보냈습니다. 이제 새 질문이 올라오면 그곳으로 알림이 갑니다.', true);
  } catch (e) { return page('연결에 실패했어요', e.message, false); }
}
