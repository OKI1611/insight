-- ============================================================
-- 관리자 편집 즉시 반영 — 사이트 콘텐츠 저장소
-- 관리자가 admin.html에서 커리큘럼/설정을 저장하면 이 테이블에 들어가고,
-- 모든 페이지가 이 값을 우선 로드해 '즉시 반영'됩니다(없으면 정적 파일).
-- 사용법: Supabase 대시보드 → SQL Editor → 붙여넣고 RUN
-- ============================================================

create table if not exists public.site_content (
  key        text primary key,           -- 'course' | 'site'
  data       jsonb not null,
  updated_at timestamptz not null default now()
);

alter table public.site_content enable row level security;

-- 누구나 읽기(공개 콘텐츠) — 사이트가 우선 로드
drop policy if exists "content_select_all" on public.site_content;
create policy "content_select_all" on public.site_content for select using (true);

-- 저장(쓰기)은 관리자만
drop policy if exists "content_write_admin" on public.site_content;
create policy "content_write_admin" on public.site_content for all
  using ((auth.jwt() ->> 'email') = 'josephoh1611@gmail.com')
  with check ((auth.jwt() ->> 'email') = 'josephoh1611@gmail.com');
