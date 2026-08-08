-- ============================================================
-- 창립 멤버 신청 처리 — apply_founding()
--
--   founding.html 의 신청 폼이 호출하는 함수입니다.
--   지금은 이 함수가 없어서(PGRST202) 폴백 경로로만 저장되고 있고,
--   그 결과 "비로그인 신청자에게 1년 혜택이 부여되지 않는" 상태입니다.
--
--   하는 일 (한 번의 호출로)
--     1) 신청서를 founding_members 에 저장 (이메일 기준 · 재신청이면 갱신)
--     2) 창립 멤버 번호 발급 (이미 있으면 그대로 유지)
--     3) 로그인 상태면  → 1년(12개월) 창립 혜택 즉시 활성화
--        비로그인 상태면 → 명단에 남겨 두고, 나중에 로그인할 때
--                          access.js 가 부르는 claim_founding() 이 자동 활성화
--     4) { ok, activated, member_no } 반환
--
--   실행 방법: Supabase 대시보드 → SQL Editor → 붙여넣기 → Run
-- ============================================================

create or replace function public.apply_founding(
  p_name          text,
  p_email         text,
  p_phone         text    default null,
  p_region        text    default null,
  p_church        text    default null,
  p_faith_years   text    default null,
  p_motivation    text    default null,
  p_ideal_church  text    default null,
  p_ideal_pastor  text    default null,
  p_prayer        text    default null,
  p_promise       boolean default false
)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
  v_email     text := lower(btrim(coalesce(p_email, '')));
  v_name      text := btrim(coalesce(p_name, ''));
  v_no        integer;
  v_ctid      tid;
  v_exists    boolean := false;
  v_uid       uuid := auth.uid();
  v_activated boolean := false;
  v_cur_kind  text;
  v_cur_exp   timestamptz;
  v_rank      integer;
  v_start     timestamptz := now();
  v_exp       timestamptz := now() + interval '12 months';
begin
  if v_name = '' or v_email = '' then
    return jsonb_build_object('ok', false, 'error', 'NAME_EMAIL_REQUIRED');
  end if;
  if position('@' in v_email) = 0 then
    return jsonb_build_object('ok', false, 'error', 'BAD_EMAIL');
  end if;

  -- 동시에 두 사람이 신청해도 같은 번호가 나가지 않도록 직렬화한다.
  perform pg_advisory_xact_lock(hashtext('founding_members'));

  ----------------------------------------------------------------
  -- 1) 신청서 저장 (이메일이 키 — 이 표에는 id·user_id 컬럼이 없다)
  ----------------------------------------------------------------
  -- 같은 이메일이 실수로 두 번 들어가 있어도 딱 한 행만 골라 잠근다
  -- (여러 행에 같은 번호를 써 넣어 번호가 중복되는 사고를 막는다).
  select ctid, member_no, true
    into v_ctid, v_no, v_exists
    from public.founding_members
   where lower(email) = v_email
   order by member_no nulls last
   limit 1
     for update;

  if v_no is null then
    -- 아직 번호가 없으면(신규 신청, 또는 번호 미부여 행) 다음 번호를 준다.
    select coalesce(max(member_no), 0) + 1 into v_no from public.founding_members;
  end if;

  if coalesce(v_exists, false) then
    -- 재신청 — 새로 적어 주신 값만 덮어쓰고, 빈칸은 기존 내용을 지킨다.
    update public.founding_members set
      name         = v_name,
      phone        = coalesce(nullif(btrim(coalesce(p_phone, '')),         ''), phone),
      region       = coalesce(nullif(btrim(coalesce(p_region, '')),        ''), region),
      church       = coalesce(nullif(btrim(coalesce(p_church, '')),        ''), church),
      faith_years  = coalesce(nullif(btrim(coalesce(p_faith_years, '')),   ''), faith_years),
      motivation   = coalesce(nullif(btrim(coalesce(p_motivation, '')),    ''), motivation),
      ideal_church = coalesce(nullif(btrim(coalesce(p_ideal_church, '')),  ''), ideal_church),
      ideal_pastor = coalesce(nullif(btrim(coalesce(p_ideal_pastor, '')),  ''), ideal_pastor),
      prayer       = coalesce(nullif(btrim(coalesce(p_prayer, '')),        ''), prayer),
      promise      = coalesce(p_promise, promise),
      member_no    = v_no
    where ctid = v_ctid;
  else
    insert into public.founding_members
      (name, email, phone, region, church, faith_years, motivation,
       ideal_church, ideal_pastor, prayer, promise, member_no, joined_at)
    values
      (v_name, v_email,
       nullif(btrim(coalesce(p_phone, '')),        ''),
       nullif(btrim(coalesce(p_region, '')),       ''),
       nullif(btrim(coalesce(p_church, '')),       ''),
       nullif(btrim(coalesce(p_faith_years, '')),  ''),
       nullif(btrim(coalesce(p_motivation, '')),   ''),
       nullif(btrim(coalesce(p_ideal_church, '')), ''),
       nullif(btrim(coalesce(p_ideal_pastor, '')), ''),
       nullif(btrim(coalesce(p_prayer, '')),       ''),
       coalesce(p_promise, false), v_no, now());
  end if;

  ----------------------------------------------------------------
  -- 2) 로그인 상태라면 1년 혜택 즉시 활성화
  --    (혜택은 "적어 낸 이메일"이 아니라 "로그인한 계정"에만 준다 —
  --     남의 이메일을 적어 혜택을 가로채지 못하게)
  ----------------------------------------------------------------
  if v_uid is not null then
    select kind, expires_at into v_cur_kind, v_cur_exp
      from public.member_access where user_id = v_uid;

    v_rank := case v_cur_kind
                when 'trial'    then 1
                when 'referral' then 2
                when 'founding' then 3
                else 9                      -- 모르는 상위 등급은 건드리지 않는다
              end;

    if v_cur_kind is null then
      insert into public.member_access
        (user_id, email, kind, started_at, expires_at, updated_at)
      values
        (v_uid, coalesce(nullif(btrim(coalesce(auth.jwt() ->> 'email', '')), ''), v_email),
         'founding', v_start, v_exp, now());
      v_activated := true;

    elsif v_rank < 3 then
      -- 체험·추천 등급 → 창립으로 승급 (기간이 더 길면 그 기간을 지킨다)
      update public.member_access
         set kind       = 'founding',
             started_at = coalesce(started_at, v_start),
             expires_at = greatest(coalesce(expires_at, v_exp), v_exp),
             updated_at = now()
       where user_id = v_uid;
      v_activated := true;

    elsif v_cur_kind = 'founding' then
      -- 이미 창립 — 남은 기간이 1년보다 짧으면 1년으로 늘려 준다.
      if coalesce(v_cur_exp, v_start) < v_exp then
        update public.member_access
           set expires_at = v_exp, updated_at = now()
         where user_id = v_uid;
      end if;
      v_activated := true;

    else
      v_activated := true;   -- 이미 더 좋은 이용권 보유 — 그대로 둔다
    end if;
  end if;

  return jsonb_build_object('ok', true, 'activated', v_activated, 'member_no', v_no);
end;
$$;

revoke all on function public.apply_founding(
  text, text, text, text, text, text, text, text, text, text, boolean) from public;

grant execute on function public.apply_founding(
  text, text, text, text, text, text, text, text, text, text, boolean) to anon, authenticated;

-- PostgREST 스키마 캐시 즉시 갱신 (안 하면 잠깐 PGRST202 가 더 뜰 수 있음)
notify pgrst, 'reload schema';
