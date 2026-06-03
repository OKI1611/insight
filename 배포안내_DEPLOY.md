# 홈페이지 인터넷에 올리기 (무료 배포 안내)

이 폴더(`홈페이지 제작`)를 무료로 인터넷에 올리는 방법입니다. 비용 0원.

---

## 방법 A. 가장 빠름 — Netlify Drop (2분, 계정 없이도 가능)

웹에 "일단 띄워보기"용. 깃허브 몰라도 됩니다.

1. 브라우저에서 **https://app.netlify.com/drop** 접속
2. 이 폴더(`홈페이지 제작`)를 **창 안으로 드래그&드롭**
3. 끝! `https://랜덤이름.netlify.app` 주소가 바로 생김
4. (선택) 무료 가입하면 주소를 계속 유지하고 이름도 바꿀 수 있음

> 단점: 수정할 때마다 폴더를 다시 드래그해야 함. CMS(클릭 관리)는 방법 B 필요.

---

## 방법 B. 추천 — GitHub + Cloudflare Pages (이후 CMS·회원기능까지 연결)

오래 쓸 사이트라면 이 방법. 한 번 연결하면 이후 자동 배포됩니다.

### 1단계. GitHub 계정 + 저장소
1. https://github.com 가입 (무료)
2. 우측 상단 **+ → New repository**
3. Repository name: `insight-briefing` (원하는 이름) → **Private** 또는 Public 선택 → Create

### 2단계. 이 폴더를 GitHub에 올리기
이 폴더에서 아래 명령 실행 (저장소 주소는 본인 것으로 교체):
```
git remote add origin https://github.com/본인아이디/insight-briefing.git
git push -u origin main
```
> 로컬 저장소·첫 커밋은 이미 만들어 두었습니다. 위 두 줄만 실행하면 됩니다.

### 3단계. Cloudflare Pages 연결
1. https://dash.cloudflare.com 가입 (무료) → **Workers & Pages → Create → Pages**
2. **Connect to Git** → 방금 만든 GitHub 저장소 선택
3. 빌드 설정: **Framework=None**, Build command=비움, Output=`/` (루트)
4. **Save and Deploy** → `https://이름.pages.dev` 주소 생성
5. 이후 `git push` 할 때마다 자동으로 반영됨

---

## 배포 후 주의 (중요)
- `admin.html`(관리자)·회원가입은 **지금은 화면 데모**라 누구나 접근 가능합니다.
  실제 회원·결제 기능을 붙이는 **다음 단계(Supabase 로그인 연결)** 에서 비밀번호/로그인으로 보호합니다.
- 개인 워드파일·기획서(`.docx`, `PLAN.md`)는 `.gitignore`로 **업로드에서 제외**되어 안전합니다.
- 도메인(예: `ohinsight.com`)을 사고 싶으면 Cloudflare/가비아에서 구매 후 연결 가능(연 약 1.5만원, 선택).
