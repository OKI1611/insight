-- ============================================================
-- BIBLY 전체 이용권(PASS) 회원 테이블 — 1회만 실행
-- Supabase 대시보드 → SQL Editor 에 붙여넣고 Run
-- ============================================================

create table if not exists public.pass_members (
  email       text primary key,
  type        text,                       -- 'pass-1y' | 'pass-life' 등
  expires_at  timestamptz,                -- NULL = 평생 이용권
  note        text,
  created_at  timestamptz default now()
);

alter table public.pass_members enable row level security;

-- 로그인한 본인의 이용권 행만 조회 가능(다른 사람 이메일은 안 보임)
drop policy if exists "pass self select" on public.pass_members;
create policy "pass self select" on public.pass_members
  for select using ( auth.jwt() ->> 'email' = email );

-- 회원 추가/수정/삭제는 대시보드(또는 service-role)에서 관리자가 직접 합니다.
-- 예) 입금 확인 후:
--   1년권:   insert into pass_members(email, type, expires_at)
--            values ('buyer@example.com', 'pass-1y', now() + interval '1 year');
--   평생권:  insert into pass_members(email, type, expires_at)
--            values ('buyer@example.com', 'pass-life', null);
