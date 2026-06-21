-- ============================================================
-- BIBLY 자료 이용기록(열람·다운로드 로그) — 1회만 실행
-- 환불 분쟁 시 "구매자가 실제로 다운로드/열람했다"는 증거가 됩니다.
-- (한국 전자상거래법: 디지털 콘텐츠는 다운로드·열람 시 청약철회 제한 가능)
-- 전제: supabase/store_grant.sql 의 _is_store_admin() 가 먼저 있어야 함.
-- Supabase 대시보드 → SQL Editor 에 붙여넣고 Run
-- ============================================================

create table if not exists public.access_logs (
  id         bigint generated always as identity primary key,
  email      text not null,
  kind       text,                 -- 'pass'(전체 이용권) | 'book'(개별 교재)
  track      text,                 -- 열람/다운로드한 책(과정) 이름
  action     text,                 -- 'view'(열람) | 'download'(PDF 저장)
  created_at timestamptz default now()
);

alter table public.access_logs enable row level security;
-- 직접 insert/select은 막고(스푸핑·노출 방지), 아래 RPC로만 접근.

-- 로그인한 본인 행을 기록(이메일은 JWT에서 가져와 위조 불가)
create or replace function log_access(p_kind text, p_track text, p_action text)
returns void language plpgsql security definer as $$
declare em text;
begin
  em := auth.jwt() ->> 'email';
  if em is null or em = '' then return; end if;
  insert into public.access_logs(email, kind, track, action)
  values (lower(em), p_kind, p_track, p_action);
end; $$;

-- 관리자만 전체 기록 조회
create or replace function list_access(p_limit int default 300)
returns setof public.access_logs language sql security definer as $$
  select * from public.access_logs
  where _is_store_admin()
  order by created_at desc
  limit coalesce(p_limit, 300);
$$;

grant execute on function log_access(text,text,text), list_access(int) to anon, authenticated;
