# CLAUDE.md — 바이블 인사이트 (BIBLY / biblynote.com)

이 저장소로 작업할 때 참고하는 안내입니다.

> **작업 원칙(판정 기준)은 `원칙-바이블인사이트.md` 에 있습니다. 변경 전에 먼저 읽고, 끝에 있는 점검표로 확인하세요.**
> 이 문서(CLAUDE.md)는 실무 절차·파일 위치 안내이고, 둘이 어긋나면 원칙 문서가 우선합니다.

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
- **질문방 새 글 알림(🔔+N)**: `qna-notify.js` — 언어 단추 자리 옆에 종을 붙여 수강생 질문방(community_posts board=qna) 최근 15개를 보여 주고,
  이 기기에서 마지막으로 연 뒤 올라온 글에 N(localStorage `bibly_qna_seen`). site-header.js·app-shell.js·index.html 이 불러온다.
- **새 질문 → 강사 카카오톡**: `worker/notify.js`(카카오 「나에게 보내기」). 질문 등록 화면(qna-board·qna·app-menu)이 등록 직후 `POST /api/notify/qna {id}`,
  5분마다 크론이 놓친 글 재시도. 토큰은 Supabase `notify_kv`(서버 전용, `db/kakao_notify.sql`), 연결은 관리자 › 커뮤니티 관리 › 「카카오톡 연결하기」. 시크릿 `KAKAO_REST_KEY`.
- **앱 푸시(새 강의·새 글)**: `worker/push.js`(Web Push, VAPID 열쇠는 서버가 만들어 notify_kv 에 보관) + `push-client.js`(앱 홈 「알림 켜기」 카드, app-shell 이 불러옴) + sw.js push/notificationclick.
  크론 5분마다 course.json 새 강의(유튜브 id)·columns·notices 새 글을 찾아 push_subs 전체에 30명씩 나눠 발송. 관리자 › 커뮤니티 관리에 구독 수·직접 보내기.
  크론이 5분 간격이 되면서 이메일 육성(processEmailQueue)은 매시 정각 무렵(UTC 분<5)에만 돈다.

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
- `python tools/build_nanje.py` → 질의응답 「성경 난제」 등 85편(`tools/nanje/NNN.json` 원고)을 `content/qna.json` 에 다시 만든다.
  원고에는 구절 위치만 적고 본문은 정본역(bible/kr)에서 자동으로 끼운다 — **정본역을 고친 뒤에도 이것을 다시 돌릴 것**.
  이어서 `python tools/build_smart_index.py` (검색 색인에 질의응답 포함).
- `YT_API_KEY=… node tools/build_hall_of_fame.mjs` → `content/hall-of-fame.json` 갱신.
  평소엔 `.github/workflows/update-hall-of-fame.yml` 이 매일 05:00(KST) 자동 실행한다.
  로직만 점검할 땐 `MOCK=1` (실제 명단 파일 대신 `hall-of-fame.mock.json` 에 쓴다).
  제외할 계정은 `content/hall-of-fame-exclude.json` 에 핸들을 넣는다.
  ⚠️ 이 워크플로 커밋 메시지에 `[skip ci]` 를 넣지 말 것 — Cloudflare 가 배포까지 건너뛴다.

## 다국어(한국어 · English · Español · 日本語 · 中文 繁體) — 2026-11-26 1단계
- **기계 번역 금지.** 용어는 `i18n/GLOSSARY.md`(신학·성경 용어 5개 언어 대조표)를 먼저 따르고, 없는 용어는 표에 추가한 뒤 옮긴다.
- 엔진 `i18n.js` — 언어는 `?lang=xx` > localStorage `bibly_lang` > ko. `<html data-ui="xx">` 를 붙인다.
  site-header.js 가 자동으로 불러오고(첫머리에서 data-ui 먼저 표시), index.html 은 head 에서 직접 불러온다.
  언어 선택 단추는 `id="biblyLangSlot"` 자리(상단 띠)에 그려진다.
- 짧은 화면 글자: `i18n/common.json`(메뉴·머리글·바닥글) + 페이지별 `i18n/pages/<페이지>.json`
  (i18n.js 의 `PAGES` 배열에 이름을 넣어야 불러온다). 키 = 화면의 한국어 그대로, 값 = {en,es,ja,zh}.
  태그가 섞인 문장은 요소에 `data-i18n="키"`. 번역이 없는 글자는 한국어로 남고, 번역본이 없는 페이지엔 안내 띠가 뜬다.
- 긴 글은 언어별 원고를 따로 둔다. 예: `tools/rapture/<lang>.json` → `python tools/build_rapture.py` → `rapture.html`
  (언어별 `<article class="rp" data-l="xx">`). 성경 인용은 위치만 적고 본문은 자동: ko 정본역 · en KJV 전체 본문(bible/kjv — bible/en 의 'en' 은 줄인 절이 섞여 있어 쓰지 않음) ·
  es RV1909 · ja 文語訳 · zh 和合本(`i18n/bible-verses.json`, 위키문헌 원문). 口語訳(일본어)은 저작권 분쟁 소지로 쓰지 않는다.
- i18n.js·common.json 을 고치면 i18n.js 의 `VER` 와 불러오는 쪽 `?v=`(index.html·site-header.js) 를 함께 올린다.
- **페이지 번역 절차(2단계 홈부터)**: 브라우저에서 화면 글자를 추출 → `i18n/pages/_work/<페이지>.items.json`
  ({k, type: text|html|attr}) → 언어별 작업본 `_work/<페이지>.<lang>.json` → `python i18n/pages/_work/check.py <lang>`
  (태그 동일·한글 잔존·{n} 개수 검사) → `python tools/i18n_merge.py <페이지>` → `i18n/pages/<페이지>.json`, i18n.js `PAGES` 에 이름 추가.
  사전 규칙: 앞뒤 기호(└ · ▶ → ›)는 떼고 찾는다, `{n}` = 바뀌는 숫자, 태그 섞인 문장은 innerHTML 전체가 키,
  `<span data-stat>` 안 숫자는 비교에서 빼고 번역 뒤 되돌려 넣는다. 강의 제목·블로그 글·회원 이름(콘텐츠)은 3단계.
- 외국어 구절 수집: `python tools/fetch_ws_verses.py <원고.json>` (위키문헌 원문 → i18n/bible-verses.json). 번역본 구조 검사: `python tools/rapture_struct_check.py`.
- 앱(html.app): 상단바·앱 홈 머리글에 작은 언어 단추(data-compact), app-shell.js 가 i18n.js 를 불러온다. 앱 전용 화면 글자는 `i18n/pages/app-menu.json`.
- **영어판(2026-11-27)**: 화면 글자 전 페이지 + 강의 목록 완료(노트·확인문제·사전·Q&A 등 긴 본문은 한국어 유지 → 그 화면엔 안내 띠).
  - 강의 목록 사전 `i18n/course.json`(제목·요약·과목명·태그·챕터, en) — i18n.js `COURSE_PAGES` 페이지에서만 불러온다.
    **새 강의를 content/course.json 에 넣으면 i18n/course.json 에도 영어를 보탤 것**(없으면 그 강의만 한국어로 보인다).
  - 영어 완료 페이지 목록 = i18n.js `DONE_LANG.en`(안내 띠 안 뜸). 성경 읽기는 영어 화면이면 KJV 단독이 기본, 1611 서문은 영어 원문.
  - 새 페이지·새 문구 번역 절차: 로컬 미리보기에서 `tools/i18n_extract.js`(화면 글자 추출, i18n.js 와 같은 키 규칙) +
    `python tools/i18n_jsstrings.py <파일>`(스크립트 속 문구) → 번역 → `python tools/i18n_merge_en.py <작업 폴더>` →
    `tools/i18n_audit.js`(외국어 화면에 남은 한국어 세기). 브라우저 결과는 로컬 수신기(POST → 파일)로 받는다.
- **스페인어·일본어·중국어 채우기(2026-11-27~)**: 키는 영어판 때 이미 다 뽑혀 있으므로 화면 추출 없이 사전의 빈 칸만 채운다.
  `i18n/pages/_work/l3/<이름>.todo.json`(빠진 키→영어 참고) → 언어별 번역 `<이름>.<lang>.json` → `python tools/i18n_merge_l3.py <이름…>`
  (이름 common = i18n/common.json, 그 밖은 i18n/pages/<이름>.json · 한글 잔존·{n}·태그 검사 후 채움) → 다 된 페이지는 i18n.js `DONE_LANG.es/ja/zh` 에 추가.
  성경 66권 이름·장절 표기는 `python tools/i18n_books.py`(GLOSSARY §5). 진행 순서는 `계획-휴거재림QA.md` 11단계.
- 강사 학력 표기(2026-11-26 저자 지시): West Coast Baptist College 학위는 **Master of Bible Studies**
  (한국어 '성경학 석사(Master of Bible Studies)', 일 聖書学修士, 중 聖經研究碩士, 스 Maestría en Estudios Bíblicos).
  M.R.E.·신학 석사·Th.M. 표기 금지. 성균관대는 '박사과정 수료'(Ph.D.·박사 금지).

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
- **전수 검토(2026-08-22~)**: 기준은 `bible/번역지침.md` §9. 도구 순서 `tools/review_scan.py --book X --emit-input`
  → 장별 에이전트(`tools/review_agent_prompt.md`) → `review_report.py --book X`(검수표, `tools/_review/report/`)
  → 역자 승인 → `review_report.py --collect` → `review_apply.py --approved` → `build_search_index.py` → `tr_battery_run.py`.
  타 역본 본문(`tools/_review/sources/`)은 **저장소·노트·커밋 메시지에 절대 인용 금지**(gitignore). Python은 이 PC에
  `%LOCALAPPDATA%\Programs\Python\Python312\python.exe` 로 설치돼 있다(PATH 미등록 — 전체 경로로 실행).

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
