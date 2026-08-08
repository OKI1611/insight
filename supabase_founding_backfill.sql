-- ============================================================
-- 창립 멤버 혜택 점검 · 소급 적용
--
--   신청은 apply_founding(..., p_months) 가 처리하고 있습니다.
--   다만 신청 당시 통신 오류·타임아웃 등으로 폴백 경로(직접 insert)만 성공해
--   명단(founding_members)에는 있는데 1년 이용권(member_access)이 없는 분이
--   생길 수 있습니다. 그런 분을 찾아 채워 넣는 점검용 SQL입니다.
--
--   [1] 조회만으로 문제 유무를 먼저 확인하고, ⚠ 가 없으면 실행할 필요 없습니다.
--
--   ※ 회원가입을 아직 안 하신 분은 소급 대상이 아닙니다 —
--     로그인하는 순간 claim_founding() 이 자동으로 활성화해 줍니다.
--
--   실행 순서: [1] 로 대상 확인 → [2] 로 적용 → [3] 으로 결과 확인
-- ============================================================


-- ------------------------------------------------------------
-- [1] 먼저 확인만 — 누가 혜택을 못 받고 있는지 (아무것도 바꾸지 않음)
-- ------------------------------------------------------------
select
  f.member_no                                        as "창립번호",
  f.name                                             as "이름",
  f.email                                            as "이메일",
  f.joined_at::date                                  as "신청일",
  case when u.id is null then '가입 전(로그인 시 자동 적용)'
       when a.user_id is null then '⚠ 이용권 없음 — 소급 대상'
       when a.kind <> 'founding' then '⚠ ' || a.kind || ' 등급 — 승급 대상'
       when a.expires_at < now() then '⚠ 만료됨'
       else '정상(' || a.expires_at::date || ' 까지)'
  end                                                as "상태"
from public.founding_members f
left join auth.users u          on lower(u.email) = lower(f.email)
left join public.member_access a on a.user_id = u.id
order by f.member_no nulls last;


-- ------------------------------------------------------------
-- [2] 소급 적용 — 위 목록에서 ⚠ 표시된 분들에게 창립 혜택 부여
--     · 기간: 신청일 + 1년. 이미 지난 경우에는 오늘부터 1년으로 다시 잡는다.
--     · 이미 창립이고 기간이 더 긴 분은 건드리지 않는다(강등 방지).
-- ------------------------------------------------------------
insert into public.member_access
  (user_id, email, kind, started_at, expires_at, updated_at)
select distinct on (u.id)
  u.id,
  u.email,
  'founding',
  coalesce(f.joined_at, now()),
  case
    when coalesce(f.joined_at, now()) + interval '12 months' > now()
      then coalesce(f.joined_at, now()) + interval '12 months'
    else now() + interval '12 months'      -- 신청이 오래돼 이미 지난 경우 오늘부터 1년
  end,
  now()
from public.founding_members f
join auth.users u on lower(u.email) = lower(f.email)
order by u.id, f.member_no nulls last
on conflict (user_id) do update
  set kind       = 'founding',
      expires_at = greatest(member_access.expires_at, excluded.expires_at),
      updated_at = now()
  where member_access.kind is distinct from 'founding'
     or member_access.expires_at < excluded.expires_at;


-- ------------------------------------------------------------
-- [2-1] 번호가 비어 있는 창립 멤버에게 번호 채워 주기 (필요할 때만)
-- ------------------------------------------------------------
with base as (
  select coalesce(max(member_no), 0) as maxno from public.founding_members
), todo as (
  select f.email,
         (select maxno from base) + row_number() over (order by f.joined_at, f.email) as newno
    from public.founding_members f
   where f.member_no is null
)
update public.founding_members f
   set member_no = t.newno
  from todo t
 where f.email = t.email;


-- ------------------------------------------------------------
-- [3] 결과 확인 — 남은 ⚠ 가 없으면 완료
-- ------------------------------------------------------------
select
  count(*)                                                   as "창립 신청 총원",
  count(u.id)                                                as "가입 완료",
  count(*) filter (where a.kind = 'founding'
                     and a.expires_at > now())               as "혜택 정상 적용",
  count(*) filter (where u.id is not null
                     and (a.user_id is null
                          or a.kind <> 'founding'
                          or a.expires_at < now()))          as "남은 문제"
from public.founding_members f
left join auth.users u           on lower(u.email) = lower(f.email)
left join public.member_access a on a.user_id = u.id;
