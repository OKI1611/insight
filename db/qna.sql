-- ============================================================
-- 질의응답 코너 (qna.html · qna-board.html)
-- 사용법: Supabase 대시보드 → SQL Editor → New query → 아래 전체 붙여넣고 RUN
-- 안전: 여러 번 실행해도 됩니다(idempotent).
-- 선행: db/setup.sql 의 is_admin() 함수, db/community.sql 의 community_posts 테이블
-- ============================================================

-- ------------------------------------------------------------
-- 1) 수강생 질문방 — 기존 community_posts(board='qna')를 그대로 쓴다.
--    여기에 '답변 완료' 표시 칸만 더한다.
-- ------------------------------------------------------------
alter table public.community_posts add column if not exists answered boolean not null default false;

-- 관리자가 답변 완료 표시를 켜고 끌 수 있게 update 정책 추가
drop policy if exists posts_update on public.community_posts;
create policy posts_update on public.community_posts for update
  using (public.is_admin() or auth.uid() = author_id)
  with check (public.is_admin() or auth.uid() = author_id);

-- 목록 정렬용 인덱스
create index if not exists community_posts_board_idx
  on public.community_posts(board, created_at desc);

-- ------------------------------------------------------------
-- 2) 정리된 질의응답(qna.html)의 답변에 달리는 댓글
--    qa_id 는 content/qna.json 의 id 또는 site_content['qna_posts'] 의 id (문자열)
-- ------------------------------------------------------------
create table if not exists public.qna_comments (
  id          uuid primary key default gen_random_uuid(),
  qa_id       text not null,
  user_id     uuid references auth.users(id) on delete set null,
  author_name text,
  content     text not null,
  is_admin    boolean not null default false,
  created_at  timestamptz not null default now()
);
create index if not exists qna_comments_idx on public.qna_comments(qa_id, created_at);

alter table public.qna_comments enable row level security;

drop policy if exists qc_select on public.qna_comments;
create policy qc_select on public.qna_comments for select using (true);

drop policy if exists qc_insert on public.qna_comments;
create policy qc_insert on public.qna_comments for insert with check (auth.uid() = user_id);

drop policy if exists qc_update on public.qna_comments;
create policy qc_update on public.qna_comments for update
  using (auth.uid() = user_id) with check (auth.uid() = user_id);

drop policy if exists qc_delete on public.qna_comments;
create policy qc_delete on public.qna_comments for delete
  using (public.is_admin() or auth.uid() = user_id);

-- ============================================================
-- 끝! 이제 수강생 질문방에 '답변 완료' 표시가 되고,
--     정리된 질의응답 답변마다 댓글을 달 수 있습니다.
-- ============================================================
