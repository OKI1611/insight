-- ============================================================
-- 관리자용 수강권 부여/회수/목록 함수 (admin.html '수강권' 탭에서 사용)
-- Supabase SQL Editor → New query → 붙여넣고 RUN (여러 번 실행해도 안전)
-- SECURITY DEFINER: auth.users(이메일) 조회를 위해 권한 상승하되,
--                   함수 내부에서 is_admin()을 확인해 관리자만 실행 가능.
-- 선행: db/cert.sql(또는 setup.sql)로 cert_access 테이블과 is_admin() 함수가 있어야 함.
-- ============================================================

-- 이메일로 수강권 부여(또는 등급 변경). tier 1=Associate·2=Professional·3=Expert.
create or replace function public.grant_cert(p_email text, p_tier int, p_package text default null)
returns text language plpgsql security definer set search_path = public as $$
declare uid uuid;
begin
  if not public.is_admin() then raise exception 'forbidden'; end if;
  select id into uid from auth.users where lower(email) = lower(trim(p_email)) limit 1;
  if uid is null then return 'NOT_FOUND'; end if;
  insert into public.cert_access(user_id, tier, package, granted_at)
    values (uid, p_tier, p_package, now())
    on conflict (user_id) do update set tier = excluded.tier, package = excluded.package, granted_at = now();
  return 'OK';
end; $$;
grant execute on function public.grant_cert(text,int,text) to authenticated;

-- 이메일로 수강권 회수.
create or replace function public.revoke_cert(p_email text)
returns text language plpgsql security definer set search_path = public as $$
declare uid uuid;
begin
  if not public.is_admin() then raise exception 'forbidden'; end if;
  select id into uid from auth.users where lower(email) = lower(trim(p_email)) limit 1;
  if uid is null then return 'NOT_FOUND'; end if;
  delete from public.cert_access where user_id = uid;
  return 'OK';
end; $$;
grant execute on function public.revoke_cert(text) to authenticated;

-- 수강권 보유자 목록(이메일 포함). 관리자만.
create or replace function public.list_cert()
returns table(email text, tier int, package text, granted_at timestamptz)
language sql security definer set search_path = public stable as $$
  select u.email::text, c.tier, c.package, c.granted_at
  from public.cert_access c join auth.users u on u.id = c.user_id
  where public.is_admin()
  order by c.granted_at desc;
$$;
grant execute on function public.list_cert() to authenticated;
