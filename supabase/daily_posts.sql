-- 매일 말씀과 함께 — 수강생 묵상 나눔(블로그식)
-- Supabase SQL 편집기에서 한 번 실행하세요.

create table if not exists public.daily_posts (
  id          uuid primary key default gen_random_uuid(),
  author_id   uuid not null references auth.users(id) on delete cascade,
  author_name text,
  devo_date   date not null,                 -- 어느 날짜 묵상에 붙는 글인지
  title       text,
  content     text not null,
  created_at  timestamptz not null default now()
);
create index if not exists daily_posts_date_idx on public.daily_posts(devo_date, created_at desc);

create table if not exists public.daily_post_likes (
  post_id uuid not null references public.daily_posts(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  primary key (post_id, user_id)
);

alter table public.daily_posts enable row level security;
alter table public.daily_post_likes enable row level security;

-- 글: 누구나 읽기, 본인만 작성·수정·삭제
drop policy if exists "daily_posts read" on public.daily_posts;
create policy "daily_posts read" on public.daily_posts for select using (true);
drop policy if exists "daily_posts insert own" on public.daily_posts;
create policy "daily_posts insert own" on public.daily_posts for insert with check (auth.uid() = author_id);
drop policy if exists "daily_posts update own" on public.daily_posts;
create policy "daily_posts update own" on public.daily_posts for update using (auth.uid() = author_id) with check (auth.uid() = author_id);
drop policy if exists "daily_posts delete own" on public.daily_posts;
create policy "daily_posts delete own" on public.daily_posts for delete using (auth.uid() = author_id);

-- 공감: 누구나 읽기, 본인 것만 추가·삭제
drop policy if exists "daily_likes read" on public.daily_post_likes;
create policy "daily_likes read" on public.daily_post_likes for select using (true);
drop policy if exists "daily_likes insert own" on public.daily_post_likes;
create policy "daily_likes insert own" on public.daily_post_likes for insert with check (auth.uid() = user_id);
drop policy if exists "daily_likes delete own" on public.daily_post_likes;
create policy "daily_likes delete own" on public.daily_post_likes for delete using (auth.uid() = user_id);
