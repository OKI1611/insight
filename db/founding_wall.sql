-- =============================================================
-- 1기 창립 멤버 "명예의 전당" 공개용 함수
-- 실행: Supabase 대시보드 → SQL Editor → New query → 전체 붙여넣기 → RUN
--
-- 개인정보 보호:
--   · 이 함수는 '가려진 이름'과 '멤버 번호'만 돌려줍니다. (예: 홍*동 / #001)
--   · 실명·이메일·전화·주소는 서버 밖으로 나가지 않습니다.
--   · 가리는 작업을 서버(데이터베이스) 안에서 하므로, 브라우저로는 원본이 전송되지 않습니다.
--
-- 이 함수를 실행하기 전까지 홈페이지의 명예의 전당은 자동으로 숨겨집니다(오류 없음).
-- =============================================================

-- 이름 가리기: 1글자 → *  /  2글자 → 김*  /  3글자 이상 → 홍*동, 남궁**수
create or replace function public.mask_name(p text)
returns text language sql immutable as $$
  select case
    when coalesce(btrim(p),'') = '' then '창립멤버'
    when char_length(btrim(p)) = 1 then '*'
    when char_length(btrim(p)) = 2 then left(btrim(p),1) || '*'
    else left(btrim(p),1)
         || repeat('*', char_length(btrim(p)) - 2)
         || right(btrim(p),1)
  end;
$$;

-- 공개 명단: 가려진 이름 + 멤버 번호만
create or replace function public.founding_wall()
returns table (member_no int, masked_name text)
language sql
security definer
set search_path = public
as $$
  select member_no, public.mask_name(name)
  from public.founding_members
  where member_no is not null
  order by member_no;
$$;

-- 로그인하지 않은 방문자도 볼 수 있게 실행 권한 부여
grant execute on function public.mask_name(text)  to anon, authenticated;
grant execute on function public.founding_wall()  to anon, authenticated;
