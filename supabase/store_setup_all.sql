-- ============================================================
-- BIBLY 스토어 권한 — 통합 설치 (딱 1회만 실행)
-- Supabase 대시보드 → SQL Editor → New query → 아래 전체 복붙 → Run
-- 이 한 파일이 아래 3가지를 순서대로 모두 설치합니다:
--   1) pass_members  (전체 이용권 회원 테이블)
--   2) book_access   (개별 책자 구매 인증 테이블)
--   3) grant/revoke/list RPC 함수 (admin.html '스토어 권한' 버튼용)
-- 여러 번 실행해도 안전합니다(create if not exists / create or replace).
-- ============================================================

-- 1) 전체 이용권(PASS) 회원 테이블 ---------------------------------
create table if not exists public.pass_members (
  email       text primary key,
  type        text,                       -- 'pass-1y' | 'pass-life' 등
  expires_at  timestamptz,                -- NULL = 평생 이용권
  note        text,
  created_at  timestamptz default now()
);
alter table public.pass_members enable row level security;
drop policy if exists "pass self select" on public.pass_members;
create policy "pass self select" on public.pass_members
  for select using ( auth.jwt() ->> 'email' = email );

-- 2) 개별 책자 구매 인증 테이블 ------------------------------------
create table if not exists public.book_access (
  email       text not null,
  track       text not null,            -- 구매한 책(과정) 이름 = booklet 책 제목과 동일
  expires_at  timestamptz,              -- NULL = 영구 소장
  note        text,
  created_at  timestamptz default now(),
  primary key (email, track)
);
alter table public.book_access enable row level security;
drop policy if exists "book self select" on public.book_access;
create policy "book self select" on public.book_access
  for select using ( auth.jwt() ->> 'email' = email );

-- 3) 관리자 부여/회수/목록 RPC 함수 --------------------------------
create or replace function _is_store_admin() returns boolean
language sql stable as $$
  select coalesce(auth.jwt() ->> 'email','') = 'josephoh1611@gmail.com';
$$;

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

-- 완료! 이제 admin.html → '스토어 권한'에서 버튼으로 부여/회수할 수 있습니다.
