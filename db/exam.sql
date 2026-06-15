-- ============================================================
-- 수료 시험 결과 · 학점 테이블 (exam.html, mylearning.html)
-- Supabase 대시보드 → SQL Editor → New query → 붙여넣고 RUN
-- 여러 번 실행해도 안전(idempotent).
-- ============================================================
create table if not exists public.exam_results (
  user_id     uuid not null references auth.users(id) on delete cascade,
  lesson_id   text not null,        -- 유튜브 영상 ID (강의 단위)
  track       text,                 -- 과목(트랙) 이름
  attempt1    int,                  -- 1차 점수 (0~100)
  attempt2    int,                  -- 2차 점수 (0~100, 미응시면 null)
  final_score numeric,              -- 최종 점수
  passed      boolean not null default false,
  updated_at  timestamptz not null default now(),
  primary key (user_id, lesson_id)
);
alter table public.exam_results enable row level security;
drop policy if exists ex_select on public.exam_results;
create policy ex_select on public.exam_results for select using (auth.uid() = user_id);
drop policy if exists ex_insert on public.exam_results;
create policy ex_insert on public.exam_results for insert with check (auth.uid() = user_id);
drop policy if exists ex_update on public.exam_results;
create policy ex_update on public.exam_results for update using (auth.uid() = user_id) with check (auth.uid() = user_id);
drop policy if exists ex_delete on public.exam_results;
create policy ex_delete on public.exam_results for delete using (auth.uid() = user_id);
