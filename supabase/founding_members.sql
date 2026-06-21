-- ============================================================
-- BIBLY 1기 창립 멤버 — 1회만 실행
-- 가입자에게 '창립 멤버 번호'를 부여하고, 관리자가 명단을 보게 합니다.
-- 전제: supabase/store_grant.sql 의 _is_store_admin() 가 먼저 있어야 함.
-- Supabase 대시보드 → SQL Editor 에 붙여넣고 Run
-- ============================================================

create table if not exists public.founding_members (
  email      text primary key,
  name       text,
  member_no  int unique,
  joined_at  timestamptz default now()
);

alter table public.founding_members enable row level security;

-- 로그인한 본인을 창립 멤버로 등록(이미 있으면 그대로) → 멤버 번호 반환
create or replace function join_founding(p_name text default null)
returns int language plpgsql security definer as $$
declare em text; no int;
begin
  em := lower(coalesce(auth.jwt() ->> 'email',''));
  if em = '' then return null; end if;
  select member_no into no from public.founding_members where email = em;
  if no is not null then
    if coalesce(p_name,'') <> '' then update public.founding_members set name = p_name where email = em; end if;
    return no;
  end if;
  select coalesce(max(member_no),0) + 1 into no from public.founding_members;
  insert into public.founding_members(email, name, member_no) values (em, nullif(p_name,''), no);
  return no;
end; $$;

-- 본인의 창립 멤버 번호(없으면 null) — 뱃지 표시용
create or replace function my_founding()
returns int language sql security definer as $$
  select member_no from public.founding_members where email = lower(coalesce(auth.jwt() ->> 'email',''));
$$;

-- 관리자만 전체 명단 조회
create or replace function list_founding()
returns setof public.founding_members language sql security definer as $$
  select * from public.founding_members where _is_store_admin() order by member_no;
$$;

grant execute on function join_founding(text), my_founding(), list_founding() to anon, authenticated;
