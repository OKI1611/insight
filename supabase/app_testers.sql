-- ============================================================
-- 앱 테스터 신청 명단 — 1회만 실행
-- 누구나 신청(insert), 본인 확인 불가(개인정보 보호로 select는 관리자만).
-- Supabase 대시보드 → SQL Editor 에 붙여넣고 Run
-- ============================================================

create table if not exists public.app_testers (
  id         bigint generated always as identity primary key,
  gmail      text not null,                       -- 콘솔 테스터 목록에 넣을 구글 계정
  name       text,                                -- 선물 배송용 이름(선택)
  phone      text,                                -- 연락처(선택)
  memo       text,                                -- 남기고 싶은 말
  status     text not null default 'applied',     -- applied(신청) | registered(콘솔등록) | installed(설치확인) | done(완주) | dropped(이탈)
  book       text,                                -- 완주 선물로 고른 책
  address    text,                                -- 선물 배송지(완주 후 수집)
  created_at timestamptz default now()
);

create unique index if not exists app_testers_gmail_uniq on public.app_testers (lower(gmail));

alter table public.app_testers enable row level security;

-- 누구나 신청 가능(insert만) — 명단 열람은 불가
drop policy if exists "app_testers_insert_all" on public.app_testers;
create policy "app_testers_insert_all" on public.app_testers for insert with check (true);

-- 관리자만 열람/수정/삭제
drop policy if exists "app_testers_admin_select" on public.app_testers;
create policy "app_testers_admin_select" on public.app_testers for select
  using ((auth.jwt() ->> 'email') = 'josephoh1611@gmail.com');

drop policy if exists "app_testers_admin_update" on public.app_testers;
create policy "app_testers_admin_update" on public.app_testers for update
  using ((auth.jwt() ->> 'email') = 'josephoh1611@gmail.com');

drop policy if exists "app_testers_admin_delete" on public.app_testers;
create policy "app_testers_admin_delete" on public.app_testers for delete
  using ((auth.jwt() ->> 'email') = 'josephoh1611@gmail.com');

grant insert on public.app_testers to anon, authenticated;
grant select, update, delete on public.app_testers to authenticated;
