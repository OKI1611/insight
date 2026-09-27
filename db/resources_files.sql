-- ============================================================
-- 자료실(resources.html) — 첨부 파일 여러 개(최대 5개) 저장 칸
-- 사용법: Supabase 대시보드 → SQL Editor → New query → 아래 전체 붙여넣고 RUN
-- 안전: 여러 번 실행해도 됩니다(idempotent).
-- 선행: db/setup.sql 의 resources 테이블이 있어야 함.
-- ============================================================

-- 첨부 목록을 통째로 담는 칸 — [{"url":"...","name":"원래이름.pdf","size":"1.2MB"}, ...]
-- 옛 자료의 file_url/file_name 은 그대로 두고(호환), 새 저장부터 이 칸을 함께 씁니다.
alter table public.resources add column if not exists files jsonb;
