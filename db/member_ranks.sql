-- 🏅 회원 급수 휘장(공개용) — 커뮤니티 등에서 작성자 급수를 표시하기 위한 테이블
-- 등급(tier)만 공개하고 이름/연락처 등 개인정보는 담지 않음(프라이버시 안전).
-- Supabase SQL Editor에서 1회 실행.

create table if not exists public.member_ranks (
  user_id    uuid primary key references auth.users(id) on delete cascade,
  tier       int  not null default 0,   -- 1=Associate … 5=Laureate (시험으로 통과한 최고 급수)
  updated_at timestamptz not null default now()
);

alter table public.member_ranks enable row level security;

-- 누구나(로그인 회원) 다른 회원의 급수 휘장을 읽을 수 있음 (등급만 노출)
drop policy if exists "member_ranks read all" on public.member_ranks;
create policy "member_ranks read all" on public.member_ranks
  for select using (true);

-- 본인 급수만 기록/수정 가능
drop policy if exists "member_ranks upsert own" on public.member_ranks;
create policy "member_ranks upsert own" on public.member_ranks
  for insert with check (auth.uid() = user_id);
drop policy if exists "member_ranks update own" on public.member_ranks;
create policy "member_ranks update own" on public.member_ranks
  for update using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- 참고: 내 강의실(mylearning)이 급수 취득 시 자동으로 upsert 하고,
--       커뮤니티(community)가 작성자 user_id로 tier를 읽어 휘장(Ⅰ~Ⅴ 메달)을 표시함.
--       이 테이블이 없어도 사이트는 정상 동작하며, 단지 휘장만 표시되지 않음(graceful).
