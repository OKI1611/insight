-- ============================================================
-- 방문 통계 (E단계) — 간단한 페이지 방문 로깅
-- 각 방문자는 세션당 1회 기록되며, 관리자 콘솔 대시보드에 집계됩니다.
-- 사용법: Supabase 대시보드 → SQL Editor → 붙여넣고 RUN
-- ============================================================

create table if not exists public.site_visits (
  id         uuid primary key default gen_random_uuid(),
  path       text,
  created_at timestamptz not null default now()
);

alter table public.site_visits enable row level security;

-- 누구나(비로그인 포함) 방문 기록을 남길 수 있음
drop policy if exists "visits_insert_any" on public.site_visits;
create policy "visits_insert_any" on public.site_visits for insert with check (true);

-- 조회는 관리자만
drop policy if exists "visits_admin_select" on public.site_visits;
create policy "visits_admin_select" on public.site_visits for select
  using ((auth.jwt() ->> 'email') = 'josephoh1611@gmail.com');

-- 조회 속도용 인덱스
create index if not exists site_visits_created_idx on public.site_visits (created_at);
