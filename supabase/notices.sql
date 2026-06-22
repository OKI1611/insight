-- ============================================================
-- BIBLY 공지사항 · 이벤트 게시판 — 1회만 실행
-- 관리자(josephoh1611@gmail.com)만 작성/수정/삭제, 누구나 읽기.
-- Supabase 대시보드 → SQL Editor 에 붙여넣고 Run
-- ============================================================

create table if not exists public.notices (
  id         bigint generated always as identity primary key,
  kind       text not null default 'notice',     -- 'notice'(공지) | 'event'(이벤트)
  title      text not null,
  body       text,                                -- 본문(마크다운/플레인)
  pinned     boolean not null default false,      -- 상단 고정
  created_at timestamptz default now()
);

alter table public.notices enable row level security;

-- 누구나 읽기
drop policy if exists "notices_read_all" on public.notices;
create policy "notices_read_all" on public.notices for select using (true);

-- 관리자만 작성/수정/삭제 (JWT 이메일로 판별)
drop policy if exists "notices_admin_insert" on public.notices;
create policy "notices_admin_insert" on public.notices for insert
  with check ((auth.jwt() ->> 'email') = 'josephoh1611@gmail.com');

drop policy if exists "notices_admin_update" on public.notices;
create policy "notices_admin_update" on public.notices for update
  using ((auth.jwt() ->> 'email') = 'josephoh1611@gmail.com');

drop policy if exists "notices_admin_delete" on public.notices;
create policy "notices_admin_delete" on public.notices for delete
  using ((auth.jwt() ->> 'email') = 'josephoh1611@gmail.com');

grant select on public.notices to anon, authenticated;
grant insert, update, delete on public.notices to authenticated;

-- 첫 안내 글(샘플) — 원하면 삭제하세요
insert into public.notices (kind, title, body, pinned)
values ('notice', 'BIBLY에 오신 것을 환영합니다 🙏',
  '말씀으로 시대를 읽는 BIBLY입니다. 전 강의 무료로 공개되어 있으니 마음껏 배우세요. 새 소식은 이 공지에서 전해드립니다.', true)
on conflict do nothing;
