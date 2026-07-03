// 결제 함수 배포·환경변수 진단용. 브라우저로 /api/pay/ping 을 열면 상태가 JSON으로 보인다.
// (비밀키 값은 노출하지 않고, 설정 여부만 true/false로 표시)
export async function onRequestGet({ env }) {
  return new Response(JSON.stringify({
    ok: true,
    functions: 'deployed',
    hasServiceKey: !!env.SUPABASE_SERVICE_KEY,   // Supabase 서비스키 설정 여부
    hasTossSecret: !!env.TOSS_SECRET_KEY,        // 토스 시크릿키 설정 여부(테스트는 없어도 됨)
    time: new Date().toISOString()
  }, null, 2), { headers: { 'Content-Type': 'application/json; charset=utf-8', 'Access-Control-Allow-Origin': '*' } });
}
