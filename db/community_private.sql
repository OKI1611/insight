-- ============================================================
-- 신앙상담(비공개 1:1) + 비공개 기도요청 — 진짜 비공개 보안(RLS)
-- 적용: Supabase → SQL Editor → New query → 아래 전체 붙여넣기 → Run
-- (한 번만 실행, 다시 실행해도 안전. 기존 community.sql 위에 덮어쓰는 보강분)
--
-- 핵심: board='counsel'(신앙상담) 글과 그 댓글은 '작성한 본인 + 관리자'만 조회 가능.
--       is_private=true 기도요청도 동일하게 본인+관리자만. 그 외 공개글은 누구나.
-- ※ 프론트에서 숨기는 것만으로는 anon 키로 조회되므로, 반드시 RLS로 막아야 함.
-- ============================================================

-- is_private 컬럼이 없으면 추가
alter table public.community_posts
  add column if not exists is_private boolean not null default false;

-- 1) 게시글 읽기 정책 -----------------------------------------
--    공개글(비-counsel & is_private=false)은 누구나, 비공개는 작성자/관리자만
drop policy if exists "posts_read" on public.community_posts;
create policy "posts_read" on public.community_posts for select using (
  ( board <> 'counsel' and coalesce(is_private, false) = false )
  or auth.uid() = author_id
  or (auth.jwt() ->> 'email') = 'josephoh1611@gmail.com'
);

-- 2) 댓글 읽기 정책 -------------------------------------------
--    부모 글을 볼 수 있는 사람만 그 댓글을 볼 수 있음(신앙상담 답변=본인/관리자만)
drop policy if exists "comments_read" on public.community_comments;
create policy "comments_read" on public.community_comments for select using (
  (auth.jwt() ->> 'email') = 'josephoh1611@gmail.com'
  or exists (
    select 1 from public.community_posts p
    where p.id = community_comments.post_id
      and ( ( p.board <> 'counsel' and coalesce(p.is_private, false) = false )
            or p.author_id = auth.uid() )
  )
);

-- 3) 댓글 작성 정책 -------------------------------------------
--    자기 이름으로, 자신이 볼 수 있는 글에만(=비공개 상담엔 본인/관리자만 답글)
drop policy if exists "comments_insert" on public.community_comments;
create policy "comments_insert" on public.community_comments for insert with check (
  auth.uid() = author_id
  and (
    (auth.jwt() ->> 'email') = 'josephoh1611@gmail.com'
    or exists (
      select 1 from public.community_posts p
      where p.id = post_id
        and ( ( p.board <> 'counsel' and coalesce(p.is_private, false) = false )
              or p.author_id = auth.uid() )
    )
  )
);

-- (게시글 insert/delete, 댓글 delete 정책은 기존 community.sql 그대로 유효:
--  insert= 본인만, delete= 본인 또는 관리자)
-- ============================================================
-- 적용 후 확인: 신앙상담(🔒) 탭에서 본인 글만 보이고, 로그아웃 시 안 보이면 정상.
