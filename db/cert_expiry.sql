-- 아카데미 인증과정 "수강기간" 도입 (전 급수 1년 6개월 = 18개월)
-- cert_access 테이블에 만료일 컬럼을 추가한다. (한 번만 실행 · 이미 있으면 건너뜀)
-- 이 컬럼이 채워진 행은 expires_at 이후 유료 혜택(시험·라이브·책자·수료)이 자동 잠긴다.
-- (컬럼을 추가하기 전이거나 expires_at이 비어 있으면 무기한으로 동작 — 기존 동작 보존)

alter table public.cert_access add column if not exists expires_at timestamptz;

-- ───────────────────────────────────────────────────────────
-- [관리자 사용 예시] 입금 확인 후 수강권 부여 — 등록일로부터 18개월
--   tier: 5급=1, 4급=2, 3급=3, 2급=4, 1급=5
--
-- insert into public.cert_access (user_id, tier, expires_at)
-- values ('여기에-유저-UUID', 3, now() + interval '18 months')
-- on conflict (user_id) do update
--   set tier = excluded.tier, expires_at = excluded.expires_at;
--
-- [연장(재등록)] 기존 만료일이 지났으면 지금부터, 아니면 남은 기간에 더하기:
-- update public.cert_access
--   set expires_at = greatest(coalesce(expires_at, now()), now()) + interval '18 months'
--   where user_id = '여기에-유저-UUID';
-- ───────────────────────────────────────────────────────────
