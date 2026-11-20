-- ═══════════════════════════════════════════════════════════════════
-- A.W.F 자동수익 퍼널 테이블 (2026-11-21)
-- 실행 방법: Supabase 대시보드 → SQL Editor 에 전체를 붙여넣고 Run 한 번.
-- 두 테이블 모두 RLS로 외부 접근을 전부 막는다 — Worker(service_role)만 읽고 쓴다.
-- ═══════════════════════════════════════════════════════════════════

-- 1) 마케팅 리드 — 옵트인(무료특강·PDF 신청)과 심화과정 상담 신청을 모은다
create table if not exists public.marketing_leads (
  id          bigint generated always as identity primary key,
  email       text not null unique,
  name        text,
  topic       text,                      -- 옵트인 당시 주제(start.html ?t=)
  src         text,                      -- 유입 경로(?src=)
  kind        text not null default 'optin',          -- optin | consult
  note        text,                      -- 상담 신청서 답변(JSON 문자열)
  status      text not null default 'active',         -- active | unsubscribed | converted
  unsub_token text,                      -- 수신거부 링크 토큰
  created_at  timestamptz not null default now()
);
create index if not exists marketing_leads_status_idx on public.marketing_leads (status);
create index if not exists marketing_leads_kind_idx   on public.marketing_leads (kind);

-- 2) 이메일 발송 큐 — 리드별 육성 시퀀스 예약(n1~n7)·상담 접수 확인(c1)
create table if not exists public.email_queue (
  id         bigint generated always as identity primary key,
  lead_id    bigint not null references public.marketing_leads(id) on delete cascade,
  step       text   not null,            -- n1~n7 | c1
  due_at     timestamptz not null,
  sent_at    timestamptz,
  skipped    boolean default false,
  tries      int not null default 0,
  last_error text,
  created_at timestamptz not null default now()
);
create index if not exists email_queue_due_idx on public.email_queue (due_at) where sent_at is null;

-- 3) RLS — 전부 잠근다(허용 정책 없음). service_role 은 RLS 를 통과하므로 Worker 만 접근 가능.
alter table public.marketing_leads enable row level security;
alter table public.email_queue     enable row level security;
