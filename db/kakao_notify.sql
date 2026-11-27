-- ============================================================
-- 알림(2026-11-27): 질문방 새 질문 → 강사 카카오톡 + 앱 푸시(새 강의·새 글) 구독
-- 적용: Supabase → SQL Editor → New query → 아래 전체 붙여넣기 → Run (한 번만, 다시 실행해도 안전)
--
-- notify_kv  : 카카오 토큰 등 서버 전용 값. RLS 를 켜고 정책을 하나도 두지 않아
--              브라우저(anon·로그인 사용자)는 읽기·쓰기 모두 불가, 서버(service_role)만 접근한다.
-- notify_log : 알림을 이미 보낸 글 기록(같은 글을 두 번 보내지 않게). 역시 서버 전용.
-- ============================================================

create table if not exists public.notify_kv (
  k          text primary key,
  v          text not null,
  updated_at timestamptz not null default now()
);
alter table public.notify_kv enable row level security;

create table if not exists public.notify_log (
  post_id uuid primary key,
  channel text not null default 'kakao',
  sent_at timestamptz not null default now()
);
alter table public.notify_log enable row level security;

-- 정책 없음 = anon/authenticated 접근 차단 (service_role 은 RLS 를 우회)
revoke all on public.notify_kv  from anon, authenticated;
revoke all on public.notify_log from anon, authenticated;

-- ============================================================
-- 앱 푸시 알림(새 강의·새 글) 구독 — 서버 전용 (worker/push.js)
-- ============================================================
create table if not exists public.push_subs (
  endpoint   text primary key,
  p256dh     text not null,
  auth       text not null,
  lang       text not null default 'ko',
  ua         text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
alter table public.push_subs enable row level security;
revoke all on public.push_subs from anon, authenticated;
