-- ============================================================
-- 수강생 라운지(커뮤니티) — 테이블 + 보안정책(RLS) + 반응(❤️🙏)
-- 적용: Supabase 대시보드 → SQL Editor → New query → 아래 전체 붙여넣기 → Run
-- (한 번만 실행하면 됩니다. 이미 있어도 다시 실행해도 안전합니다.)
-- ※ '글이 올라가지 않는' 문제는 보통 아래 insert 정책 누락이 원인입니다.
-- ============================================================

-- 1) 게시글 -------------------------------------------------
create table if not exists public.community_posts (
  id          uuid primary key default gen_random_uuid(),
  board       text not null default 'free',
  author_id   uuid not null references auth.users(id) on delete cascade,
  author_name text,
  content     text,
  image_url   text,
  created_at  timestamptz not null default now()
);
alter table public.community_posts enable row level security;

drop policy if exists "posts_read"   on public.community_posts;
create policy "posts_read"   on public.community_posts for select using (true);

drop policy if exists "posts_insert" on public.community_posts;
create policy "posts_insert" on public.community_posts for insert
  with check (auth.uid() = author_id);

drop policy if exists "posts_delete" on public.community_posts;
create policy "posts_delete" on public.community_posts for delete
  using (auth.uid() = author_id or (auth.jwt() ->> 'email') = 'josephoh1611@gmail.com');

-- 2) 댓글(답글) ---------------------------------------------
create table if not exists public.community_comments (
  id          uuid primary key default gen_random_uuid(),
  post_id     uuid not null references public.community_posts(id) on delete cascade,
  author_id   uuid not null references auth.users(id) on delete cascade,
  author_name text,
  content     text not null,
  is_admin    boolean not null default false,
  created_at  timestamptz not null default now()
);
create index if not exists community_comments_post_idx on public.community_comments(post_id);
alter table public.community_comments enable row level security;

drop policy if exists "comments_read"   on public.community_comments;
create policy "comments_read"   on public.community_comments for select using (true);

drop policy if exists "comments_insert" on public.community_comments;
create policy "comments_insert" on public.community_comments for insert
  with check (auth.uid() = author_id);

drop policy if exists "comments_delete" on public.community_comments;
create policy "comments_delete" on public.community_comments for delete
  using (auth.uid() = author_id or (auth.jwt() ->> 'email') = 'josephoh1611@gmail.com');

-- 3) 반응(❤️ 공감 / 🙏 기도) --------------------------------
create table if not exists public.community_reactions (
  id         uuid primary key default gen_random_uuid(),
  post_id    uuid not null references public.community_posts(id) on delete cascade,
  user_id    uuid not null references auth.users(id) on delete cascade,
  emoji      text not null,
  created_at timestamptz not null default now(),
  unique (post_id, user_id, emoji)
);
create index if not exists community_reactions_post_idx on public.community_reactions(post_id);
alter table public.community_reactions enable row level security;

drop policy if exists "reactions_read"   on public.community_reactions;
create policy "reactions_read"   on public.community_reactions for select using (true);

drop policy if exists "reactions_insert" on public.community_reactions;
create policy "reactions_insert" on public.community_reactions for insert
  with check (auth.uid() = user_id);

drop policy if exists "reactions_delete" on public.community_reactions;
create policy "reactions_delete" on public.community_reactions for delete
  using (auth.uid() = user_id);

-- 4) (선택) 이미지 업로드용 스토리지 버킷 'community'가 없다면 ----
--   Supabase → Storage → New bucket → 이름 'community', Public 체크
--   그리고 아래 정책을 추가하면 로그인 사용자가 업로드할 수 있습니다.
-- create policy "community_upload" on storage.objects for insert
--   to authenticated with check (bucket_id = 'community');
-- create policy "community_read" on storage.objects for select
--   using (bucket_id = 'community');
