-- ============================================================
-- 말씀묵상 노트 (meditation.html) — 글 + 댓글 + 조회수
-- 사용법: Supabase 대시보드 → SQL Editor → New query → 아래 전체 붙여넣고 RUN
-- 안전: 여러 번 실행해도 됩니다(idempotent).
-- 선행: db/setup.sql 의 is_admin() 함수
-- ============================================================

-- 1) 묵상 글 (관리자만 작성·수정·삭제, 누구나 읽기)
create table if not exists public.meditations (
  id          uuid primary key default gen_random_uuid(),
  category    text not null default '시편묵상',   -- 분류(시편묵상·잠언묵상 등, 자유 입력)
  title       text not null,
  body_html   text,
  excerpt     text,
  views       int  not null default 0,
  author_name text default '오광일',
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);
create index if not exists meditations_idx on public.meditations(created_at desc);

alter table public.meditations enable row level security;

drop policy if exists med_select on public.meditations;
create policy med_select on public.meditations for select using (true);

drop policy if exists med_insert on public.meditations;
create policy med_insert on public.meditations for insert with check (public.is_admin());

drop policy if exists med_update on public.meditations;
create policy med_update on public.meditations for update
  using (public.is_admin()) with check (public.is_admin());

drop policy if exists med_delete on public.meditations;
create policy med_delete on public.meditations for delete using (public.is_admin());

-- 2) 조회수 — 누구나 +1만 가능
create or replace function public.bump_meditation_views(p_id uuid)
returns void language sql security definer set search_path = public as $$
  update public.meditations set views = views + 1 where id = p_id;
$$;
grant execute on function public.bump_meditation_views(uuid) to anon, authenticated;

-- 3) 묵상 댓글 (로그인 회원만 작성, 본인/관리자 삭제)
create table if not exists public.meditation_comments (
  id            uuid primary key default gen_random_uuid(),
  meditation_id uuid references public.meditations(id) on delete cascade,
  user_id       uuid references auth.users(id) on delete set null,
  author_name   text,
  content       text not null,
  is_admin      boolean not null default false,
  created_at    timestamptz not null default now()
);
create index if not exists meditation_comments_idx on public.meditation_comments(meditation_id, created_at);
alter table public.meditation_comments enable row level security;

drop policy if exists mc_select on public.meditation_comments;
create policy mc_select on public.meditation_comments for select using (true);

drop policy if exists mc_insert on public.meditation_comments;
create policy mc_insert on public.meditation_comments for insert with check (auth.uid() = user_id);

drop policy if exists mc_update on public.meditation_comments;
create policy mc_update on public.meditation_comments for update
  using (auth.uid() = user_id) with check (auth.uid() = user_id);

drop policy if exists mc_delete on public.meditation_comments;
create policy mc_delete on public.meditation_comments for delete
  using (public.is_admin() or auth.uid() = user_id);

-- ============================================================
-- 끝! 말씀묵상 노트에 글쓰기·댓글·조회수가 작동합니다.
-- ============================================================
