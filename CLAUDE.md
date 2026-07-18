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

## 작업 관례
- 커밋 메시지·UI 문구·주석은 **한국어**로 작성합니다(기존 커밋 히스토리 참고).
- 개인/비공개 파일(`*.docx`, `*.pdf`(단 `files/*.pdf` 제외), `PLAN.md`, 키스토어 등)은 `.gitignore`로 제외되어 있습니다.
- `.github/workflows/update-youtube-stats.yml`가 매일 06:00(KST) `content/site.json`의 유튜브 실적을 자동 커밋합니다.
  로컬 작업 시작 전 `git pull`로 이 자동 커밋을 먼저 받아오세요.
- 참고 문서: `배포안내_DEPLOY.md`, `유튜브_유입_가이드.md`, `계획-*.md`
