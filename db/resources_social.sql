-- ============================================================
-- 자료실(resources.html) — 글 수정 · 댓글 · 첨부 파일 이름
-- 사용법: Supabase 대시보드 → SQL Editor → New query → 아래 전체 붙여넣고 RUN
-- 안전: 여러 번 실행해도 됩니다(idempotent).
-- 선행: db/setup.sql 의 is_admin() 함수, resources 테이블이 있어야 함.
-- ============================================================

-- 1) 첨부 파일의 '원래 이름'을 저장할 칸
--    (없으면 주소 끝의 파일명으로 대신 보여 주지만, 한글 이름은 살릴 수 없다)
alter table public.resources add column if not exists file_name text;

-- 2) 자료 읽기는 누구나, 올리기·고치기·지우기는 관리자만
alter table public.resources enable row level security;
drop policy if exists res_select on public.resources;
create policy res_select on public.resources for select using (true);
drop policy if exists res_insert on public.resources;
create policy res_insert on public.resources for insert with check (public.is_admin());
drop policy if exists res_update on public.resources;
create policy res_update on public.resources for update using (public.is_admin()) with check (public.is_admin());
drop policy if exists res_delete on public.resources;
create policy res_delete on public.resources for delete using (public.is_admin());

-- 3) 자료 댓글 (로그인 회원만 작성, 본인·관리자 삭제)
create table if not exists public.resource_comments (
  id          uuid primary key default gen_random_uuid(),
  resource_id uuid references public.resources(id) on delete cascade,
  user_id     uuid references auth.users(id) on delete set null,
  author_name text,
  content     text not null,
  created_at  timestamptz not null default now()
);
create index if not exists resource_comments_idx on public.resource_comments(resource_id, created_at);
alter table public.resource_comments enable row level security;
drop policy if exists rc_select on public.resource_comments;
create policy rc_select on public.resource_comments for select using (true);
drop policy if exists rc_insert on public.resource_comments;
create policy rc_insert on public.resource_comments for insert with check (auth.uid() = user_id);
drop policy if exists rc_update on public.resource_comments;
create policy rc_update on public.resource_comments for update using (auth.uid() = user_id) with check (auth.uid() = user_id);
drop policy if exists rc_delete on public.resource_comments;
create policy rc_delete on public.resource_comments for delete using (public.is_admin() or auth.uid() = user_id);

-- ============================================================
-- 끝! 자료실에서 글 수정과 댓글이 작동합니다.
-- ============================================================
