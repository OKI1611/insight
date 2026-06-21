-- ============================================================
-- BIBLY 스토어 권한 관리 RPC — 1회만 실행
-- 관리자 페이지(admin.html → 🛒 스토어 권한)에서 버튼으로 이용권·교재를
-- 부여/회수할 수 있게 해주는 함수들. (SQL을 매번 칠 필요 없음)
-- 전제: supabase/pass_members.sql, supabase/book_access.sql 을 먼저 실행했을 것.
-- Supabase 대시보드 → SQL Editor 에 붙여넣고 Run
-- ============================================================

-- 관리자 판별(이 함수의 JWT 이메일이 관리자 메일인지)
create or replace function _is_store_admin() returns boolean
language sql stable as $$
  select coalesce(auth.jwt() ->> 'email','') = 'josephoh1611@gmail.com';
$$;

-- 전체 이용권 부여 (p_type: 'pass-life'=평생, 'pass-1y'=1년)
create or replace function grant_pass(p_email text, p_type text)
returns text language plpgsql security definer as $$
begin
  if not _is_store_admin() then return 'NOT_ADMIN'; end if;
  insert into public.pass_members(email, type, expires_at)
  values (lower(trim(p_email)), p_type,
          case when p_type = 'pass-1y' then now() + interval '1 year' else null end)
  on conflict (email) do update set type = excluded.type, expires_at = excluded.expires_at;
  return 'OK';
end; $$;

create or replace function revoke_pass(p_email text)
returns text language plpgsql security definer as $$
begin
  if not _is_store_admin() then return 'NOT_ADMIN'; end if;
  delete from public.pass_members where email = lower(trim(p_email));
  return 'OK';
end; $$;

create or replace function list_pass()
returns setof public.pass_members language sql security definer as $$
  select * from public.pass_members where _is_store_admin() order by created_at desc;
$$;

-- 개별 교재(책) 권한 부여
create or replace function grant_book(p_email text, p_track text)
returns text language plpgsql security definer as $$
begin
  if not _is_store_admin() then return 'NOT_ADMIN'; end if;
  insert into public.book_access(email, track)
  values (lower(trim(p_email)), p_track)
  on conflict (email, track) do nothing;
  return 'OK';
end; $$;

create or replace function revoke_book(p_email text, p_track text)
returns text language plpgsql security definer as $$
begin
  if not _is_store_admin() then return 'NOT_ADMIN'; end if;
  delete from public.book_access where email = lower(trim(p_email)) and track = p_track;
  return 'OK';
end; $$;

create or replace function list_book()
returns setof public.book_access language sql security definer as $$
  select * from public.book_access where _is_store_admin() order by created_at desc;
$$;

grant execute on function
  grant_pass(text,text), revoke_pass(text), list_pass(),
  grant_book(text,text), revoke_book(text,text), list_book()
to anon, authenticated;
