-- ============================================================
-- BIBLY 개별 책자 구매 인증 테이블 — 1회만 실행
-- (전체 이용권은 pass_members, 낱권 구매는 이 테이블)
-- Supabase 대시보드 → SQL Editor 에 붙여넣고 Run
-- ============================================================

create table if not exists public.book_access (
  email       text not null,
  track       text not null,            -- 구매한 책(과정) 이름 = booklet 의 책 제목과 동일하게
  expires_at  timestamptz,              -- NULL = 영구 소장
  note        text,
  created_at  timestamptz default now(),
  primary key (email, track)
);

alter table public.book_access enable row level security;

-- 로그인한 본인의 구매 내역만 조회 가능
drop policy if exists "book self select" on public.book_access;
create policy "book self select" on public.book_access
  for select using ( auth.jwt() ->> 'email' = email );

-- 입금 확인 후 관리자가 부여(대시보드/SQL). track 은 책 제목과 정확히 일치해야 함.
--   insert into book_access (email, track)
--   values ('buyer@example.com', '기독교 기초 · 처음 만나는 신앙');
-- 환불 시:
--   delete from book_access where email='buyer@example.com' and track='기독교 기초 · 처음 만나는 신앙';
