-- 성경암송 365 — 학습/테스트 기록
-- Supabase SQL 편집기에서 한 번 실행하세요.

create table if not exists public.memorize_records (
  user_id    uuid not null references auth.users(id) on delete cascade,
  verse_id   text not null,
  learned    boolean not null default false,   -- 암송 학습 완료(외웠어요) 여부
  test_best  int not null default 0,            -- 테스트 최고 점수(0~100)
  test_count int not null default 0,            -- 테스트 응시 횟수
  learned_at timestamptz,                       -- 처음 외운 시각
  updated_at timestamptz not null default now(),
  primary key (user_id, verse_id)
);

alter table public.memorize_records enable row level security;

-- 본인 기록만 읽기/쓰기
drop policy if exists "memorize own select" on public.memorize_records;
create policy "memorize own select" on public.memorize_records
  for select using (auth.uid() = user_id);

drop policy if exists "memorize own upsert" on public.memorize_records;
create policy "memorize own upsert" on public.memorize_records
  for insert with check (auth.uid() = user_id);

drop policy if exists "memorize own update" on public.memorize_records;
create policy "memorize own update" on public.memorize_records
  for update using (auth.uid() = user_id) with check (auth.uid() = user_id);

drop policy if exists "memorize own delete" on public.memorize_records;
create policy "memorize own delete" on public.memorize_records
  for delete using (auth.uid() = user_id);
