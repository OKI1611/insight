-- ============================================================
-- BIBLY 1기 창립 멤버 — "1년간 전 강의·전 책자 무료" 혜택 관리 (1회 실행)
--
-- 왜 필요한가
--   founding.html 은 1년 무료를 약속하지만, 실제 이용권 부여가
--   'Web3Forms 메일 발송 성공 + 로그인 상태' 일 때만 실행돼 대부분 누락됐다.
--   또 member_access 에 관리자 조회 정책이 없어 누가 혜택을 받았는지도 볼 수 없었다.
--
-- 무엇을 하는가
--   1) member_access 백업(최초 1회)
--   2) founding_benefits(약속 대장) 신설 — 아직 가입 전인 이메일도 예약해 둘 수 있다
--   3) 관리자 RPC 4종 — 조회/부여/회수/본인수령
--   4) 이미 창립 번호를 받은 분 전원에게 오늘부터 1년 이용권 부여
--
-- 안전장치
--   · 전체가 하나의 트랜잭션 — 중간에 실패하면 아무것도 적용되지 않는다
--   · 여러 번 실행해도 안전(idempotent). 기존 이용권 기간을 줄이지 않는다(greatest)
--   · 전제: supabase/store_grant.sql 의 _is_store_admin(), db/membership.sql 의 member_access
--
-- Supabase 대시보드 → SQL Editor 에 전체 복사 → Run
-- ============================================================
begin;

-- ── 0) 백업 (최초 1회만 — 재실행이 스냅샷을 덮어쓰지 않게) ──
do $$ begin
  if to_regclass('public._bak_member_access') is null
     and to_regclass('public.member_access') is not null then
    execute 'create table public._bak_member_access as select * from public.member_access';
  end if;
end $$;

-- ── 1) 관리자 판별 (store_grant.sql 과 동일 정의 — 단독 실행도 되게) ──
create or replace function _is_store_admin() returns boolean
language sql stable as $$
  select coalesce(auth.jwt() ->> 'email','') = 'josephoh1611@gmail.com';
$$;

-- ── 2) 약속 대장 ──
-- member_access 는 user_id 가 auth.users 참조라 '로그인 전 이메일'에는 행을 만들 수 없다.
-- 그래서 이메일을 키로 하는 예약 표를 둔다. 로그인하는 순간 claim_founding() 이 옮겨 준다.
create table if not exists public.founding_benefits (
  email       text primary key,               -- 항상 소문자로 저장
  kind        text not null default 'founding',
  started_at  timestamptz not null default now(),
  expires_at  timestamptz not null,
  granted_by  text,                           -- 'admin' | 'apply' | 'migration'
  note        text,
  claimed_at  timestamptz,                    -- member_access 로 실제 활성화된 시각
  created_at  timestamptz not null default now()
);
alter table public.founding_benefits enable row level security;
-- 정책을 두지 않는다 = anon/authenticated 직접 접근 차단. 접근은 아래 RPC(security definer)로만.

-- 명단 표의 name 이 NOT NULL 이면 자동 등록이 막히므로 완화(이미 nullable 이면 무해)
alter table public.founding_members alter column name drop not null;

-- ── 3) 관리자: 명단 + 이용권 + 유료 보유 여부를 한 번에 ──
-- founding_members 의 모든 컬럼을 그대로 싣기 위해 jsonb 배열로 돌려준다.
-- (컬럼을 하나씩 나열하면 나중에 늘어난 항목이 조용히 빠진다)
create or replace function list_founding_full()
returns jsonb language sql security definer as $$
  select coalesce(jsonb_agg(x order by (x->>'member_no')::int nulls last), '[]'::jsonb) from (
    select to_jsonb(f) || jsonb_build_object(
             'benefit_expires_at', b.expires_at,          -- 예약 대장(미가입자 포함)
             'access_kind',        m.kind,                -- 실제 이용권 종류
             'access_expires_at',  m.expires_at,
             'access_days_left',   case when m.expires_at is null then null
                                        else ceil(extract(epoch from (m.expires_at - now())) / 86400)::int end,
             'paid_tier',          coalesce(c.tier, 0),   -- 유료 인증과정 급수(0=없음)
             'paid_pass',          p.type,                -- 유료 전체 이용권
             'has_login',          (u.id is not null)
           ) as x
      from public.founding_members f
      left join public.founding_benefits b on b.email = lower(trim(f.email))
      left join auth.users            u on lower(u.email) = lower(trim(f.email))
      left join public.member_access  m on m.user_id = u.id
      left join public.cert_access    c on c.user_id = u.id
      left join public.pass_members   p on p.email  = lower(trim(f.email))
     where _is_store_admin()
  ) t;
$$;

-- ── 4) 관리자: 창립 1년 부여(연장) ──
-- 반환 'OK'=즉시 활성 / 'PENDING'=미가입이라 예약만 / 'NOT_ADMIN'
create or replace function grant_founding(p_email text, p_months int default 12)
returns text language plpgsql security definer as $$
declare em text; uid uuid; exp timestamptz;
begin
  if not _is_store_admin() then return 'NOT_ADMIN'; end if;
  em := lower(trim(coalesce(p_email,'')));
  if em = '' then return 'NO_EMAIL'; end if;

  -- 명단에 없으면(메일로만 받은 신청자 등) 번호를 새로 부여해 등록
  if not exists (select 1 from public.founding_members where lower(trim(email)) = em) then
    insert into public.founding_members(email, name, member_no)
    values (em, null, (select coalesce(max(member_no),0) + 1 from public.founding_members))
    on conflict do nothing;
  end if;

  exp := now() + (p_months || ' months')::interval;

  -- 약속 대장 (기간은 절대 줄이지 않는다)
  insert into public.founding_benefits(email, expires_at, granted_by, note)
  values (em, exp, 'admin', '관리자 부여')
  on conflict (email) do update
    set expires_at = greatest(public.founding_benefits.expires_at, excluded.expires_at);

  select id into uid from auth.users where lower(email) = em limit 1;
  if uid is null then
    return 'PENDING';                        -- 로그인하면 claim_founding() 이 자동 활성화
  end if;

  insert into public.member_access(user_id, email, kind, started_at, expires_at, updated_at)
  values (uid, em, 'founding', now(), exp, now())
  on conflict (user_id) do update
    set kind       = 'founding',
        email      = coalesce(public.member_access.email, excluded.email),
        expires_at = greatest(public.member_access.expires_at, excluded.expires_at),
        updated_at = now();

  update public.founding_benefits set claimed_at = now() where email = em;
  return 'OK';
end; $$;

-- ── 5) 관리자: 회수 ──
-- 창립 이용권만 지운다. 추천(referral)·체험(trial) 이용권과
-- 창립 번호·신청서 내용(founding_members)은 그대로 남긴다.
create or replace function revoke_founding(p_email text)
returns text language plpgsql security definer as $$
declare em text; uid uuid;
begin
  if not _is_store_admin() then return 'NOT_ADMIN'; end if;
  em := lower(trim(coalesce(p_email,'')));
  delete from public.founding_benefits where email = em;
  select id into uid from auth.users where lower(email) = em limit 1;
  if uid is not null then
    delete from public.member_access where user_id = uid and kind = 'founding';
  end if;
  return 'OK';
end; $$;

-- ── 6) 본인: 예약된 혜택 수령(자가 구제) ──
-- 로그인 안 한 채로 신청했던 분이 나중에 로그인하면 access.js 가 이걸 부른다.
create or replace function claim_founding()
returns text language plpgsql security definer as $$
declare em text; uid uuid; b record;
begin
  em  := lower(coalesce(auth.jwt() ->> 'email',''));
  uid := auth.uid();
  if em = '' or uid is null then return 'NONE'; end if;
  select * into b from public.founding_benefits where email = em;
  if not found then return 'NONE'; end if;
  if b.expires_at <= now() then return 'EXPIRED'; end if;

  insert into public.member_access(user_id, email, kind, started_at, expires_at, updated_at)
  values (uid, em, 'founding', b.started_at, b.expires_at, now())
  on conflict (user_id) do update
    set kind       = 'founding',
        expires_at = greatest(public.member_access.expires_at, excluded.expires_at),
        updated_at = now();

  update public.founding_benefits set claimed_at = now() where email = em;
  return 'OK';
end; $$;

grant execute on function
  list_founding_full(), grant_founding(text,int), revoke_founding(text), claim_founding()
to anon, authenticated;

-- ── 7) 기존 창립 번호 보유자 전원에게 오늘부터 1년 부여 ──
-- 약속 대장부터 채우고(미가입자 포함), 계정이 있는 분은 이용권까지 바로 생성한다.
insert into public.founding_benefits(email, started_at, expires_at, granted_by, note)
select lower(trim(f.email)), now(), now() + interval '12 months', 'migration', '창립 멤버 1년 무료(일괄 부여)'
  from public.founding_members f
 where coalesce(trim(f.email),'') <> ''
on conflict (email) do update
  set expires_at = greatest(public.founding_benefits.expires_at, excluded.expires_at);

insert into public.member_access(user_id, email, kind, started_at, expires_at, updated_at)
select u.id, b.email, 'founding', b.started_at, b.expires_at, now()
  from public.founding_benefits b
  join auth.users u on lower(u.email) = b.email
on conflict (user_id) do update
  set kind       = 'founding',
      expires_at = greatest(public.member_access.expires_at, excluded.expires_at),
      updated_at = now();

update public.founding_benefits b
   set claimed_at = coalesce(b.claimed_at, now())
  from auth.users u
 where lower(u.email) = b.email;

commit;

-- ── 확인용 (실행 후 따로 돌려 보세요) ──
-- select count(*) filter (where kind='founding') as 창립이용권, count(*) as 전체 from public.member_access;
-- select email, kind, expires_at from public.member_access where kind='founding' order by expires_at;
-- select granted_by, count(*), min(expires_at) from public.founding_benefits group by 1;
--
-- ── 되돌리기 ──
-- delete from public.member_access where kind='founding';
-- drop table public.founding_benefits;
-- (완전 복원) begin; delete from public.member_access;
--             insert into public.member_access select * from public._bak_member_access; commit;
