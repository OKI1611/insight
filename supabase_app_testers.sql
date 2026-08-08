-- ============================================================
-- 앱 테스터 신청(tester.html)용 Supabase 테이블 + 보안정책
-- 사용법: Supabase 대시보드 → SQL Editor → 아래 전체 붙여넣고 RUN
--
-- 신청 페이지는 로그인 없이 누구나 신청할 수 있고(구글 플레이 비공개 테스트 모집),
-- 명단 조회·상태변경은 관리자만 가능하도록 막는다.
-- ============================================================

-- 1) 신청자 테이블
create table if not exists public.app_testers (
  id         bigserial primary key,
  created_at timestamptz not null default now(),
  gmail      text not null,                    -- 플레이 콘솔 테스터 등록에 쓸 구글 계정
  name       text,
  phone      text,
  book       text,                             -- 완주 선물로 고를 책
  memo       text,
  status     text not null default 'pending'   -- pending(접수) / invited(초대발송) / installed(설치확인) / done(완주) / dropped(이탈)
);

-- 같은 Gmail 중복 신청 방지 (대소문자 무시)
create unique index if not exists app_testers_gmail_uniq
  on public.app_testers (lower(gmail));

-- 최신순 조회 성능
create index if not exists app_testers_created_idx
  on public.app_testers (created_at desc);

-- 2) RLS(행 수준 보안) 활성화
alter table public.app_testers enable row level security;

-- 3) 정책 (재실행 안전: 기존 정책 있으면 먼저 제거)
drop policy if exists "app_testers_insert_anyone" on public.app_testers;
drop policy if exists "app_testers_select_admin" on public.app_testers;
drop policy if exists "app_testers_update_admin" on public.app_testers;
drop policy if exists "app_testers_delete_admin" on public.app_testers;

-- 신청: 누구나 가능(로그인 불필요). 단 status 는 항상 'pending' 으로만 등록되게 강제.
create policy "app_testers_insert_anyone" on public.app_testers
  for insert with check (status = 'pending');

-- 조회·수정·삭제: 관리자만 (개인정보 보호 — 익명 조회 차단)
create policy "app_testers_select_admin" on public.app_testers
  for select using ((auth.jwt() ->> 'email') = 'josephoh1611@gmail.com');
create policy "app_testers_update_admin" on public.app_testers
  for update using      ((auth.jwt() ->> 'email') = 'josephoh1611@gmail.com')
              with check ((auth.jwt() ->> 'email') = 'josephoh1611@gmail.com');
create policy "app_testers_delete_admin" on public.app_testers
  for delete using ((auth.jwt() ->> 'email') = 'josephoh1611@gmail.com');

-- ============================================================
-- 확인용 쿼리 (SQL Editor 에서 따로 실행)
--   select count(*) from public.app_testers;                       -- 접수 인원
--   select gmail, name, phone, book, status, created_at            -- 명단(플레이 콘솔 붙여넣기용)
--     from public.app_testers order by created_at;
--   select string_agg(gmail, E'\n') from public.app_testers;       -- Gmail 만 줄바꿈으로
-- ============================================================
