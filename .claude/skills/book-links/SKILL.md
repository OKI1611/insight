---
name: book-links
description: 오광일 저자 도서의 서점 구매 링크를 홈페이지(books.html·index.html·about.html) 전 위치에 한 번에 반영한다. 사용자가 "책 구매 링크 업데이트", "yes24/알라딘/교보/영풍 링크 추가", "신간 서점 입점됐어" 같은 요청을 하면 사용한다.
---

# 책 구매 링크 업데이트

사장님이 서점 URL을 던져 주면 이 절차대로 **3개 파일 4~6곳**을 모두 고친다. 한 곳만 고치면 다른 페이지에는 옛 링크가 남는다.

## ⚠️ 시작 전에 반드시

```bash
git pull origin main
```

**다른 세션에서 이미 같은 파일을 고쳐 두었을 수 있다.** (실제로 2026-08-28 작업 때 원격에 "가이사의 교회 교보문고 입점"과 "저서 목록 아코디언 개편"이 먼저 들어와 있어, 옛 구조로 만든 커밋이 통째로 충돌했다.) pull 하지 않고 작업하면 push 단계에서 전부 다시 해야 한다.

## 입력 해석

사장님은 보통 이렇게 준다.

```
마귀는 거짓말을 하지 않는다. yes24 구매 https://...
알리딘 구매 https://...
가이사의 교회,하나님의 교회 알라딘 구매 https://...
```

- 책 제목이 나온 줄부터 다음 책 제목 전까지가 그 책의 링크다.
- "알리딘/알라딘", "예스24/yes24/YES24", "영풍/영풍문고", "교보/교보문고", "부크크" 모두 같은 서점.
- **종이책인지 전자책인지 말이 없으면 종이책**으로 넣는다(전자책이면 "전자책"이라고 쓴다).
- 애매하면 적용 전에 물어본다.

## 책 ↔ 앵커 대응

| 책 | 앵커 | 아코디언 id |
|---|---|---|
| 마귀는 거짓말을 하지 않는다 (신간) | `#devil` | `bk1` |
| 가이사의 교회, 하나님의 교회 | `#caesar` | `bk2` |
| 가면의 시대 | `#mask` | `bk3` |
| 교회를 떠나고서야, 예수를 만났다 | `#church` | `bk4` |
| 엄마 향기 | `#mom` | `bk5` |

## 고쳐야 할 위치 (한 책당 4곳)

먼저 `grep -n "<그 책의 기존 서점 URL 하나>" books.html index.html about.html` 로 실제 위치를 확인한다.

1. **books.html** — 책 상세의 `구매하기` 블록 (`storeRow`)
2. **index.html** — 홈 신간 카드의 `📘 종이책` 버튼 줄
3. **index.html** — 하단 강사 소개의 **저서 아코디언** (`bkbuy-bkN`)
4. **about.html** — 저자 소개의 저서 아코디언 (index와 같은 구조)

확인: `grep -c "<새 URL 조각>" books.html index.html about.html` → **1 / 2 / 1** 이 나와야 한다(index는 카드 + 아코디언 두 곳).

## 서점 순서·스타일

순서는 항상 **교보문고 → 영풍문고 → 알라딘 → YES24 → 부크크**.

**books.html** — 전부 `buyGhost`. 서점이 하나뿐일 때만 `buyPrimary` + "…에서 구매하기" 문구를 쓴다.
```html
              <a href="URL" target="_blank" rel="noopener"
                 class="buyBtn buyGhost">알라딘</a>
```

**index.html 신간 카드** — 첫 버튼만 금색, 나머지 흰색.
```html
              <a href="URL" target="_blank" rel="noopener" class="flex-1 min-w-[68px] text-center bg-gold text-white text-[11.5px] font-bold rounded-lg py-2 hover:opacity-90 transition">영풍문고</a>
              <a href="URL" target="_blank" rel="noopener" class="flex-1 min-w-[62px] text-center bg-white text-ink border border-ink/15 text-[11.5px] font-bold rounded-lg py-2 hover:border-gold/60 hover:text-gold transition">알라딘</a>
```

**저서 아코디언 (index·about)** — 전부 흰색. 종이책은 📘(책마다 📙·📕도 섞여 있으니 그 책이 이미 쓰던 이모지를 따른다), 전자책은 📱.
```html
                      <a href="URL" target="_blank" rel="noopener"
                         class="inline-flex items-center gap-1 text-[11px] font-bold text-ink bg-white border border-ink/15 rounded-md px-2 py-1 hover:border-gold/60 hover:text-gold transition">📘 알라딘</a>
```

## 함께 고칠 것 (빠뜨리기 쉬움)

- **"입점 준비 중" 안내 문구** — `grep -n "입점 준비 중" *.html`. 방금 넣은 서점을 문구에서 빼고 남은 서점만 적는다. **다 입점했으면 그 `<p>` 줄을 통째로 지운다**(books.html·index.html 두 곳에 있고, about.html에는 없다).
- **철 지난 HTML 주석** — 예 `<!-- … 부크크 단독 판매, 서점 입점 전 -->`.
- **`sw.js` 캐시 버전** — `const CACHE = 'bibleinsight-vNNN'` 숫자를 1 올린다. 안 올리면 재방문자에게 옛 페이지가 보인다.
- meta description·og:description에는 서점 이름이 없으므로 보통 손댈 필요 없다.

## 작업 순서

1. `git pull origin main`
2. 기존 URL로 grep 해서 고칠 위치를 전부 찾고, **현재 구조를 눈으로 확인한다**(구조가 바뀌어 있을 수 있다).
3. Python 스크립트로 치환한다. 주의:
   - **파일이 CRLF다.** 여러 줄 문자열을 그대로 쓰면 매칭이 안 된다 → `crlf = '\r\n' in s` 를 검사해 검색·치환 문자열의 `\n`을 `\r\n`으로 바꿀 것.
   - 치환 전에 `count(old) == 1` 을 확인하고, **하나라도 실패하면 아무것도 저장하지 말고** 보고한다.
4. `grep -c` 로 새 URL 개수(1/2/1)를 확인한다.
5. `sw.js` 버전을 올린다.
6. 커밋(한국어 메시지) → `git push origin main` → Cloudflare 자동 배포(1분쯤).
7. `curl -s https://www.biblynote.com/books.html | grep -c "<새 URL 조각>"` 로 라이브 확인 → 어느 책에 어느 서점이 붙었는지 한 줄로 보고.

## 커밋 메시지 예

```
책 구매 링크 업데이트: 마귀는 거짓말을 하지 않는다(영풍문고·알라딘·YES24), 가이사의 교회(알라딘)

- books.html·index.html·about.html 반영, '입점 준비 중' 안내 문구 갱신
- sw.js 캐시 버전 v260
```
