-- ============================================================
-- 강의 요청·건의함 (request.html)용 Supabase 테이블 + 보안정책
-- 사용법: Supabase 대시보드 → SQL Editor → 아래 전체 붙여넣고 RUN
-- ============================================================

-- 1) 요청·건의 글 테이블
create table if not exists public.lecture_requests (
  id          uuid primary key default gen_random_uuid(),
  created_at  timestamptz not null default now(),
  type        text not null default 'request',     -- 'request'(강의 요청) | 'feedback'(건의)
  title       text not null,
  body        text,
  author_id   uuid references auth.users(id) on delete set null,
  author_name text,
  status      text not null default '접수',          -- 접수 / 검토중 / 제작확정 / 완료
  admin_reply text
);

-- 2) 추천(투표) 테이블 — 한 사람당 글 하나에 1표
create table if not exists public.lecture_request_votes (
  request_id uuid not null references public.lecture_requests(id) on delete cascade,
  user_id    uuid not null references auth.users(id) on delete cascade,
  created_at timestamptz not null default now(),
  primary key (request_id, user_id)
);

-- 3) RLS(행 수준 보안) 활성화
alter table public.lecture_requests       enable row level security;
alter table public.lecture_request_votes  enable row level security;

-- 4) 정책 — 요청·건의 글 (재실행 안전: 기존 정책 있으면 먼저 제거)
drop policy if exists "requests_select_all"         on public.lecture_requests;
drop policy if exists "requests_insert_own"         on public.lecture_requests;
drop policy if exists "requests_delete_owner_admin" on public.lecture_requests;
drop policy if exists "requests_update_admin"       on public.lecture_requests;
create policy "requests_select_all"        on public.lecture_requests for select using (true);
create policy "requests_insert_own"        on public.lecture_requests for insert with check (auth.uid() = author_id);
create policy "requests_delete_owner_admin" on public.lecture_requests for delete
  using (auth.uid() = author_id or (auth.jwt() ->> 'email') = 'josephoh1611@gmail.com');
create policy "requests_update_admin"      on public.lecture_requests for update
  using      ((auth.jwt() ->> 'email') = 'josephoh1611@gmail.com')
  with check ((auth.jwt() ->> 'email') = 'josephoh1611@gmail.com');

-- 5) 정책 — 추천(투표)
drop policy if exists "votes_select_all"  on public.lecture_request_votes;
drop policy if exists "votes_insert_own"  on public.lecture_request_votes;
drop policy if exists "votes_delete_own"  on public.lecture_request_votes;
create policy "votes_select_all"  on public.lecture_request_votes for select using (true);
create policy "votes_insert_own"  on public.lecture_request_votes for insert with check (auth.uid() = user_id);
create policy "votes_delete_own"  on public.lecture_request_votes for delete using (auth.uid() = user_id);
