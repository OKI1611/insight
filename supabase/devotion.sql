-- 매일 말씀과 함께 — 묵상 완료 기록(스트릭)
-- Supabase SQL 편집기에서 한 번 실행하세요.

create table if not exists public.devotion_log (
  user_id    uuid not null references auth.users(id) on delete cascade,
  devo_date  date not null,                 -- 묵상한 날짜(해당 묵상의 date)
  created_at timestamptz not null default now(),
  primary key (user_id, devo_date)
);

alter table public.devotion_log enable row level security;

drop policy if exists "devotion own select" on public.devotion_log;
create policy "devotion own select" on public.devotion_log
  for select using (auth.uid() = user_id);

drop policy if exists "devotion own insert" on public.devotion_log;
create policy "devotion own insert" on public.devotion_log
  for insert with check (auth.uid() = user_id);

drop policy if exists "devotion own delete" on public.devotion_log;
create policy "devotion own delete" on public.devotion_log
  for delete using (auth.uid() = user_id);
