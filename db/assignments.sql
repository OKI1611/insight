-- ============================================================
-- 과제 제출·피드백 (watch.html 제출 · mylearning.html 내 과제 · admin.html 첨삭)
-- 급수 인증 과목(유료 수강생) 전용. 강의별 고정 과제 1개.
-- Supabase 대시보드 → SQL Editor → New query → 붙여넣고 RUN.
-- 여러 번 실행해도 안전(idempotent).
-- ============================================================

-- 과제 제출물 (제출 + 강사 피드백을 한 행에 보관)
create table if not exists public.assignment_submissions (
  id          uuid primary key default gen_random_uuid(),
  user_id     uuid not null references auth.users(id) on delete cascade,
  lesson_id   text not null,                 -- 유튜브 영상 ID(강의 단위, 과제 키)
  track       text,                          -- 과목(트랙) 이름
  user_name   text,                          -- 표시용 이름(제출 시점 스냅샷)
  body        text not null,                 -- 과제 서술 내용
  image_url   text,                          -- 첨부 사진(Storage 공개 URL, 선택)
  status      text not null default 'submitted',  -- submitted | passed | revise
  feedback    text,                          -- 강사 첨삭
  reviewer    text,                          -- 첨삭한 관리자 이메일
  submitted_at timestamptz not null default now(),
  feedback_at  timestamptz,
  unique (user_id, lesson_id)                -- 강의당 1인 1제출(재제출은 update)
);

alter table public.assignment_submissions enable row level security;

-- 본인 제출: 읽기/쓰기 가능
drop policy if exists asg_select_own on public.assignment_submissions;
create policy asg_select_own on public.assignment_submissions
  for select using (auth.uid() = user_id);

drop policy if exists asg_insert_own on public.assignment_submissions;
create policy asg_insert_own on public.assignment_submissions
  for insert with check (auth.uid() = user_id);

-- 본인 수정: 아직 첨삭 전(submitted/revise)일 때만 본문 수정 허용
drop policy if exists asg_update_own on public.assignment_submissions;
create policy asg_update_own on public.assignment_submissions
  for update using (auth.uid() = user_id and status <> 'passed')
  with check (auth.uid() = user_id);

-- 관리자(대표강사): 전체 조회 + 첨삭(피드백/상태 변경)
-- ※ 관리자 이메일을 아래 두 정책에 동일하게 유지.
drop policy if exists asg_select_admin on public.assignment_submissions;
create policy asg_select_admin on public.assignment_submissions
  for select using (
    (auth.jwt() ->> 'email') = 'josephoh1611@gmail.com'
  );

drop policy if exists asg_update_admin on public.assignment_submissions;
create policy asg_update_admin on public.assignment_submissions
  for update using (
    (auth.jwt() ->> 'email') = 'josephoh1611@gmail.com'
  ) with check (
    (auth.jwt() ->> 'email') = 'josephoh1611@gmail.com'
  );

create index if not exists asg_lesson_idx on public.assignment_submissions (lesson_id);
create index if not exists asg_status_idx on public.assignment_submissions (status);

-- ============================================================
-- 사진 첨부용 Storage 버킷 (선택 기능)
-- 대시보드 → Storage → New bucket → 이름 "assignments" · Public 체크
-- (아래는 SQL로도 생성 가능. 이미 있으면 무시됨)
-- ============================================================
insert into storage.buckets (id, name, public)
values ('assignments', 'assignments', true)
on conflict (id) do nothing;

-- 로그인 사용자는 본인 폴더(user_id/…)에 업로드, 공개 읽기
drop policy if exists asg_img_read on storage.objects;
create policy asg_img_read on storage.objects
  for select using (bucket_id = 'assignments');

drop policy if exists asg_img_write on storage.objects;
create policy asg_img_write on storage.objects
  for insert to authenticated with check (
    bucket_id = 'assignments'
    and (storage.foldername(name))[1] = auth.uid()::text
  );
