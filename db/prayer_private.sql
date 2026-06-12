-- ============================================================
-- 기도요청 비공개 기능 — community_posts에 is_private 추가 + 열람 정책 강화
-- 비공개 글은 '작성자 본인'과 '관리자'만 볼 수 있습니다(서버에서 차단).
-- 적용: Supabase 대시보드 → SQL Editor → 붙여넣고 RUN
-- ============================================================

-- 1) 비공개 여부 컬럼
alter table public.community_posts
  add column if not exists is_private boolean not null default false;

-- 2) 열람 정책 교체 — 공개글은 모두, 비공개글은 작성자/관리자만
drop policy if exists "posts_read" on public.community_posts;
create policy "posts_read" on public.community_posts for select
  using (
    coalesce(is_private, false) = false
    or auth.uid() = author_id
    or (auth.jwt() ->> 'email') = 'josephoh1611@gmail.com'
  );
