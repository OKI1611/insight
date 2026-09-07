-- ============================================================
-- Storage 개인정보 보안 조치 (2026-09-07)
-- 실행 방법: Supabase 대시보드 → SQL Editor → 전체 붙여넣고 Run
-- ============================================================
-- [배경 — 2026-09-07 실측으로 확인된 문제]
--   db/assignments.sql 의 asg_img_read 가
--       for select using (bucket_id = 'assignments')
--   처럼 **역할 제한 없이** 만들어져 있었다. 커뮤니티 버킷도 같은 형태였다.
--   그 결과 로그인하지 않은 사람이
--       POST /storage/v1/object/list/<버킷>
--   으로 **버킷 안 파일 이름을 전부 나열하고 그대로 내려받을 수** 있었다.
--   (당시 실제로 들어 있던 파일은 칼럼 이미지 7개·자료실 PDF 2개뿐이라
--    회원 개인정보 유출은 없었으나, 회원이 게시판 사진이나 과제 사진을
--    올리는 순간 그대로 공개되는 구조였다.)
--
-- [이 스크립트가 하는 일]
--   1) 과제 버킷(assignments)을 **비공개**로 전환한다.
--      → 과제 사진은 이제 서명 URL(만료 1시간)로만 열린다.
--        watch.html·admin.html 코드가 이미 서명 URL 방식으로 함께 수정되어 있다.
--   2) storage.objects 에서 community·assignments 를 가리키는 **기존 SELECT 정책을 전부 회수**한다.
--      → 익명 목록 조회(/object/list/)가 막힌다.
--   3) 과제 사진 SELECT 는 **본인 또는 관리자**에게만 다시 부여한다.
--
-- [화면에 미치는 영향 — 없음]
--   커뮤니티 버킷은 public 이라 이미 게시된 칼럼 이미지·자료실 PDF 는
--   /object/public/… 경로로 서비스되며, 이 경로는 RLS 를 타지 않는다.
--   따라서 SELECT 정책을 회수해도 기존 게시물은 그대로 보인다.
--   막히는 것은 '목록 조회'와 '탐색'뿐이다.
-- ============================================================

-- 1) 과제 버킷 비공개 전환 ------------------------------------
update storage.buckets set public = false where id = 'assignments';

-- 2) community · assignments 를 가리키는 기존 SELECT 정책 전량 회수 ----
--    (대시보드에서 손으로 만든 정책은 이름을 알 수 없으므로 이름을 훑어 지운다)
do $$
declare r record;
begin
  for r in
    select policyname
      from pg_policies
     where schemaname = 'storage'
       and tablename  = 'objects'
       and cmd = 'SELECT'
       and coalesce(qual, '') ~ '(community|assignments)'
  loop
    execute format('drop policy if exists %I on storage.objects', r.policyname);
    raise notice '회수한 SELECT 정책: %', r.policyname;
  end loop;
end $$;

-- 3) 과제 사진 읽기 = 본인 또는 관리자만 -----------------------
--    (경로 규칙: <auth.uid()>/<lesson_id>_<timestamp>.<ext>)
drop policy if exists asg_img_read on storage.objects;
create policy asg_img_read on storage.objects
  for select to authenticated using (
    bucket_id = 'assignments'
    and (
      (storage.foldername(name))[1] = auth.uid()::text
      or public.is_admin()
    )
  );

-- 4) 업로드 권한은 기존과 동일 — 로그인 사용자가 본인 폴더에만 -----
drop policy if exists asg_img_write on storage.objects;
create policy asg_img_write on storage.objects
  for insert to authenticated with check (
    bucket_id = 'assignments'
    and (storage.foldername(name))[1] = auth.uid()::text
  );

-- 5) 본인 과제 사진 교체(재제출) 허용 --------------------------
drop policy if exists asg_img_update on storage.objects;
create policy asg_img_update on storage.objects
  for update to authenticated using (
    bucket_id = 'assignments'
    and (storage.foldername(name))[1] = auth.uid()::text
  );

-- 6) 커뮤니티 버킷 업로드 권한 (없으면 생성) -------------------
--    읽기는 public 버킷의 /object/public/ 경로가 담당하므로 SELECT 정책은 두지 않는다.
drop policy if exists community_upload on storage.objects;
create policy community_upload on storage.objects
  for insert to authenticated with check ( bucket_id = 'community' );

-- ============================================================
-- 실행 후 확인 (익명 키로 호출했을 때 빈 배열이 아니라 권한 오류여야 정상)
--   curl -X POST 'https://<프로젝트>.supabase.co/storage/v1/object/list/community' \
--        -H 'apikey: <anon>' -H 'Authorization: Bearer <anon>' \
--        -H 'Content-Type: application/json' -d '{"prefix":"","limit":5}'
-- ============================================================
