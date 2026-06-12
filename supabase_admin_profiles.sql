-- ============================================================
-- 관리자 콘솔(admin.html) — 전체 회원·수강·진도 조회 권한
-- 기존 '본인 행만 조회' 정책은 그대로 두고, 관리자 이메일에 한해
-- 전체 SELECT 권한을 '추가'합니다. (RLS 정책은 OR로 합쳐지므로 안전)
-- 사용법: Supabase 대시보드 → SQL Editor → 아래 전체 붙여넣고 RUN
-- ============================================================

-- 회원 기본정보(이름)
drop policy if exists "profiles_admin_select_all" on public.profiles;
create policy "profiles_admin_select_all" on public.profiles for select
  using ((auth.jwt() ->> 'email') = 'josephoh1611@gmail.com');

-- 수강신청 내역
drop policy if exists "enrollments_admin_select_all" on public.enrollments;
create policy "enrollments_admin_select_all" on public.enrollments for select
  using ((auth.jwt() ->> 'email') = 'josephoh1611@gmail.com');

-- 학습 진도
drop policy if exists "lesson_progress_admin_select_all" on public.lesson_progress;
create policy "lesson_progress_admin_select_all" on public.lesson_progress for select
  using ((auth.jwt() ->> 'email') = 'josephoh1611@gmail.com');

-- 참고: 이메일·연락처는 auth.users에 있어 이 정책으로도 조회되지 않습니다(보안 정상).
--       회원 이름은 가입 시 profiles.full_name 에 저장된 값이 표시됩니다.
