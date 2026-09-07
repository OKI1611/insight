-- ============================================================
-- rpc_hardening.sql 후속 보완 (2026-09-07 · 2차)
-- 실행 방법: Supabase 대시보드 → SQL Editor → 전체 붙여넣고 Run
--   ※ 맨 아래에 확인용 조회가 있어 실행하면 결과 표가 함께 나옵니다.
--      그 표를 그대로 알려 주시면 제가 최종 확인해 드립니다.
-- ============================================================
-- [1차 실행 후 발견된 것]
--   ① app_testers 표에 배송지 컬럼(ship_name·ship_address·gift_submitted_at 등)이
--      **아예 없었다.** supabase_tester_gift.sql 이 라이브에 적용된 적이 없다.
--      → 완주 선물 배송지 페이지(tester-gift.html)는 원래부터 저장이 안 되는 상태였다.
--        (1차 강화 때문이 아니라 그 전부터 깨져 있었다. 여기서 함께 고친다.)
--   ② reset_tester_gift 를 anon 에서 revoke 했지만, PostgreSQL 은 함수 실행 권한을
--      기본으로 PUBLIC 에 부여한다. anon 은 PUBLIC 을 통해 여전히 호출할 수 있었다.
--      다행히 함수 안의 is_admin() 검사가 막아 주었으나(익명 호출 시 '관리자만' 예외),
--      권한 자체를 제대로 회수한다.
-- ============================================================

-- ────────────────────────────────────────────────────────────
-- 1) app_testers 배송지 컬럼 추가 — 선물 기능 복구
-- ────────────────────────────────────────────────────────────
alter table public.app_testers add column if not exists book              text;
alter table public.app_testers add column if not exists address           text;
alter table public.app_testers add column if not exists ship_name         text;
alter table public.app_testers add column if not exists ship_phone        text;
alter table public.app_testers add column if not exists ship_address      text;
alter table public.app_testers add column if not exists gift_book         text;
alter table public.app_testers add column if not exists gift_memo         text;
alter table public.app_testers add column if not exists gift_submitted_at timestamptz;

-- ────────────────────────────────────────────────────────────
-- 2) 함수 실행 권한 제대로 회수 (PUBLIC 기본 부여를 먼저 없애야 한다)
-- ────────────────────────────────────────────────────────────
revoke execute on function public.reset_tester_gift(text) from public;
revoke execute on function public.reset_tester_gift(text) from anon;
grant  execute on function public.reset_tester_gift(text) to authenticated;

-- 신청 경로 두 개는 비로그인도 불러야 하므로 anon 유지(내부에서 소유자 검사를 한다)
grant execute on function
  apply_founding(text,text,text,text,text,text,text,text,text,text,boolean,int) to anon, authenticated;
grant execute on function
  public.submit_tester_gift(text,text,text,text,text,text) to anon, authenticated;

-- ────────────────────────────────────────────────────────────
-- 3) founding_members 직접 삽입 정책 재확인 (이미 되어 있으면 그대로)
-- ────────────────────────────────────────────────────────────
do $$
declare r record;
begin
  for r in
    select policyname from pg_policies
     where schemaname='public' and tablename='founding_members' and cmd='INSERT'
  loop
    execute format('drop policy if exists %I on public.founding_members', r.policyname);
  end loop;
end $$;

create policy "founding insert admin only" on public.founding_members
  for insert to authenticated with check ( public.is_admin() );

-- ============================================================
-- 확인용 — 아래 두 표의 결과를 알려 주세요
-- ============================================================
-- ① founding_members 에 남은 정책 (INSERT 는 'founding insert admin only' 하나여야 정상)
select 'policy' as 구분, policyname as 이름, cmd as 동작, roles::text as 대상역할
  from pg_policies
 where schemaname='public' and tablename='founding_members'
union all
-- ② app_testers 배송지 컬럼 (6개가 모두 나와야 정상)
select 'column' as 구분, column_name as 이름, data_type as 동작, '' as 대상역할
  from information_schema.columns
 where table_schema='public' and table_name='app_testers'
   and column_name in ('ship_name','ship_phone','ship_address','gift_book','gift_memo','gift_submitted_at')
order by 1, 2;
