// access.js — BIBLY 멤버십 이용권 상태(창립멤버 1년 / 추천가입 3개월)
// 사용: const st = await biblyAccess(sb, user);  / 배너: biblyAccessBanner(st)
(function(){
  // 이용권 상태 조회
  window.biblyAccess = async function(sb, user){
    const none = { full:false, kind:'none', founding:false, expiresAt:null, expired:false, daysLeft:null, paidTier:0 };
    if(!sb || !user) return none;
    let paidTier = 0, acc = null;
    try{ const { data } = await sb.from('cert_access').select('tier').eq('user_id', user.id).maybeSingle(); if(data && data.tier) paidTier = Number(data.tier)||0; }catch(e){}
    try{ const { data } = await sb.from('member_access').select('kind,expires_at,referrer_name').eq('user_id', user.id).maybeSingle(); acc = data || null; }catch(e){}
    const now = Date.now();
    let expired=false, daysLeft=null, expiresAt=null, kind='none', founding=false;
    if(acc){
      kind = acc.kind; founding = (acc.kind === 'founding');
      expiresAt = acc.expires_at;
      const exp = new Date(acc.expires_at).getTime();
      expired = exp < now;
      daysLeft = Math.ceil((exp - now) / 86400000);
    }
    const full = paidTier > 0 || (acc && !expired);   // 유료등급이거나 무료기간 유효 → 전체 자료 이용 가능
    return { full, kind, founding, expiresAt, expired, daysLeft, paidTier };
  };

  // 만료/임박 안내 배너 (없으면 빈 문자열)
  window.biblyAccessBanner = function(st){
    if(!st || st.paidTier > 0 || st.kind === 'none') return '';   // 유료회원·이용권없음(전강의 무료기) → 배너 없음
    const kindLabel = st.founding ? '창립멤버 1년 무료 이용' : '추천 가입 3개월 무료 이용';
    if(!st.expired){
      if(st.daysLeft != null && st.daysLeft <= 21){
        return '<div class="bg-gold/10 border border-gold/30 text-ink/80 rounded-xl px-4 py-2.5 text-sm">⏳ <b>'+kindLabel+'</b> 종료까지 <b class="text-gold">'+st.daysLeft+'일</b> 남았어요. 기간 안에 마음껏 누리세요!</div>';
      }
      return '';
    }
    // 만료 → 결제 안내 (창립멤버는 20% 할인)
    var disc = st.founding ? ' <b class="text-gold">창립멤버는 정가의 80%(20% 할인)</b>로 이어가실 수 있어요.' : '';
    return '<div class="bg-ink text-paper rounded-2xl px-5 py-4 flex flex-col sm:flex-row sm:items-center gap-3">'
      + '<div class="flex-1 text-sm leading-relaxed">🔔 <b>'+kindLabel.replace(' 무료 이용','')+' 기간이 종료</b>되었어요. 유료 자료(인증과정 시험·교재 PDF)를 계속 이용하시려면 결제가 필요합니다.'+disc+'</div>'
      + '<a href="academy.html#packages" class="shrink-0 bg-gold text-white font-bold text-sm px-5 py-2.5 rounded-full hover:opacity-90 transition text-center">결제하고 계속 이용 →</a>'
      + '</div>';
  };

  // 이용권 부여(창립멤버 1년 / 추천가입 3개월). months=12 또는 3.
  window.biblyGrantAccess = async function(sb, user, kind, months, referrer){
    if(!sb || !user) return false;
    const start = new Date();
    const exp = new Date(start); exp.setMonth(exp.getMonth() + months);
    const row = { user_id:user.id, email:user.email||null, kind:kind,
      started_at:start.toISOString(), expires_at:exp.toISOString(), updated_at:start.toISOString() };
    if(referrer){ row.referrer_email = (referrer.email||'').trim()||null; row.referrer_name = (referrer.name||'').trim()||null; }
    try{
      // 기존 이용권이 founding이면 referral로 덮어쓰지 않음(상위 유지)
      const { data:cur } = await sb.from('member_access').select('kind,expires_at').eq('user_id', user.id).maybeSingle();
      if(cur && cur.kind === 'founding' && kind === 'referral') return true;
      const { error } = await sb.from('member_access').upsert(row, { onConflict:'user_id' });
      return !error;
    }catch(e){ return false; }
  };
})();
