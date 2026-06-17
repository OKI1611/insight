-- ============================================================
-- 칼럼(column.html) 댓글 + 조회수
-- 사용법: Supabase 대시보드 → SQL Editor → New query → 붙여넣고 RUN (여러 번 실행해도 안전)
-- 선행: db/setup.sql 의 is_admin() 함수, columns 테이블이 있어야 함.
-- ============================================================

-- 1) 조회수 컬럼 + 안전한 증가 함수(누구나 +1만 가능)
alter table public.columns add column if not exists views int not null default 0;

create or replace function public.bump_column_views(p_id uuid)
returns void language sql security definer set search_path = public as $$
  update public.columns set views = views + 1 where id = p_id;
$$;
grant execute on function public.bump_column_views(uuid) to anon, authenticated;

-- 2) 칼럼 댓글 (로그인 수강생만 작성, 본인/관리자 삭제)
create table if not exists public.column_comments (
  id          uuid primary key default gen_random_uuid(),
  column_id   uuid references public.columns(id) on delete cascade,
  user_id     uuid references auth.users(id) on delete set null,
  author_name text,
  content     text not null,
  created_at  timestamptz not null default now()
);
create index if not exists column_comments_idx on public.column_comments(column_id, created_at);
alter table public.column_comments enable row level security;
drop policy if exists cc_select on public.column_comments;
create policy cc_select on public.column_comments for select using (true);
drop policy if exists cc_insert on public.column_comments;
create policy cc_insert on public.column_comments for insert with check (auth.uid() = user_id);
drop policy if exists cc_update on public.column_comments;
create policy cc_update on public.column_comments for update using (auth.uid() = user_id) with check (auth.uid() = user_id);
drop policy if exists cc_delete on public.column_comments;
create policy cc_delete on public.column_comments for delete using (public.is_admin() or auth.uid() = user_id);

-- ============================================================
-- 끝! 칼럼 글에 댓글과 조회수가 작동합니다. (댓글=로그인 수강생, 조회수=자동)
-- ============================================================
