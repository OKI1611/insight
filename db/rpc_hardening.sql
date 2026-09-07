-- ============================================================
-- 익명 호출 가능 함수(RPC) 악용 차단 (2026-09-07)
-- 실행 방법: Supabase 대시보드 → SQL Editor → 전체 붙여넣고 Run
-- ============================================================
-- [배경 — 2026-09-07 점검에서 확인된 문제]
--   ① apply_founding() 이 anon 에 열려 있어, 로그인하지 않은 사람이
--      **남의 이메일로 창립멤버 신청서를 덮어쓸 수** 있었다.
--      (이름·연락처·출석교회·기도제목이 비어 있던 칸을 임의 값으로 채울 수 있었다)
--      또 가짜 이메일로 무제한 신청이 가능해 창립 번호가 오염될 수 있었다.
--   ② submit_tester_gift() 가 anon 에 열려 있어, 테스터의 Gmail 만 알면
--      **선물 배송지를 남의 주소로 바꿔치기** 할 수 있었다.
--   ③ founding_members 표에 `for insert with check (true)` 정책이 있어
--      함수를 거치지 않고 표에 직접 신청서를 꽂아 넣을 수 있었다.
--
-- [설계 원칙]
--   비로그인 신청 자체는 막지 않는다(그게 이 사이트의 유입 경로다).
--   대신 **남의 기록을 건드리는 것**과 **표 직접 조작**만 차단한다.
--   혜택 예약(founding_benefits)은 그대로 둔다 — claim_founding() 이
--   로그인 JWT 이메일로만 수령을 허용하므로, 예약만으로는 아무 이득이 없다.
-- ============================================================

-- ────────────────────────────────────────────────────────────
-- 1) apply_founding — 남의 신청서 덮어쓰기 차단
-- ────────────────────────────────────────────────────────────
--  · 새 이메일        → 그대로 접수(비로그인 허용, 기존 유입 경로 유지)
--  · 이미 있는 이메일  → 본인(로그인 이메일 일치) 또는 관리자만 수정 가능.
--                       그 외에는 **아무것도 바꾸지 않고** 접수된 것처럼 응답한다
--                       (duplicate=true. 화면 흐름을 깨지 않으면서 변조는 막는다)
--  · 이용권 즉시 활성화 → 로그인 이메일이 신청 이메일과 같을 때만.
--                       (카카오 등 이메일이 없는 계정은 예외적으로 허용)
create or replace function apply_founding(
  p_name text, p_email text,
  p_phone text default null, p_region text default null, p_church text default null,
  p_faith_years text default null, p_motivation text default null,
  p_ideal_church text default null, p_ideal_pastor text default null,
  p_prayer text default null, p_promise boolean default false,
  p_months int default 12
) returns jsonb language plpgsql security definer as $$
declare
  em text; uid uuid; no int; exp timestamptz; activated boolean := false;
  nm text; caller_em text; is_owner boolean; existed boolean; dup boolean := false;
begin
  em := lower(trim(coalesce(p_email,'')));
  if em = '' or position('@' in em) = 0 or length(em) > 190 then
    return jsonb_build_object('ok', false, 'error', 'NO_EMAIL');
  end if;

  nm := nullif(trim(coalesce(p_name,'')), '');
  -- 이름 없는 자동 제출(스팸) 차단 — 화면 폼은 이름을 필수로 받는다
  if nm is null or length(nm) > 80 then
    return jsonb_build_object('ok', false, 'error', 'NO_NAME');
  end if;

  uid       := auth.uid();
  caller_em := lower(trim(coalesce(auth.jwt() ->> 'email', '')));
  existed   := exists (select 1 from public.founding_members where lower(trim(email)) = em);

  -- 본인 확인: 로그인 이메일이 신청 이메일과 같거나, 관리자
  is_owner := (uid is not null and caller_em <> '' and caller_em = em) or public.is_admin();

  if existed then
    if is_owner then
      -- 본인(또는 관리자)만 빈 칸을 채워 넣는다
      update public.founding_members set
        name         = coalesce(nm,                                             name),
        phone        = coalesce(nullif(trim(coalesce(p_phone,'')),''),          phone),
        region       = coalesce(nullif(trim(coalesce(p_region,'')),''),         region),
        church       = coalesce(nullif(trim(coalesce(p_church,'')),''),         church),
        faith_years  = coalesce(nullif(trim(coalesce(p_faith_years,'')),''),    faith_years),
        motivation   = coalesce(nullif(trim(coalesce(p_motivation,'')),''),     motivation),
        ideal_church = coalesce(nullif(trim(coalesce(p_ideal_church,'')),''),   ideal_church),
        ideal_pastor = coalesce(nullif(trim(coalesce(p_ideal_pastor,'')),''),   ideal_pastor),
        prayer       = coalesce(nullif(trim(coalesce(p_prayer,'')),''),         prayer),
        promise      = coalesce(p_promise, promise)
       where lower(trim(email)) = em;
    else
      -- ★남의 기록은 절대 건드리지 않는다. 화면에는 정상 접수처럼 보이게 한다.
      dup := true;
    end if;
  else
    insert into public.founding_members(email, name, member_no, phone, region, church,
                                        faith_years, motivation, ideal_church, ideal_pastor, prayer, promise)
    values (em, nm, (select coalesce(max(member_no),0) + 1 from public.founding_members),
            nullif(trim(coalesce(p_phone,'')),''),  nullif(trim(coalesce(p_region,'')),''),
            nullif(trim(coalesce(p_church,'')),''), nullif(trim(coalesce(p_faith_years,'')),''),
            nullif(trim(coalesce(p_motivation,'')),''),   nullif(trim(coalesce(p_ideal_church,'')),''),
            nullif(trim(coalesce(p_ideal_pastor,'')),''), nullif(trim(coalesce(p_prayer,'')),''),
            coalesce(p_promise, false));
  end if;

  select member_no into no from public.founding_members where lower(trim(email)) = em;
  exp := now() + (greatest(coalesce(p_months, 12), 1) || ' months')::interval;

  -- 혜택 예약은 그대로 — 수령(claim_founding)은 로그인 JWT 이메일로만 되므로 안전하다
  insert into public.founding_benefits(email, expires_at, granted_by, note)
  values (em, exp, 'apply', '창립 멤버 신청 — 1년 무료')
  on conflict (email) do update
    set expires_at = greatest(public.founding_benefits.expires_at, excluded.expires_at);

  -- ★즉시 활성화는 '본인 이메일로 신청한 로그인 사용자'에게만.
  --   (이메일이 없는 소셜 계정은 검증할 방법이 없어 예외적으로 허용)
  if uid is not null and (caller_em = em or caller_em = '') then
    insert into public.member_access(user_id, email, kind, started_at, expires_at, updated_at)
    values (uid, em, 'founding', now(), exp, now())
    on conflict (user_id) do update
      set kind       = 'founding',
          email      = coalesce(public.member_access.email, excluded.email),
          expires_at = greatest(public.member_access.expires_at, excluded.expires_at),
          updated_at = now();
    update public.founding_benefits set claimed_at = now() where email = em;
    activated := true;
  end if;

  return jsonb_build_object('ok', true, 'member_no', no, 'activated', activated,
                            'duplicate', dup, 'expires_at', exp);
end; $$;

-- ────────────────────────────────────────────────────────────
-- 2) submit_tester_gift — 배송지 바꿔치기 차단
-- ────────────────────────────────────────────────────────────
--  한 번 제출된 배송지는 다시 덮어쓸 수 없다(관리자 제외).
--  본인이 주소를 잘못 적었다면 관리자가 reset_tester_gift() 로 다시 열어 준다.
create or replace function public.submit_tester_gift(
  p_gmail   text,
  p_name    text,
  p_phone   text,
  p_address text,
  p_book    text,
  p_memo    text default null
) returns void
language plpgsql
security definer
set search_path = public
as $$
declare
  v_id bigint;
  v_done timestamptz;
begin
  select id, gift_submitted_at into v_id, v_done
    from public.app_testers
   where lower(gmail) = lower(btrim(p_gmail))
   limit 1;

  if v_id is null then
    raise exception 'not found: 신청 내역을 찾을 수 없습니다';
  end if;

  -- ★이미 제출된 배송지는 잠근다 — Gmail 만 알면 남의 선물을 가로챌 수 있었다
  if v_done is not null and not public.is_admin() then
    raise exception '이미 배송지가 제출되었습니다. 변경이 필요하시면 contact@biblynote.com 으로 알려 주세요.';
  end if;

  update public.app_testers
     set ship_name         = btrim(p_name),
         ship_phone        = btrim(p_phone),
         ship_address      = btrim(p_address),
         gift_book         = p_book,
         gift_memo         = p_memo,
         gift_submitted_at = now()
   where id = v_id;
end;
$$;

-- 관리자가 배송지 재입력을 열어 주는 함수 (정당한 변경 요청 대응용)
create or replace function public.reset_tester_gift(p_gmail text)
returns text language plpgsql security definer set search_path = public as $$
begin
  if not public.is_admin() then
    raise exception '관리자만 사용할 수 있습니다';
  end if;
  update public.app_testers
     set gift_submitted_at = null
   where lower(gmail) = lower(btrim(p_gmail));
  if not found then return 'NOT_FOUND'; end if;
  return 'OK';
end; $$;

revoke execute on function public.reset_tester_gift(text) from anon;
grant  execute on function public.reset_tester_gift(text) to authenticated;

-- ────────────────────────────────────────────────────────────
-- 3) founding_members 표 직접 삽입(우회 경로) 차단
-- ────────────────────────────────────────────────────────────
--  신청은 apply_founding()(security definer)이 처리하므로 RLS 를 타지 않는다.
--  따라서 표에 대한 익명 INSERT 정책은 필요 없고, 스팸 우회로로만 쓰인다.
do $$
declare r record;
begin
  for r in
    select policyname from pg_policies
     where schemaname='public' and tablename='founding_members' and cmd='INSERT'
  loop
    execute format('drop policy if exists %I on public.founding_members', r.policyname);
    raise notice '회수한 INSERT 정책: %', r.policyname;
  end loop;
end $$;

-- 관리자만 표에 직접 넣을 수 있게 남겨 둔다(수동 보정용)
create policy "founding insert admin only" on public.founding_members
  for insert to authenticated with check ( public.is_admin() );

-- ────────────────────────────────────────────────────────────
-- 4) 실행 권한 재확인
-- ────────────────────────────────────────────────────────────
grant execute on function
  apply_founding(text,text,text,text,text,text,text,text,text,text,boolean,int)
to anon, authenticated;

grant execute on function
  public.submit_tester_gift(text,text,text,text,text,text)
to anon, authenticated;

-- ============================================================
-- 실행 후 확인
--   -- ① 남의 이메일로 덮어쓰기 시도 → duplicate:true 가 나오고 기록은 그대로여야 정상
--   --    (익명 키로) select apply_founding('아무개','이미있는주소@example.com');
--   -- ② 이미 배송지를 낸 Gmail 로 재제출 → '이미 배송지가 제출되었습니다' 예외가 나야 정상
--   -- ③ 익명 키로 founding_members 직접 insert → 권한 오류가 나야 정상
-- ============================================================

-- ※ 남은 과제: 자동 가입 스팸을 근본적으로 막으려면 Cloudflare Turnstile 같은
--    캡차를 신청 폼에 붙이는 것이 정석이다. 위 조치는 '남의 기록 변조'와
--    '표 직접 조작'을 막을 뿐, 가짜 이메일로 새 신청서를 만드는 것까지는 막지 못한다.
