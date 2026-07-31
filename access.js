// access.js — BIBLY 멤버십 이용권 상태(창립멤버 1년 / 추천가입 3개월)
// 사용: const st = await biblyAccess(sb, user);  / 배너: biblyAccessBanner(st)
(function(){
  // 이용권 상태 조회
  window.biblyAccess = async function(sb, user){
    const none = { full:false, allBooks:false, kind:'none', founding:false, expiresAt:null, expired:false, daysLeft:null, paidTier:0, certExpired:false, certExpiresAt:null };
    if(!sb || !user) return none;
    let paidTier = 0, acc = null, certExpired = false, certExpiresAt = null;
    // 인증 수강기간: cert_access.expires_at(만료일)이 지나면 유료 혜택 잠금. (컬럼 없으면 expires_at=undefined → 무기한)
    try{ const { data } = await sb.from('cert_access').select('*').eq('user_id', user.id).maybeSingle();
      if(data && data.tier){
        certExpiresAt = data.expires_at || null;
        const exp = certExpiresAt ? new Date(certExpiresAt).getTime() : null;
        if(exp && exp < Date.now()){ certExpired = true; }   // 수강기간 만료 → 잠금
        else paidTier = Number(data.tier)||0;
      }
    }catch(e){}
    try{ const { data } = await sb.from('member_access').select('kind,expires_at,referrer_name').eq('user_id', user.id).maybeSingle(); acc = data || null; }catch(e){}
    // 로그인 전에 창립 멤버를 신청하신 분 자동 구제 — 예약된 혜택이 있으면 이용권으로 옮긴다.
    // 이용권 행이 아직 없을 때만, 세션당 1회. RPC가 없으면(SQL 미실행) 조용히 지나간다.
    if(!acc){
      try{
        if(!sessionStorage.getItem('_bfclaim')){
          sessionStorage.setItem('_bfclaim','1');
          const { data:cl } = await sb.rpc('claim_founding');
          if(cl === 'OK'){
            const { data } = await sb.from('member_access').select('kind,expires_at,referrer_name').eq('user_id', user.id).maybeSingle();
            acc = data || null;
          }
        }
      }catch(e){}
    }
    const now = Date.now();
    let expired=false, daysLeft=null, expiresAt=null, kind='none', founding=false;
    if(acc){
      kind = acc.kind; founding = (acc.kind === 'founding');
      expiresAt = acc.expires_at;
      const exp = new Date(acc.expires_at).getTime();
      expired = exp < now;
      daysLeft = Math.ceil((exp - now) / 86400000);
    }
    const full = paidTier > 0 || (acc && !expired);   // 유료등급(급수 보유)이거나 무료기간 유효 → 시험 등 유료자료 이용
    const allBooks = paidTier >= 3 || (acc && !expired);  // 3급 이상(tier≥3) 또는 무료기간 → 전 PDF 책자 이용권 포함(5·4급은 별도 구매)
    return { full, allBooks, kind, founding, expiresAt, expired, daysLeft, paidTier, certExpired, certExpiresAt };
  };

  // 이용권 종류 라벨
  window.biblyAccessLabel = function(st){
    if(!st) return '';
    return st.founding ? '창립멤버 1년 무료 이용'
         : st.kind === 'referral' ? '추천 가입 3개월 무료 이용'
         : st.kind === 'trial' ? '신규 가입 5일 무료 체험'
         : '';
  };

  // 만료/임박 안내 배너 (없으면 빈 문자열)
  window.biblyAccessBanner = function(st){
    if(!st) return '';
    if(st.certExpired && st.paidTier === 0){   // 인증과정 수강기간(18개월) 만료 → 재등록 안내
      return '<div class="bg-ink text-paper rounded-2xl px-5 py-4 flex flex-col sm:flex-row sm:items-center gap-3">'
        + '<div class="flex-1 text-sm leading-relaxed"><b>인증 과정 수강기간(1년 6개월)이 종료</b>되었어요. 시험·1:1 질의응답·교재 등 유료 혜택을 이어가시려면 재등록(연장)이 필요합니다. 이미 취득한 학점·수료는 보존됩니다.</div>'
        + '<a href="academy.html#packages" class="shrink-0 bg-gold text-white font-bold text-sm px-5 py-2.5 rounded-full hover:opacity-90 transition text-center">재등록하고 계속 →</a>'
        + '</div>';
    }
    if(st.paidTier > 0 || st.kind === 'none') return '';   // 유료회원(유효)·이용권없음 → 배너 없음
    const kindLabel = window.biblyAccessLabel(st);
    if(!st.expired){
      if(st.daysLeft != null && st.daysLeft <= 21){
        return '<div class="bg-gold/10 border border-gold/30 text-neutral-900/80 rounded-xl px-4 py-2.5 text-sm">⏳ <b>'+kindLabel+'</b> 종료까지 <b class="text-gold">'+st.daysLeft+'일</b> 남았어요. 기간 안에 마음껏 누리세요!</div>';
      }
      return '';
    }
    // 만료 → 결제 안내 (창립멤버는 20% 할인)
    var disc = st.founding ? ' <b class="text-gold">창립멤버는 정가의 80%(20% 할인)</b>로 이어가실 수 있어요.' : '';
    return '<div class="bg-ink text-paper rounded-2xl px-5 py-4 flex flex-col sm:flex-row sm:items-center gap-3">'
      + '<div class="flex-1 text-sm leading-relaxed"><b>'+kindLabel.replace(' 무료 이용','')+' 기간이 종료</b>되었어요. 유료 자료(인증과정 시험·교재 PDF)를 계속 이용하시려면 결제가 필요합니다.'+disc+'</div>'
      + '<a href="academy.html#packages" class="shrink-0 bg-gold text-white font-bold text-sm px-5 py-2.5 rounded-full hover:opacity-90 transition text-center">결제하고 계속 이용 →</a>'
      + '</div>';
  };

  // 이용권 부여. period = 숫자(개월) 또는 {months:n} / {days:n}.
  //  kind: 'founding'(1년) | 'referral'(3개월) | 'trial'(5일). 하위 등급으로 덮어쓰지 않음.
  window.biblyGrantAccess = async function(sb, user, kind, period, referrer){
    if(!sb || !user) return false;
    const RANK = { trial:1, referral:2, founding:3 };
    const start = new Date();
    const exp = new Date(start);
    if(typeof period === 'number'){ exp.setMonth(exp.getMonth() + period); }
    else if(period && period.days){ exp.setDate(exp.getDate() + period.days); }
    else if(period && period.months){ exp.setMonth(exp.getMonth() + period.months); }
    else { exp.setDate(exp.getDate() + 5); }
    const row = { user_id:user.id, email:user.email||null, kind:kind,
      started_at:start.toISOString(), expires_at:exp.toISOString(), updated_at:start.toISOString() };
    if(referrer){ row.referrer_email = (referrer.email||'').trim()||null; row.referrer_name = (referrer.name||'').trim()||null; }
    try{
      // 기존 이용권이 더 높거나 같은 등급이면 유지(특히 trial 재발급·상위→하위 강등 방지)
      const { data:cur } = await sb.from('member_access').select('kind,expires_at').eq('user_id', user.id).maybeSingle();
      if(cur && (RANK[cur.kind]||0) >= (RANK[kind]||0)) return true;
      const { error } = await sb.from('member_access').upsert(row, { onConflict:'user_id' });
      return !error;
    }catch(e){ return false; }
  };
})();
