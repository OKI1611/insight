-- ============================================================
-- BIBLY 아카데미 인증 과정 — 수강권(잠금 해제) 테이블
-- Supabase 대시보드 → SQL Editor → New query → 붙여넣고 RUN (여러 번 실행해도 안전)
-- 결제(계좌이체) 확인 후, 관리자가 이 표에 행을 넣어 수강권을 부여합니다.
--   tier: 1=여명(3급) · 2=통찰(2급) · 3=파수(1급). 상위 등급은 하위 과정을 포함합니다.
--   부여 예: insert into cert_access(user_id, tier, package) values ('<유저UUID>', 1, '여명');
-- ============================================================
create table if not exists public.cert_access (
  user_id    uuid primary key references auth.users(id) on delete cascade,
  tier       int not null default 0,    -- 0=없음, 1=여명, 2=통찰, 3=파수
  package    text,                       -- 부여된 패키지명
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
