-- ============================================================
-- 위대한 설교자 시리즈 (preachers.html) — 관리자 추가 글 + 수강생 댓글
-- 사용법: Supabase 대시보드 → SQL Editor → New query → 아래 전체 붙여넣고 RUN
-- 안전: 여러 번 실행해도 됩니다(idempotent).
-- 선행: db/setup.sql 의 is_admin() 함수가 있어야 합니다(관리자=josephoh1611@gmail.com).
-- 초기 10편(스펄전5·로이드존스5)은 content/preachers.json 으로 항상 표시되며 DB 불필요.
-- ============================================================

-- ── 1) 관리자가 추가로 쓰는 설교 글 ──────────────────────────
create table if not exists public.preacher_posts (
  id           uuid primary key default gen_random_uuid(),
  preacher     text not null,           -- 설교자 (예: 찰스 스펄전)
  preacher_en  text,                    -- 설교자 영문
  title        text not null,
  sermon_title text,                    -- 원 설교 제목
  scripture    text,                    -- 본문 성구
  body_html    text not null,
  created_at   timestamptz not null default now()
);
alter table public.preacher_posts enable row level security;
drop policy if exists pp_select on public.preacher_posts;
create policy pp_select on public.preacher_posts for select using (true);          -- 누구나 읽기
drop policy if exists pp_insert on public.preacher_posts;
create policy pp_insert on public.preacher_posts for insert with check (public.is_admin());  -- 관리자만 작성
drop policy if exists pp_update on public.preacher_posts;
create policy pp_update on public.preacher_posts for update using (public.is_admin()) with check (public.is_admin());
drop policy if exists pp_delete on public.preacher_posts;
create policy pp_delete on public.preacher_posts for delete using (public.is_admin());

-- ── 2) 수강생 댓글(묵상 나눔) ────────────────────────────────
-- post_key = JSON 시드 글의 id(slug) 또는 'db-<uuid>'(관리자 추가 글)
create table if not exists public.preacher_comments (
  id          uuid primary key default gen_random_uuid(),
  post_key    text not null,
  user_id     uuid references auth.users(id) on delete set null,
  author_name text,
  content     text not null,
  created_at  timestamptz not null default now()
);
create index if not exists preacher_comments_postkey_idx on public.preacher_comments(post_key, created_at);
alter table public.preacher_comments enable row level security;
drop policy if exists pc_select on public.preacher_comments;
create policy pc_select on public.preacher_comments for select using (true);       -- 누구나 읽기
drop policy if exists pc_insert on public.preacher_comments;
create policy pc_insert on public.preacher_comments for insert with check (auth.uid() = user_id);  -- 로그인 수강생만, 본인 명의
drop policy if exists pc_update on public.preacher_comments;
create policy pc_update on public.preacher_comments for update
  using (auth.uid() = user_id) with check (auth.uid() = user_id);                  -- 본인 댓글만 수정
drop policy if exists pc_delete on public.preacher_comments;
create policy pc_delete on public.preacher_comments for delete
  using (public.is_admin() or auth.uid() = user_id);                              -- 본인 또는 관리자 삭제

-- ============================================================
-- 끝! 이제 위대한 설교자 게시판에서 관리자 글쓰기와 수강생 댓글이 작동합니다.
-- (수강생은 댓글만 가능, 글 작성은 관리자 전용)
-- ============================================================
