-- ============================================================
-- 완주자 선물 배송지 수집(tester-gift.html)용 컬럼 + 전용 함수
-- 사용법: Supabase 대시보드 → SQL Editor → 아래 전체 붙여넣고 RUN
--
-- 설계 의도:
--   배송지 입력은 로그인 없이 해야 하는데, 익명에게 UPDATE 권한을 열어 주면
--   남의 신청 상태(완주 등)까지 바꿀 수 있어 위험하다.
--   그래서 UPDATE 권한은 계속 관리자만 갖고, 배송지 항목만 건드리는
--   전용 함수(submit_tester_gift)를 만들어 그 함수만 호출하게 한다.
-- ============================================================

-- 1) 배송지 컬럼 추가 (이미 있으면 건너뜀)
alter table public.app_testers add column if not exists ship_name         text;
alter table public.app_testers add column if not exists ship_phone        text;
alter table public.app_testers add column if not exists ship_address      text;
alter table public.app_testers add column if not exists gift_book         text;
alter table public.app_testers add column if not exists gift_memo         text;
alter table public.app_testers add column if not exists gift_submitted_at timestamptz;

-- 2) 배송지 제출 전용 함수
--    - 신청한 Gmail 이 있어야만 저장됨(없으면 오류)
--    - 배송지 관련 항목만 수정하고, status 등 다른 값은 절대 건드리지 않음
create or replace function public.submit_tester_gift(
  p_gmail   text,
  p_name    text,
  p_phone   text,
  p_address text,
  p_book    text,
  p_memo    text default null
) returns void
language plpgsql
security definer
set search_path = public
as $$
declare
  v_id bigint;
begin
  select id into v_id
    from public.app_testers
   where lower(gmail) = lower(btrim(p_gmail))
   limit 1;

  if v_id is null then
    raise exception 'not found: 신청 내역을 찾을 수 없습니다';
  end if;

  update public.app_testers
     set ship_name         = btrim(p_name),
         ship_phone        = btrim(p_phone),
         ship_address      = btrim(p_address),
         gift_book         = p_book,
         gift_memo         = p_memo,
         gift_submitted_at = now()
   where id = v_id;
end;
$$;

-- 3) 로그인 없이도 이 함수만은 부를 수 있게 허용
grant execute on function public.submit_tester_gift(text,text,text,text,text,text) to anon, authenticated;

-- ============================================================
-- 확인용 (따로 실행)
--   -- 배송지 제출한 사람 목록
--   select gmail, ship_name, ship_phone, ship_address, gift_book, gift_submitted_at
--     from public.app_testers
--    where gift_submitted_at is not null
--    order by gift_submitted_at;
--
--   -- 완주했는데 아직 배송지 안 낸 사람
--   select gmail, name from public.app_testers
--    where status = 'done' and gift_submitted_at is null;
-- ============================================================
