-- ============================================================
-- BIBLY 멤버십(창립멤버 1년 / 추천 가입 3개월) — 한 번에 실행
-- Supabase SQL Editor에서 전체 복사 → Run. 여러 번 실행해도 안전(idempotent).
-- ============================================================

-- 1) 창립멤버 신청 표: 빠진 컬럼 보정(이미 있던 표여서 컬럼이 안 들어갔던 경우 대비)
create table if not exists public.founding_members (
  id bigint generated always as identity primary key,
  created_at timestamptz not null default now(),
  name text not null,
  email text not null
);
alter table public.founding_members add column if not exists phone        text;
alter table public.founding_members add column if not exists region       text;
alter table public.founding_members add column if not exists church       text;
alter table public.founding_members add column if not exists faith_years  text;
alter table public.founding_members add column if not exists motivation   text;
alter table public.founding_members add column if not exists ideal_church text;
alter table public.founding_members add column if not exists ideal_pastor text;
alter table public.founding_members add column if not exists prayer       text;
alter table public.founding_members add column if not exists promise      boolean default false;

alter table public.founding_members enable row level security;
drop policy if exists "founding insert anyone" on public.founding_members;
create policy "founding insert anyone" on public.founding_members
  for insert with check (true);

-- 2) 멤버 이용권(접근) 표 — 창립멤버(1년)·추천가입(3개월)의 무료 이용기간 관리
create table if not exists public.member_access (
  user_id        uuid primary key references auth.users(id) on delete cascade,
  email          text,
  kind           text not null,            -- 'founding'(창립멤버,1년) | 'referral'(추천가입,3개월)
  referrer_email text,                      -- 추천한 창립멤버 이메일
  referrer_name  text,                      -- 추천한 창립멤버 이름
  started_at     timestamptz not null default now(),
  expires_at     timestamptz not null,      -- 무료 이용 만료일(이후 결제 안내)
  updated_at     timestamptz not null default now()
);
alter table public.member_access enable row level security;

-- 본인 이용권만 조회/생성/수정 (만료 판단·결제안내에 사용)
drop policy if exists "access read own" on public.member_access;
create policy "access read own" on public.member_access
  for select using (auth.uid() = user_id);
drop policy if exists "access insert own" on public.member_access;
create policy "access insert own" on public.member_access
  for insert with check (auth.uid() = user_id);
drop policy if exists "access update own" on public.member_access;
create policy "access update own" on public.member_access
  for update using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- 참고:
--  · 창립멤버: founding.html 신청(로그인 상태)에서 kind='founding', expires_at = now()+1년 으로 기록.
--  · 추천가입: 회원가입 시 추천인(창립멤버) 이메일 입력 → kind='referral', expires_at = now()+3개월.
--  · 만료 후에는 유료 자료(인증과정 시험·교재 PDF) 접근이 잠기고 결제 안내가 표시됨(창립멤버는 20% 할인).
--  · 실제 유료 결제(PG/계좌이체)는 사업자등록 후 연결. 현재는 안내 메시지까지 구현.
