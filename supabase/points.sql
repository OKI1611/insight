-- ============================================================
-- BIBLY 미션포인트 — 1회만 실행
-- 통독 체크·강의 수강·퀴즈 등에서 포인트를 적립(멱등: 같은 ref는 1회만).
-- Supabase 대시보드 → SQL Editor 에 붙여넣고 Run
-- ============================================================

create table if not exists public.user_points (
  user_id    uuid primary key references auth.users(id) on delete cascade,
  total      int not null default 0,
  updated_at timestamptz default now()
);

create table if not exists public.points_log (
  id         bigint generated always as identity primary key,
  user_id    uuid not null references auth.users(id) on delete cascade,
  amount     int not null,
  reason     text,
  ref        text,                      -- 멱등 키(같은 ref는 1회만 적립)
  created_at timestamptz default now()
);
-- 같은 사용자+ref 중복 적립 방지
create unique index if not exists points_log_user_ref_uniq
  on public.points_log(user_id, ref) where ref is not null;

alter table public.user_points enable row level security;
alter table public.points_log  enable row level security;

-- 본인 점수만 조회
drop policy if exists "user_points_select_own" on public.user_points;
create policy "user_points_select_own" on public.user_points for select using (auth.uid() = user_id);
drop policy if exists "points_log_select_own" on public.points_log;
create policy "points_log_select_own" on public.points_log for select using (auth.uid() = user_id);

-- 적립은 RPC(award_points)로만 — 직접 insert/update 불가(점수 조작 방지)

create or replace function award_points(p_amount int, p_reason text, p_ref text default null)
returns int language plpgsql security definer set search_path = public as $$
declare uid uuid; newtotal int;
begin
  uid := auth.uid();
  if uid is null or p_amount is null or p_amount <= 0 then
    select total into newtotal from public.user_points where user_id = uid; return coalesce(newtotal,0);
  end if;
  begin
    insert into public.points_log(user_id, amount, reason, ref) values (uid, p_amount, p_reason, p_ref);
  exception when unique_violation then
    select total into newtotal from public.user_points where user_id = uid; return coalesce(newtotal,0); -- 이미 적립됨
  end;
  insert into public.user_points(user_id, total, updated_at) values (uid, p_amount, now())
    on conflict (user_id) do update set total = public.user_points.total + p_amount, updated_at = now();
  select total into newtotal from public.user_points where user_id = uid;
  return coalesce(newtotal,0);
end; $$;

grant select on public.user_points, public.points_log to authenticated;
grant execute on function award_points(int,text,text) to authenticated;
