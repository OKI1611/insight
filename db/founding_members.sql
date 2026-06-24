-- 🎖️ 1기 창립 멤버 신청 데이터
-- founding.html 신청서 → Supabase 저장(+Web3Forms 관리자 메일은 별도로 항상 발송).
-- Supabase SQL Editor에서 1회 실행. (이 표가 없어도 신청은 메일로 접수되므로 사이트는 정상 동작)

create table if not exists public.founding_members (
  id           bigint generated always as identity primary key,
  created_at   timestamptz not null default now(),
  name         text not null,
  email        text not null,
  phone        text,
  region       text,
  church       text,
  faith_years  text,          -- 신앙 연수
  motivation   text,          -- 가입 동기
  ideal_church text,          -- 꿈꾸는 교회상
  ideal_pastor text,          -- 바라는 목회자상
  prayer       text,          -- 기도 제목
  promise      boolean default false  -- 홍보(전도) 약속 동의
);

alter table public.founding_members enable row level security;

-- 누구나(비로그인 포함) 신청서를 제출(insert)할 수 있게 허용. 읽기는 막아 둠(관리자는 대시보드/서비스롤로 조회).
drop policy if exists "founding insert anyone" on public.founding_members;
create policy "founding insert anyone" on public.founding_members
  for insert with check (true);

-- (읽기 정책은 의도적으로 만들지 않음 → anon 키로는 조회 불가, 개인정보 보호)
-- 관리자는 Supabase 대시보드 Table Editor 또는 service_role 로 확인.
