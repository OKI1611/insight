-- ============================================================
-- 수강생 질의응답 "토론(댓글)" 기능용 테이블
-- 적용 방법: Supabase 대시보드 → SQL Editor → 새 쿼리 → 아래 전체 붙여넣기 → Run
-- (한 번만 실행하면 됩니다. 이미 만들어졌다면 다시 실행해도 안전합니다.)
-- ============================================================

create table if not exists public.lecture_replies (
  id            uuid primary key default gen_random_uuid(),
  question_id   uuid not null references public.lecture_questions(id) on delete cascade,
  user_id       uuid not null references auth.users(id) on delete cascade,
  author_name   text,
  content       text not null,
  is_instructor boolean not null default false,
  created_at    timestamptz not null default now()
);

create index if not exists lecture_replies_qid_idx on public.lecture_replies(question_id);

alter table public.lecture_replies enable row level security;

-- 읽기: 공개 질문의 댓글은 누구나, 비밀 질문의 댓글은 본인·강사만
drop policy if exists "replies_read" on public.lecture_replies;
create policy "replies_read" on public.lecture_replies for select
using (
  exists (
    select 1 from public.lecture_questions q
    where q.id = question_id
      and ( q.is_private = false
            or q.user_id = auth.uid()
            or (auth.jwt() ->> 'email') = 'josephoh1611@gmail.com' )
  )
);

-- 작성: 로그인한 본인만 (남의 이름으로 작성 불가)
drop policy if exists "replies_insert" on public.lecture_replies;
create policy "replies_insert" on public.lecture_replies for insert
with check ( auth.uid() = user_id );

-- 삭제: 본인 또는 강사(관리자)
drop policy if exists "replies_delete" on public.lecture_replies;
create policy "replies_delete" on public.lecture_replies for delete
using ( auth.uid() = user_id or (auth.jwt() ->> 'email') = 'josephoh1611@gmail.com' );
