# 계획서 — 성경 권별 Q&A 격차 보강 (keepbible BQNA 비논쟁 주제 흡수)

목적: 참고 사이트 keepbible.com/BQNA(66권 Q&A 게시판)의 **비논쟁 주제만** 골라, 우리에게 빠진 것을 우리 관점(원어·근본주의 침례신학 1차+복음주의·개혁주의 균형)으로 **100% 자체 집필(패러프레이징, 문장 복제 금지)** 해 권별 Q&A를 풍성화.

## 진행 현황
- **✅ W1 완료(6권, +33)**: 창15·출5·레6·민4·신2·수1.
- **✅ W2 역사서(11권, +80)**: 사사기3·룻7·삼상9·삼하4·왕상9·왕하10·대상8·대하8·스6·느8·에8.
- **✅ W3 시가·대선지(10권, +76)**: 욥기3·시편15·잠언6·전도서2·아가8·이사야14·예레미야8·애가8·에스겔1·다니엘11.
- **✅ W4 소선지 12권(+76)**: 호세아10·요엘6·아모스8·오바댜6·요나6·미가7·나훔5·하박국5·스바냐6·학개6·스가랴3·말라기8.
- 권별 Q&A 총계: **1,495 → 1,803** (이후 다른 세션 보강분 포함). 66권 유지, 금지어·세례 0.
- ⚠️ **데이터 구조 변경(다른 세션)**: 사이트는 이제 `dictionary/qa-book.json`(권별 경량 추출)·`qa-topic.json`(주제별)을 읽음. entries.json은 여전히 마스터. **병합 후 반드시 qa-book.json 재추출**: `python -c "import json,io;d=json.load(io.open('dictionary/entries.json',encoding='utf-8'));b=[e for e in d if e.get('category')=='자주 묻는 질문' and e.get('book')];io.open('dictionary/qa-book.json','w',encoding='utf-8').write(json.dumps(b,ensure_ascii=False,indent=0)+chr(10))"` (indent=0 형식 유지). 주제별 무변동이면 qa-topic.json 건드리지 말 것.
- **✅ W5 복음·행(5권, +62)**: 마태15·마가12·누가14·요한11·사도행전10.
- 권별 Q&A 총계: **1,865**. 66권 유지, 금지어·세례 0.
- 다음 재개: **W6 바울서신(로마서~빌레몬 13권, BQNA45~57)**, 이어 W7 일반서신·계(BQNA58~66). our_book_titles.json 재생성 완료.
- 참고 특성 재확인: 역사서도 권당 게시글 1~16건으로 성글고 번역시비 다수 → 실신규는 우리 관점 격차 자체발굴이 큼(허수는 금지, 실질 주제만).
- ⚠️ 서브에이전트가 def를 "한마디로 —"로 시작 안 하면 merge에서 거부됨 → 병합 전 dry로 확인, 필요시 def 앞에 "한마디로 — " 자동 보정(창세기 사례).

## 방법(웨이브별 서브에이전트 파이프라인)
각 권마다 general-purpose 서브에이전트 1개(작은 책은 묶어도 됨):
1. **수집**: WebFetch로 `https://www.keepbible.com/BQNA{NN}?page=1..`(새 글 없을 때까지, 최대 10p) 질문 **제목(주제)만**. 답변 본문 복제 금지.
2. **비논쟁 필터(제외)**: 번역본 비판/오역 주장, 번역 단어 시비, KJV-Only 옹호, 갭이론(재창조), 교파 논쟁(유아세례 등), 인물/교단 비방, 극단 주장.
3. **대조**: `scratchpad/our_book_titles.json`의 해당 책 배열과 **의미상 중복 제외**.
4. **집필**: 남은 '빠진 주제'만 우리 스키마로 자체 집필(최대 15개/권, 질 우선, 허수 금지).
5. **저장**: **절대경로** `C:/Users/오광일/OneDrive/바탕 화면/홈페이지 제작/scratchpad/qagap/book_{English}.json`. (⚠️상대경로 쓰면 세션 스크래치패드로 샘 → 반드시 절대경로)

## 스키마(merge_qa.py 호환)
`{term, category:"자주 묻는 질문", faqTopic:<8종>, def:"한마디로 —…", deep:[{h,p}…, 마지막 h="흔한 오해"], scriptures:["약칭장:절"…1+], related:[…], book:"<한글책명>"}`
- faqTopic 8종: 구원·믿음 / 하나님·예수·삼위일체 / 성경·창조 / 신앙생활 / 교회·예배·헌금 / 성령·은사 / 윤리·관계·문화 / 죽음·종말·천국
- 금지어(정동수·사랑침례교회·독립침례교회·흠정역·KeepBible·킹제임스 흠정역·그리스도예수안에·마제스티·에스라 성경 사전) 미사용. '세례'→'침례'. 경어체.

## 병합·마감 절차(매 웨이브)
```
python scratchpad/merge_qa.py scratchpad/qagap/book_*.json   # --dry 먼저 확인
# 병합 후 반드시 our_book_titles.json 재생성(다음 웨이브 중복 대조용):
python - <<'PY'
import json,io,collections
d=json.load(io.open('dictionary/entries.json',encoding='utf-8'))
bk=[e for e in d if e.get('category')=='자주 묻는 질문' and e.get('book')]
by=collections.defaultdict(list)
[by[e['book']].append(e['term']) for e in bk]
io.open('scratchpad/our_book_titles.json','w',encoding='utf-8').write(json.dumps(by,ensure_ascii=False,indent=1))
PY
git add dictionary/entries.json && git commit && git push   # SW 불필요(데이터 파일, _headers no-cache)
```

## 남은 웨이브(60권) · BQNA 번호
- **W2 역사서(11)**: 07사사기 08룻기 09삼상 10삼하 11왕상 12왕하 13대상 14대하 15에스라 16느헤미야 17에스더
- **W3 시가·대선지(10)**: 18욥기 19시편 20잠언 21전도서 22아가 23이사야 24예레미야 25예레미야애가 26에스겔 27다니엘
- **W4 소선지 12(12)**: 28호세아 29요엘 30아모스 31오바댜 32요나 33미가 34나훔 35하박국 36스바냐 37학개 38스가랴 39말라기
- **W5 복음·행(5, 대형)**: 40마태 41마가 42누가 43요한 44사도행전
- **W6 바울서신(13)**: 45로마 46고전 47고후 48갈 49엡 50빌 51골 52살전 53살후 54딤전 55딤후 56딛 57몬
- **W7 일반서신·계(9)**: 58히브리서 59야고보 60벧전 61벧후 62요일 63요이 64요삼 65유다 66계
- (BQNA는 표준 66권 순서. 참고 사이트는 권별 편차 큼 — 여호수아 2건·신명기 5건처럼 성근 책 많음. 큰 책=창세기81·복음서·로마서·시편·이사야에 실질 보강 집중.)

## 학습된 주의점
- 참고 사이트 절반가량이 KJV-Only 번역비판 → 대부분 제외됨. 실제 신규는 권당 1~15개 수준.
- 서브에이전트 **절대경로 저장** 필수(상대경로 시 세션 스크래치패드로 유실 → 복사 필요).
- 병합 후 our_book_titles.json 재생성 안 하면 다음 웨이브가 이미 추가한 걸 또 만들 수 있음.
