-- 매일 말씀과 함께 — 묵상 본문 관리자 수정본(오버라이드)
-- 정적 파일(content/daily/<날짜>.json)을 화면에서 직접 고쳐 저장하는 용도.
-- 저장하면 모든 방문자가 이 수정본을 보게 된다. Supabase SQL 편집기에서 한 번 실행하세요.

create table if not exists public.daily_overrides (
  devo_date  date primary key,         -- 어느 날짜 묵상인지
  data       jsonb not null,           -- 수정된 묵상 전체(JSON)
  updated_at timestamptz not null default now()
);

alter table public.daily_overrides enable row level security;

-- 읽기: 누구나(방문자가 수정본을 볼 수 있어야 함)
drop policy if exists "daily_overrides read" on public.daily_overrides;
create policy "daily_overrides read" on public.daily_overrides for select using (true);

-- 쓰기: 관리자만(이메일은 cms.js의 ADMIN과 동일)
drop policy if exists "daily_overrides admin insert" on public.daily_overrides;
create policy "daily_overrides admin insert" on public.daily_overrides
  for insert with check (auth.jwt() ->> 'email' = 'josephoh1611@gmail.com');
drop policy if exists "daily_overrides admin update" on public.daily_overrides;
create policy "daily_overrides admin update" on public.daily_overrides
  for update using (auth.jwt() ->> 'email' = 'josephoh1611@gmail.com')
  with check (auth.jwt() ->> 'email' = 'josephoh1611@gmail.com');
drop policy if exists "daily_overrides admin delete" on public.daily_overrides;
create policy "daily_overrides admin delete" on public.daily_overrides
  for delete using (auth.jwt() ->> 'email' = 'josephoh1611@gmail.com');
