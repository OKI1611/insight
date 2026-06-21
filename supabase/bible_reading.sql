-- ============================================================
-- BIBLY 성경 통독(1년 1독) 진도 저장 — 1회만 실행
-- 로그인한 수강생이 회독 플랜·시작일·완료한 날짜를 계정에 저장.
-- 내 강의실에서 진도를 한눈에 보여주는 데 사용.
-- Supabase 대시보드 → SQL Editor 에 붙여넣고 Run
-- ============================================================

create table if not exists public.bible_reading (
  user_id    uuid primary key references auth.users(id) on delete cascade,
  plan_reads int  not null default 1,                 -- 회독 수(1년에 몇 독)
  start_date date not null default current_date,       -- 통독 시작일(Day 1)
  checked    jsonb not null default '[]'::jsonb,        -- 완료한 Day 번호 배열 [1,2,5,...]
  updated_at timestamptz default now()
);

alter table public.bible_reading enable row level security;

-- 본인 행만 조회/생성/수정 (다른 사람 진도는 접근 불가)
drop policy if exists "bible_reading_select_own" on public.bible_reading;
create policy "bible_reading_select_own" on public.bible_reading
  for select using (auth.uid() = user_id);

drop policy if exists "bible_reading_insert_own" on public.bible_reading;
create policy "bible_reading_insert_own" on public.bible_reading
  for insert with check (auth.uid() = user_id);

drop policy if exists "bible_reading_update_own" on public.bible_reading;
create policy "bible_reading_update_own" on public.bible_reading
  for update using (auth.uid() = user_id) with check (auth.uid() = user_id);

grant select, insert, update on public.bible_reading to authenticated;
