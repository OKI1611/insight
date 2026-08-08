-- ============================================================
-- app_testers 상태값 정정 + 테스트 데이터 정리
-- 사용법: Supabase 대시보드 → SQL Editor → 아래 전체 붙여넣고 RUN
--
-- 문제: 최초 SQL의 기본값이 'pending' 이었는데, 관리자 화면(tester.html)이 쓰는
--       상태값은 applied / registered / installed / done / dropped 라서 어긋났음.
--       (신규 신청자가 DB엔 pending 인데 화면엔 '신청'으로 보이는 불일치)
-- 조치: DB를 이미 배포된 화면 기준으로 맞춘다.
-- ============================================================

-- 1) 기본값을 화면과 동일하게 'applied'(신청)로 변경
alter table public.app_testers alter column status set default 'applied';

-- 2) 기존에 'pending' 으로 저장된 행을 'applied' 로 통일
update public.app_testers set status = 'applied' where status = 'pending';

-- 3) 신청(INSERT) 정책도 새 기본값 기준으로 갱신
--    (신청자는 항상 '신청' 상태로만 등록되게 하고, 완주/등록 등으로 조작 불가)
drop policy if exists "app_testers_insert_anyone" on public.app_testers;
create policy "app_testers_insert_anyone" on public.app_testers
  for insert with check (status = 'applied');

-- 4) 점검하느라 넣은 테스트 데이터 삭제
delete from public.app_testers
 where gmail ilike '__selftest%' or gmail ilike '__rlscheck%';

-- ============================================================
-- 실행 후 확인 (아래 두 줄을 따로 실행해 보세요)
--   select count(*) from public.app_testers;                  -- 실제 신청 인원
--   select status, count(*) from public.app_testers group by status;  -- 상태별 분포
-- ============================================================
