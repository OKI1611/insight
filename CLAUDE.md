# CLAUDE.md — 바이블 인사이트 (BIBLY / biblynote.com)

이 저장소로 작업할 때 참고하는 안내입니다.

## 이 프로젝트가 무엇인가
- **BIBLY 바이블 인사이트** — "오광일의 인사이트 브리핑" 공식 성경 학습 플랫폼
- 라이브 사이트: https://www.biblynote.com
- GitHub: `OKI1611/insight` (branch: `main`)

## 구조 (빌드 없는 순수 정적 사이트 + Worker)
- 루트에 페이지가 그대로 있는 **정적 HTML** 사이트입니다. 번들러/프레임워크 없음, `npm install` 불필요.
- 페이지: `index.html`, `academy.html`, `bible.html`, `dictionary.html`, `admin.html` 등 루트의 `*.html`
- 공용 스크립트: `site-header.js`, `auth-header.js`, `content-loader.js`, `cms.js`, `access.js`, `protect.js`, `sw.js`(서비스워커) 등
- 백엔드: **Supabase** (`bmxkndkwefdgsomlznoo.supabase.co`) — 로그인·회원·콘텐츠 데이터
- 결제: **토스페이먼츠**, 결제 API는 `worker/index.js`의 `/api/pay/*`가 처리
- 콘텐츠(강의·글·자료 등)는 대체로 Supabase에서 동적 로드됩니다.

## 배포 (중요)
- **Cloudflare가 GitHub `main`에 연결되어 있어 `git push` 하면 자동 배포됩니다.** 별도 배포 명령 불필요.
- 배포 대상: Cloudflare Worker `insight` (설정은 `wrangler.jsonc`)
- **비밀 값은 저장소에 없습니다.** `SUPABASE_SERVICE_KEY`, `TOSS_SECRET_KEY` 등은 Cloudflare 대시보드
  (Worker → Settings → Variables and secrets)에만 설정되어 있습니다. 로컬에는 없어도 정상입니다.
- 서비스워커(`sw.js`)에 버전 문자열(예: `SW v149`)이 있어 정적 자산 갱신 시 함께 올립니다.

## 로컬 미리보기 / 개발
- **정적(HTML/CSS/JS)만 확인**: 루트에서 아무 정적 서버나 사용 — 예 `npx --yes serve -l 4321 .`
- **worker + 결제 API(`/api/pay/*`)까지 로컬 실행**: 저장소 루트의 **`dev-local.ps1`** 실행
  - `powershell -ExecutionPolicy Bypass -File .\dev-local.ps1`  (기본 포트 8788, `-Port 9000` 으로 변경 가능)
  - 확인: `http://localhost:8788/api/pay/ping` → `{"ok":true,"mode":"worker",...}`
  - 결제/DB API 실제 동작에는 시크릿이 필요 → 루트에 **`.dev.vars`** 생성(`.dev.vars.example` 복사 후 값 입력). `.dev.vars` 는 gitignore 됨(커밋 금지).
- ⚠️ `wrangler dev` 를 저장소 루트에서 **직접** 실행하면 무한 리로드 루프에 빠진다(자산 디렉터리가 `./` 라서 wrangler 의 `.wrangler` 상태 쓰기를 감시기가 계속 감지). 그래서 반드시 `dev-local.ps1`(저장소 밖 임시 폴더에서 실행) 을 사용한다.
- `Request.cf` 타임아웃 경고, 채널톡/Supabase 실시간 위젯의 반복 연결 시도는 로컬에서 정상(무시).

## 자동 집계 스크립트 (tools/)
- `node tools/build_stats.mjs` → `content/stats.json` 갱신.
  guide.html 의 '한눈에 보는 바이블 인사이트' 숫자판이 이 파일을 읽는다.
  **강의·사전·Q&A 자료를 추가·수정했으면 이 스크립트를 실행하고 함께 커밋**할 것
  (원본이 사전 12.9MB·권별 Q&A 4.1MB 라 브라우저에서 직접 셀 수 없다).
- `YT_API_KEY=… node tools/build_hall_of_fame.mjs` → `content/hall-of-fame.json` 갱신.
  평소엔 `.github/workflows/update-hall-of-fame.yml` 이 매일 05:00(KST) 자동 실행한다.
  로직만 점검할 땐 `MOCK=1` (실제 명단 파일 대신 `hall-of-fame.mock.json` 에 쓴다).
  제외할 계정은 `content/hall-of-fame-exclude.json` 에 핸들을 넣는다.
  ⚠️ 이 워크플로 커밋 메시지에 `[skip ci]` 를 넣지 말 것 — Cloudflare 가 배포까지 건너뛴다.

## 인강 판매 — 기수(cohort) 운영
- 급수 가격·과목·기수는 **`content/program.json` 한 곳**이 단일 출처다.
- `cohort.deadline`(KST, YYYY-MM-DD)이 지나면 `academy.html`·`watch.html` 양쪽에서
  **얼리버드가 자동으로 걷히고 정가로 돌아간다.** 다음 기수를 열 땐 `cohort`의 이름·마감일만 바꾼다.
- 판매 유입 측정: 프로모 링크의 `?src=` 값이 `site_visits`에 경로로 함께 기록된다
  (`watch-bar` 시청 페이지 띠 / `watch-quiz` 확인학습 직후 / `yt` 유튜브). 관리자 방문통계에서 비교한다.
- 유튜브 설명란·고정댓글 문구와 급수별 딥링크는 `유튜브_판매연결_문구.md` 참고.
- 등록 버튼 등 주요 터치 영역은 **모바일에서 44px 이상** 유지할 것(이용자 연령대가 높다).

## 정본역 성경 본문을 고칠 때 (3곳 동시 갱신)
- 같은 절이 **`bible/kr/<Book>-<장>.json`**(낭독용)과 **`bible/en/<Book>-<장>.json`의 `ko` 필드**(대조·학습용)에
  중복 저장돼 있다. en 쪽은 note(주석)·voc(어휘)·idi(숙어)에도 해당 표현이 인용돼 있으면 같이 고친다.
- 고친 뒤 `python tools/build_search_index.py` 실행 → `bible/search-index.json` 갱신(안 돌리면 옛 표현으로 검색됨).
- 번역 원칙: **KJV가 구체어를 쓴 자리는 해석어로 바꾸지 않는다** (예: cut down = '베어 내다', '개간/개척' ✗).

## 새 HTML 페이지를 만들 때 (아이폰 PWA)
- 아이폰은 '홈 화면에 추가'를 누른 **그 페이지의 head**를 읽는다. `</title>` 아래에 반드시 넣을 것:
  `manifest` 링크, `theme-color`, `apple-touch-icon`(?v=7), `apple-mobile-web-app-capable`, `apple-mobile-web-app-title`
  (관리자 전용 페이지는 manifest 생략 가능. 기존 54페이지는 2026-08 통일 완료).

## 주의 — 홈(index.html)은 공통 컴포넌트를 쓰지 않는 곳이 있다
- 왼쪽 퀵메뉴(`#biblyRail`)는 `site-header.js` 에도 있고 **index.html 안에 인라인 사본**도 있다
  (index 는 자체 헤더를 쓰기 때문). **한쪽만 고치면 홈 화면에는 반영되지 않는다.**
- 파비콘·아이콘 교체 시에는 `favicon.ico`, `favicon.svg`, `images/favicon-*.png`,
  `images/apple-touch-icon.png`, `images/icon-192/512`, `icon-maskable-512` 를 모두 바꾸고
  전 페이지의 `?v=N` 캐시 무효화 번호와 `sw.js` 의 `CACHE` 버전을 함께 올린다.

## 작업 관례
- 커밋 메시지·UI 문구·주석은 **한국어**로 작성합니다(기존 커밋 히스토리 참고).
- 개인/비공개 파일(`*.docx`, `*.pdf`(단 `files/*.pdf` 제외), `PLAN.md`, 키스토어 등)은 `.gitignore`로 제외되어 있습니다.
- `.github/workflows/update-youtube-stats.yml`가 매일 06:00(KST) `content/site.json`의 유튜브 실적을 자동 커밋합니다.
  로컬 작업 시작 전 `git pull`로 이 자동 커밋을 먼저 받아오세요.
- 참고 문서: `배포안내_DEPLOY.md`, `유튜브_유입_가이드.md`, `계획-*.md`
