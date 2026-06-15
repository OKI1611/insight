-- ============================================================
-- BIBLY 바이블 인사이트 — 기능 활성화 SQL
-- 사용법: Supabase 대시보드 → SQL Editor → New query → 아래 전체 붙여넣고 RUN
-- 안전: 여러 번 실행해도 됩니다(idempotent). 이미 있는 테이블/정책은 건너뜁니다.
-- 관리자 계정 = josephoh1611@gmail.com
-- ============================================================

-- 관리자 판별 헬퍼 (로그인 이메일이 관리자면 true)
create or replace function public.is_admin()
returns boolean language sql stable as $$
  select coalesce(auth.jwt() ->> 'email', '') = 'josephoh1611@gmail.com'
$$;

-- ── 1) 강의 요청 · 건의함 (request.html) ──────────────────────
create table if not exists public.lecture_requests (
  id          uuid primary key default gen_random_uuid(),
  type        text not null default 'request',   -- request(강의요청) | feedback(건의)
  title       text not null,
  body        text,
  author_id   uuid references auth.users(id) on delete set null,
  author_name text,
  status      text not null default '접수',        -- 접수 | 검토중 | 반영예정 | 완료
  admin_reply text,
  created_at  timestamptz not null default now()
);
alter table public.lecture_requests enable row level security;
drop policy if exists lr_select on public.lecture_requests;
create policy lr_select on public.lecture_requests for select using (true);
drop policy if exists lr_insert on public.lecture_requests;
create policy lr_insert on public.lecture_requests for insert with check (auth.uid() = author_id);
drop policy if exists lr_update on public.lecture_requests;
create policy lr_update on public.lecture_requests for update using (public.is_admin()) with check (public.is_admin());
drop policy if exists lr_delete on public.lecture_requests;
create policy lr_delete on public.lecture_requests for delete using (public.is_admin() or auth.uid() = author_id);

create table if not exists public.lecture_request_votes (
  request_id uuid references public.lecture_requests(id) on delete cascade,
  user_id    uuid references auth.users(id) on delete cascade,
  created_at timestamptz not null default now(),
  primary key (request_id, user_id)
);
alter table public.lecture_request_votes enable row level security;
drop policy if exists lrv_select on public.lecture_request_votes;
create policy lrv_select on public.lecture_request_votes for select using (true);
drop policy if exists lrv_insert on public.lecture_request_votes;
create policy lrv_insert on public.lecture_request_votes for insert with check (auth.uid() = user_id);
drop policy if exists lrv_delete on public.lecture_request_votes;
create policy lrv_delete on public.lecture_request_votes for delete using (auth.uid() = user_id);

-- ── 2) 수강신청 · 내 강의실 (watch.html, mylearning.html) ─────
create table if not exists public.enrollments (
  user_id    uuid not null references auth.users(id) on delete cascade,
  track      text not null,
  created_at timestamptz not null default now(),
  primary key (user_id, track)
);
alter table public.enrollments enable row level security;
drop policy if exists enr_select on public.enrollments;
create policy enr_select on public.enrollments for select using (auth.uid() = user_id);
drop policy if exists enr_insert on public.enrollments;
create policy enr_insert on public.enrollments for insert with check (auth.uid() = user_id);
drop policy if exists enr_delete on public.enrollments;
create policy enr_delete on public.enrollments for delete using (auth.uid() = user_id);

create table if not exists public.lesson_progress (
  user_id    uuid not null references auth.users(id) on delete cascade,
  lesson_id  text not null,        -- 유튜브 영상 ID
  track      text,
  created_at timestamptz not null default now(),
  primary key (user_id, lesson_id) -- 행 존재 = 학습완료, 삭제 = 미완료
);
alter table public.lesson_progress enable row level security;
drop policy if exists lp_select on public.lesson_progress;
create policy lp_select on public.lesson_progress for select using (auth.uid() = user_id);
drop policy if exists lp_insert on public.lesson_progress;
create policy lp_insert on public.lesson_progress for insert with check (auth.uid() = user_id);
drop policy if exists lp_update on public.lesson_progress;
create policy lp_update on public.lesson_progress for update using (auth.uid() = user_id) with check (auth.uid() = user_id);
drop policy if exists lp_delete on public.lesson_progress;
create policy lp_delete on public.lesson_progress for delete using (auth.uid() = user_id);

-- ── 3) 강의 인라인 질의응답 (watch.html) ─────────────────────
create table if not exists public.lecture_questions (
  id          uuid primary key default gen_random_uuid(),
  lesson_id   text not null,        -- 유튜브 영상 ID
  user_id     uuid references auth.users(id) on delete set null,
  author_name text,
  content     text not null,
  is_private  boolean not null default false,  -- 비밀질문(강사·본인만)
  answer      text,                 -- 강사 답변
  answered_at timestamptz,
  created_at  timestamptz not null default now()
);
alter table public.lecture_questions enable row level security;
drop policy if exists lq_select on public.lecture_questions;
create policy lq_select on public.lecture_questions for select
  using ( is_private = false or auth.uid() = user_id or public.is_admin() );
drop policy if exists lq_insert on public.lecture_questions;
create policy lq_insert on public.lecture_questions for insert with check (auth.uid() = user_id);
drop policy if exists lq_update on public.lecture_questions;
create policy lq_update on public.lecture_questions for update
  using ( public.is_admin() or auth.uid() = user_id )
  with check ( public.is_admin() or auth.uid() = user_id );
drop policy if exists lq_delete on public.lecture_questions;
create policy lq_delete on public.lecture_questions for delete
  using ( public.is_admin() or auth.uid() = user_id );

-- ── 4) 커뮤니티 보드 컬럼 (자유나눔/질의응답/기도요청 탭) ───────
-- community_posts 가 이미 있다는 전제(커뮤니티 사용 중). 없으면 이 줄은 건너뛰세요.
alter table public.community_posts add column if not exists board text not null default 'free';

-- ── 5) 정규 심화 과정 사전 신청 (academy.html) ──────────────────
create table if not exists public.course_applications (
  id          uuid primary key default gen_random_uuid(),
  name        text,
  email       text not null,
  phone       text,
  interest    text,        -- 관심 과정/트랙
  motivation  text,        -- 신청 동기·질문
  created_at  timestamptz not null default now()
);
alter table public.course_applications enable row level security;
drop policy if exists ca_insert on public.course_applications;
create policy ca_insert on public.course_applications for insert with check (true);   -- 비로그인 사전신청 허용(대기명단)
drop policy if exists ca_select on public.course_applications;
create policy ca_select on public.course_applications for select using (public.is_admin());
drop policy if exists ca_delete on public.course_applications;
create policy ca_delete on public.course_applications for delete using (public.is_admin());

-- ── 6) 수료 시험 결과 · 학점 (exam.html, mylearning.html) ──────
create table if not exists public.exam_results (
  user_id     uuid not null references auth.users(id) on delete cascade,
  lesson_id   text not null,        -- 유튜브 영상 ID (강의 단위)
  track       text,                 -- 과목(트랙) 이름
  attempt1    int,                  -- 1차 점수 (0~100)
  attempt2    int,                  -- 2차 점수 (0~100, 미응시면 null)
  final_score numeric,              -- 최종 점수 (1차 통과=1차점수 / 2차=1차*0.6+2차*0.4)
  passed      boolean not null default false,
  updated_at  timestamptz not null default now(),
  primary key (user_id, lesson_id)
);
alter table public.exam_results enable row level security;
drop policy if exists ex_select on public.exam_results;
create policy ex_select on public.exam_results for select using (auth.uid() = user_id);
drop policy if exists ex_insert on public.exam_results;
create policy ex_insert on public.exam_results for insert with check (auth.uid() = user_id);
drop policy if exists ex_update on public.exam_results;
create policy ex_update on public.exam_results for update using (auth.uid() = user_id) with check (auth.uid() = user_id);
drop policy if exists ex_delete on public.exam_results;
create policy ex_delete on public.exam_results for delete using (auth.uid() = user_id);

-- ── 7) BIBLY 아카데미 인증 과정 수강권 (잠금 해제) ──────────────
-- 결제(계좌이체) 확인 후 관리자가 행을 넣어 수강권 부여. tier 1=여명·2=통찰·3=파수.
create table if not exists public.cert_access (
  user_id    uuid primary key references auth.users(id) on delete cascade,
  tier       int not null default 0,
  package    text,
  note       text,
  granted_at timestamptz not null default now()
);
alter table public.cert_access enable row level security;
drop policy if exists cert_sel on public.cert_access;
create policy cert_sel on public.cert_access for select using (auth.uid() = user_id or public.is_admin());
drop policy if exists cert_ins on public.cert_access;
create policy cert_ins on public.cert_access for insert with check (public.is_admin());
drop policy if exists cert_upd on public.cert_access;
create policy cert_upd on public.cert_access for update using (public.is_admin()) with check (public.is_admin());
drop policy if exists cert_del on public.cert_access;
create policy cert_del on public.cert_access for delete using (public.is_admin());

-- ============================================================
-- 끝! 이제 강의요청·건의, 수강신청·내강의실, 강의 질의응답, 커뮤니티 탭,
--     정규과정 사전신청, 수료 시험·학점, 인증 과정 수강권이 작동합니다.
-- ============================================================
