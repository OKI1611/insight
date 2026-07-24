-- =============================================================
-- 성경 번역 이야기(번역 노트) — 관리자 편집 테이블
-- 실행: Supabase 대시보드 → SQL Editor → New query → 전체 붙여넣기 → RUN
--
-- 동작 방식:
--   · 사이트의 기본 글은 content/translation-notes.json(코드)에 있습니다.
--   · 이 테이블의 행은 같은 id의 기본 글을 "덮어쓰기"하거나, 새 글을 "추가"합니다.
--   · hidden=true 로 저장하면 해당 글이 사이트에서 숨겨집니다.
--   · 관리자(admin.html → 번역 노트)에서 작성·수정하면 즉시 사이트에 반영됩니다.
-- =============================================================

create table if not exists public.translation_notes (
  id          text primary key,                 -- 글 슬러그 (예: prophesy, my-new-note)
  cat         text not null default 'verse',    -- principle(원칙·기법) | verse(구절 해설)
  title       text not null,
  verse       text not null default '',         -- 대표 구절 표시 (예: 요한복음 3:16)
  tags        jsonb not null default '[]',      -- ["원어","칭의"] 형태
  summary     text not null default '',
  body        jsonb not null default '[]',      -- [{"h":"소제목"}|{"p":"문단"}|{"v":"인용"}] 배열
  hidden      boolean not null default false,   -- true면 사이트에서 숨김
  sort        integer not null default 100000,  -- 목록 순서(작을수록 위)
  updated_at  timestamptz not null default now()
);

alter table public.translation_notes enable row level security;

-- 누구나 읽기(사이트 노출용)
drop policy if exists tn_select_all on public.translation_notes;
create policy tn_select_all on public.translation_notes
  for select using (true);

-- 관리자만 쓰기/수정/삭제
drop policy if exists tn_insert_admin on public.translation_notes;
create policy tn_insert_admin on public.translation_notes
  for insert with check ((auth.jwt() ->> 'email') = 'josephoh1611@gmail.com');

drop policy if exists tn_update_admin on public.translation_notes;
create policy tn_update_admin on public.translation_notes
  for update using ((auth.jwt() ->> 'email') = 'josephoh1611@gmail.com');

drop policy if exists tn_delete_admin on public.translation_notes;
create policy tn_delete_admin on public.translation_notes
  for delete using ((auth.jwt() ->> 'email') = 'josephoh1611@gmail.com');
