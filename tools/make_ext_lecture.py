# -*- coding: utf-8 -*-
"""외부특강 슬라이드 생성기 — 슬라이드 데이터 한 벌로 ① 웹 슬라이드(HTML) ② 파워포인트(PPTX)를 함께 만든다.

  python tools/make_ext_lecture.py            → 두 강의 모두 생성
  python tools/make_ext_lecture.py 1          → 1강만

· 웹 슬라이드는 maranatha-lecture1.html 의 발표 엔진(로그인 게이트·→ 넘김·F 전체화면·N 발표자 노트·B 암전)을 그대로 쓰고
  슬라이드 본문과 색(따뜻한 저녁빛 테마)만 바꾼다.
· 발표자 노트는 원고 문단을 그대로 넣는다 — 원고 텍스트(책원고/외부특강_예수선교교회/*.txt, git 미추적)의 줄 번호로 참조.
· 대상이 80대 어르신이라 한 장에 한 메시지, 큰 글씨.
"""
import sys, re, os, html
sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "책원고", "외부특강_예수선교교회")

# ───────────────────────── 원고 읽기(노트·성구 원문) ─────────────────────────
def load_lines(fn):
    with open(os.path.join(SRC, fn), encoding="utf-8") as f:
        return f.read().split("\n")

def clean(t):
    return re.sub(r"^\[[^\]]+\]\s*", "", t).strip()

class MS:
    def __init__(self, fn): self.L = load_lines(fn)
    def ln(self, *nums):            # 노트용 원고 문단(1-based 줄 번호)
        out = []
        for n in nums:
            if isinstance(n, tuple):
                out += [clean(self.L[i-1]) for i in range(n[0], n[1]+1)]
            else:
                out.append(clean(self.L[n-1]))
        return "\n\n".join(x for x in out if x and not x.startswith("<<"))
    def verse(self, n):             # "Ref / English / 한국어" 표 한 줄 → (ref, en, ko)
        ref, en, ko = self.L[n-1].split(" / ", 2)
        return ref.strip(), en.strip(), ko.strip()
    def wow(self, n):               # "WOW MOMENT / 본문"
        return self.L[n-1].split(" / ", 1)[1].strip()

KO_BOOK = {"Genesis":"창세기","Hebrews":"히브리서","Isaiah":"이사야","John":"요한복음","1 Thessalonians":"데살로니가전서",
           "Zechariah":"스가랴","Revelation":"요한계시록","Luke":"누가복음","Exodus":"출애굽기"}
def ko_ref(ref):
    m = re.match(r"(.+?) (\d.*)", ref)
    return (KO_BOOK.get(m.group(1), m.group(1)) + " " + m.group(2).replace("–","~")) if m else ref

# ───────────────────────── 슬라이드 데이터 ─────────────────────────
# 유형: title / text / verse / wow / table / divider / cols / prayer
#   h·lines 안의 <em>강조</em>(금색), <b>굵게</b> 는 HTML·PPT 양쪽에 반영된다.
def lecture1():
    m = MS("원고1_고향집대문.txt")
    V = lambda n, eb="성경", h=None: dict(t="verse", eb=eb, h=h, v=m.verse(n))
    W = lambda n, eb, h=None, notes=None: dict(t="wow", eb=eb, h=h, text=m.wow(n), notes=notes or m.wow(n))
    S = [
      dict(t="title", eb="예수선교교회 특강 · 천년왕국과 부활 1강", h="고향 집 대문은<br/><em>하나만</em> 있습니다",
           lines=["그 나라는 어떤 곳이고, 누가 들어가는가", "오광일 · 오광일의 인사이트 브리핑"], notes=m.ln(4)),
      dict(t="text", eb="여는 이야기", h="백삼십 세 노인이<br/>왕 앞에 섰습니다",
           lines=["야곱이 애굽 왕 바로 앞에 섰습니다", "왕이 묻습니다. <b>“네 나이가 얼마냐?”</b>"], notes=m.ln(23)),
      V(25, "창세기 47장"),
      dict(t="text", eb="여는 이야기", h="정말 <em>험악한</em> 세월이었습니다",
           lines=["형을 피해 고향을 떠났고", "외삼촌 집에서 이십 년을 속으며 일했고", "사랑하던 아내 라헬을 길에서 잃었고",
                  "아들 요셉을 잃은 줄 알고 이십 년 넘게 울며 살았습니다"], fr=True, notes=m.ln(27)),
      dict(t="text", eb="여는 이야기", h="우리 인생도<br/><em>나그네 길</em>이었습니다",
           lines=["전쟁을 겪으셨고, 배고픈 시절을 지나셨고", "자식들 키우느라 허리 한 번 제대로 펴 보지 못하셨고", "먼저 떠나보낸 가족도 있으십니다"],
           fr=True, notes=m.ln(28, 29)),
      V(31, "히브리서 11장"),
      dict(t="text", eb="여는 이야기", h="하나님은 돌아갈<br/><em>고향</em>을 준비하셨습니다",
           lines=["“더 나은 본향” — 본향은 고향입니다", "하나님은 나그네들을 <b>부끄러워하지 않으십니다</b>",
                  "오늘 함께 볼 것: <b>그곳은 어떤 곳인가</b>, 그리고 <b>그 집의 대문은 무엇인가</b>"], fr=True, notes=m.ln(33)),
      dict(t="table", eb="오늘의 길 그림", h="시골 버스가 지나는 <em>세 정류장</em>",
           head=["정류장", "무슨 일이 있나", "성경"],
           rows=[["① 지금", "우리가 사는 이 세상 — 나그네 길", "히 11:13"],
                 ["② 예수님 다시 오심 → 천 년의 나라", "예수님이 이 땅에서 천 년 동안 직접 다스리심", "계 20:4~6"],
                 ["③ 영원한 고향", "새 하늘과 새 땅 — 눈물도 죽음도 없음", "계 21:1~4"]],
           foot="오늘은 주로 <b>두 번째 정류장, 천년왕국</b> 이야기입니다", notes=m.ln(36, 43)),
      dict(t="divider", num="첫째 이야기", h="왕이 <em>직접</em> 다스리는 나라", sub="천년왕국은 어떤 나라인가", notes=m.ln(45)),
      dict(t="text", eb="첫째 이야기", h="예수님이 이 땅에서<br/><em>천 년 동안</em> 직접 다스리십니다",
           lines=["요한계시록 20장에 “천 년”이 <b>여섯 번</b> 나옵니다", "같은 말을 여섯 번 하셨다면 — <b>“이건 분명하다”</b>는 뜻입니다",
                  "그 나라에서 가장 좋은 것은 <b>왕</b>입니다"], fr=True, notes=m.ln(45, 46)),
      V(48, "이사야 11장 — 그 나라의 왕"),
      dict(t="text", eb="첫째 이야기", h="눈에 보이는 대로,<br/>귀에 들리는 대로 <em>판단하지 않는 왕</em>",
           lines=["사람은 겉모습과 소문으로 판단합니다", "그래서 억울한 사람이 생깁니다", "교회에서도 그런 일을 겪으신 분이 계십니까?"],
           fr=True, notes=m.ln(50)),
      W(52, "WOW", "그 왕은 <em>당신의 사정</em>을 다 아십니다"),
      dict(t="text", eb="첫째 이야기", h="요셉 — 그 왕을<br/><em>미리 보여 준</em> 사람",
           lines=["형들에게 미움받아 구덩이에, 노예로, 감옥으로", "하나님이 그를 애굽의 총리로 세우심", "자기를 판 형들에게 복수하지 않고 울며 말합니다",
                  "<b>“하나님이 생명을 구원하시려고 나를 먼저 보내셨나이다”</b> (창 45:5)"], fr=True, notes=m.ln(54)),
      W(56, "WOW", "<em>“이제 죽어도 족하도다”</em>"),
      dict(t="divider", num="둘째 이야기", h="고향 집 대문은 <em>하나뿐</em>입니다", sub="다시 태어남", notes=m.ln(59)),
      dict(t="text", eb="둘째 이야기", h="니고데모 — 그 시대<br/><em>최고의 신앙인</em>",
           lines=["이스라엘의 존경받는 선생", "성경을 줄줄 외우고, 기도도 열심히 하던 사람", "어느 날 밤 예수님을 찾아왔습니다"],
           fr=True, notes=m.ln(59)),
      V(61, "요한복음 3장"),
      dict(t="text", eb="둘째 이야기", h="한 집의 가족이 되려면<br/><em>그 집에서 태어나야</em> 합니다",
           lines=["밥을 많이 얻어먹는다고 가족이 됩니까?", "일을 열심히 도와준다고 가족이 됩니까?", "태어나면 출생신고를 하고 <b>호적에 이름이 올라갑니다</b>",
                  "교회 오래 다닌 것, 봉사, 직분이 아니라 — <b>다시 태어나야 하나님의 자녀</b>"], fr=True, notes=m.ln(63, 64)),
      dict(t="text", eb="둘째 이야기", h="어떻게 <em>다시 태어납니까</em>?",
           lines=["“영접하는 자 곧 그 이름을 믿는 자들에게는 하나님의 자녀가 되는 권세를 주셨으니” (요 1:12)",
                  "예수님을 내 구주로 <b>마음에 모셔 들이는 것</b>", "나를 위해 죽으시고 다시 살아나심을 믿고 <b>나를 그분께 맡기는 것</b>",
                  "그 순간 하나님은 <b>하늘 호적에 우리 이름을</b> 올리십니다"], fr=True, notes=m.ln(65)),
      W(67, "WOW", "대문의 이름은 <em>“다시 태어남”</em>"),
      dict(t="text", eb="둘째 이야기 · 요한복음 9장", h="눈을 뜬 사람이<br/><em>회당에서 쫓겨났습니다</em>",
           lines=["예수님이 태어날 때부터 눈먼 사람의 눈을 뜨게 하셨습니다", "그 일 때문에 그는 회당(지금의 교회)에서 쫓겨납니다 (요 9:34)",
                  "<b>“예수께서 … 그를 만나사”</b> (요 9:35) — 예수님이 찾아가셨습니다", "<b>“주여 내가 믿나이다”</b> (요 9:38)"],
           fr=True, notes=m.ln(69, 70)),
      W(72, "WOW", "“나는 <em>문</em>이니” (요 10:9)"),
      dict(t="divider", num="셋째 이야기", h="먼저 간 가족,<br/>그리고 <em>부활의 순서</em>", sub="“먼저 떠난 우리 가족은 어떻게 됩니까?”", notes=m.ln(75)),
      V(77, "데살로니가전서 4장"),
      dict(t="text", eb="셋째 이야기", h="성경은 그들을<br/><em>“잠든 사람”</em>이라 부릅니다",
           lines=["잠든 사람은 다시 일어납니다", "슬퍼하지 말라는 것이 아니라 — <b>소망 없이</b> 슬퍼하지 말라는 것", "우리는 울지만, <b>다시 만날 것을 알고</b> 웁니다"],
           fr=True, notes=m.ln(79)),
      dict(t="table", eb="셋째 이야기 · 고전 15:23 “각각 자기 차례대로”", h="부활은 <em>추수</em>처럼 순서가 있습니다",
           head=["농사", "부활", "성경"],
           rows=[["첫 열매 — 처음 익은 이삭", "예수님의 부활 (2천 년 전)", "고전 15:20, 23"],
                 ["본 추수 — 들판 전체", "예수님이 공중에 오실 때 교회의 성도들", "살전 4:16~17"],
                 ["이삭줍기 — 남은 이삭", "예수님이 땅에 오실 때 구약의 성도들과 환난 때 믿은 성도들", "단 12:2, 계 20:4"]],
           notes=m.ln(80, 87)),
      dict(t="text", eb="셋째 이야기 · 고전 15:36~37", h="볍씨는 썩은 것이 아니라<br/><em>심긴</em> 것입니다",
           lines=["“흙이 되셨을 텐데 어떻게 다시 일어나십니까?”", "볍씨는 흙 속에서 썩어 없어지는 것처럼 보입니다", "가을이면 그 자리에 황금빛 벼가 고개를 숙입니다",
                  "하나님은 먼저 간 성도들을 땅에 <b>“심으신”</b> 것입니다 — 하나님의 가을을 기다립니다"], fr=True, notes=m.ln(88, 89)),
      W(91, "WOW · 살전 4:17~18", "<em>“그들과 함께”</em>"),
      dict(t="divider", num="넷째 이야기", h="그 나라에 사는<br/><em>두 종류의 사람</em>", sub="천년왕국 첫날 아침", notes=m.ln(94, 95)),
      dict(t="table", eb="넷째 이야기", h="부활한 몸, 그리고 <em>지금 같은 몸</em>",
           head=["", "부활한 몸으로 사는 사람", "지금 같은 몸으로 사는 사람"],
           rows=[["누구", "먼저 간 성도들 · 변화된 우리 · 구약의 성도 · 환난 때 순교한 성도", "7년 환난을 살아서 통과한 믿는 사람들"],
                 ["몸", "늙지 않고, 아프지 않고, 죽지 않음", "오래 살지만 늙고, 아이를 낳음"],
                 ["하는 일", "예수님과 함께 다스리고 돌봄", "집 짓고 농사짓고 가정을 이룸"]],
           foot="두 종류 모두 <b>다시 태어난 사람들</b> — 그날 그 땅에 믿지 않는 사람은 <b>단 한 명도 없습니다</b>",
           notes=m.ln(94, 95, 103)),
      dict(t="divider", num="다섯째 이야기", h="그 나라의 <em>하루</em>", sub="선지자들이 그려 놓은 풍경", notes=m.ln(105)),
      V(107, "스가랴 8장"),
      W(110, "WOW", "노인은 편히 앉고, <em>아이들은 뛰노는</em> 거리"),
      dict(t="cols", eb="다섯째 이야기", h="그 나라에는 <em>이런 일</em>이 있습니다",
           cols=[["전쟁이 없습니다", "칼을 쳐서 보습을, 창을 쳐서 낫을 만듭니다 (사 2:4)"],
                 ["짐승도 순해집니다", "이리가 어린 양과 함께 살고, 젖먹이가 독사 구멍에서 장난합니다 (사 11:6~8)"],
                 ["왜 그렇게 됩니까?", "“물이 바다를 덮음 같이 여호와를 아는 지식이 세상에 충만할 것임이니라” (사 11:9)"]],
           notes=m.ln(112, 113, 114)),
      dict(t="cols", eb="다섯째 이야기", h="아픈 몸도, 헛수고도 <em>없습니다</em>",
           cols=[["병이 고쳐집니다", "맹인의 눈이 밝고, 저는 자가 사슴같이 뜁니다 (사 35:5~6)"],
                 ["일한 것을 내가 누립니다", "집을 짓고 그 안에 살며, 포도나무를 심고 열매를 먹습니다 (사 65:21~22)"],
                 ["나무처럼 오래 삽니다", "백 살에 죽으면 “아이가 일찍 갔다”고 할 정도입니다 (사 65:20)"]],
           notes=m.ln(115, 116)),
      dict(t="table", eb="다섯째 이야기 · 고전 15:42~43", h="부활한 몸은 <em>이런 몸</em>입니다",
           head=["지금 우리 몸", "부활한 몸"], rows=[["썩고 늙는 몸", "썩지 않는 몸"], ["부끄러운 몸", "영광스러운 몸"], ["약한 몸", "강한 몸"]],
           foot="부활하신 예수님은 “나를 만져 보라” 하시고 생선을 드셨습니다 (눅 24:39~43) — <b>우리도 그 나라에서 서로를 알아봅니다</b>",
           notes=m.ln(117, 124)),
      dict(t="divider", num="여섯째 이야기", h="천 년 끝의<br/><em>이상한 일</em>", sub="계 20:7~9", notes=m.ln(126)),
      dict(t="text", eb="여섯째 이야기", h="가장 좋은 나라에서도<br/><em>마음이 바뀌지 않은</em> 사람들",
           lines=["의로운 왕, 전쟁 없음, 먹을 것 넘침, 병도 거의 없음", "그런데도 마음이 새로 태어나지 않은 사람은 하나님을 거역했습니다",
                  "광야의 이스라엘도 그랬습니다 — 만나와 구름 기둥 아래서 <b>금송아지</b>를 만들었습니다"], fr=True, notes=m.ln(127, 128)),
      W(130, "WOW", "사람을 바꾸는 것은 환경이 아니라 <em>마음</em>"),
      dict(t="divider", num="일곱째 이야기", h="그리고 <em>영원한 집</em>", sub="새 하늘과 새 땅", notes=m.ln(133)),
      dict(t="text", eb="일곱째 이야기", h="믿는 사람은<br/><em>심판대 앞에 서지 않습니다</em>",
           lines=["“…심판에 이르지 아니하나니 사망에서 생명으로 옮겼느니라” (요 5:24)", "우리 죄에 대한 심판은 <b>이미 십자가에서 끝났습니다</b>",
                  "이삿날 바뀌는 것은 사람이 아니라 <b>집</b>입니다"], fr=True, notes=m.ln(133, 134)),
      dict(t="text", eb="일곱째 이야기 · 요 14:1~2", h="“내 아버지 집에<br/><em>거할 곳이 많도다</em>”",
           lines=["명절에 자식들이 오면 어머니는 방마다 이불을 꺼내고 군불을 때 놓으셨습니다", "예수님이 지금 <b>아버지 집에 우리 방을</b> 준비하고 계십니다",
                  "늦게 오는 자식을 위해서도 <b>불을 켜 두고 기다리시는</b> 집입니다"], fr=True, notes=m.ln(135, 136)),
      V(138, "요한계시록 21장"),
      W(141, "WOW", "<em>모든 눈물</em>을 닦아 주시니"),
      dict(t="text", eb="맺는 말", h="오늘 말씀을 <em>정리</em>하면",
           lines=["하나님은 나그네들을 위해 <b>고향</b>을 준비하셨습니다", "예수님이 천 년 동안 <b>공의로 다스리시는 나라</b>",
                  "먼저 간 성도들과 <b>함께</b> 부활한 몸으로", "노인이 편히 앉고 아이들이 뛰노는 나라 — 그리고 <b>눈물 없는 영원한 집</b>",
                  "그 집의 대문은 하나 — <b>예수님을 믿어 다시 태어나는 것</b>"], fr=True, notes=m.ln(144)),
      dict(t="title", eb="2강 예고", h="그런데<br/><em>나 같은 사람도?</em>",
           lines=["믿음도 작고, 너무 늦게 믿었고, 교회에서 상처받고 떠나 있기도 했는데…",
                  "다음 시간 — 집 나갔던 아들을 맞은 아버지, 그리고 십자가 위의 한 강도", "<b class=\"gold\">그 나라에서 만나요</b>"],
           notes=m.ln(145, 146)),
    ]
    return dict(key="1", slug="ext-lecture-jmc1", pptx="ext-jmc-lecture1-one-gate-home",
                title="고향 집 대문은 하나만 있습니다", series="예수선교교회 특강 · 천년왕국과 부활 1강", slides=S)

def lecture2():
    m = MS("원고2_대문앞아버지.txt")
    V = lambda n, eb="성경", h=None: dict(t="verse", eb=eb, h=h, v=m.verse(n))
    W = lambda n, eb, h=None: dict(t="wow", eb=eb, h=h, text=m.wow(n), notes=m.wow(n))
    prayer = [x.strip().lstrip("•").strip() for x in m.L[110-1].split(" / ")[1:]]
    S = [
      dict(t="title", eb="예수선교교회 특강 · 천년왕국과 부활 2강", h="아버지는 대문 앞에서<br/><em>기다리고 계셨습니다</em>",
           lines=["나 같은 사람도 그 나라에 들어갈 수 있을까", "오광일 · 오광일의 인사이트 브리핑"], notes=m.ln(4)),
      dict(t="text", eb="지난 시간", h="고향 집 대문은 <em>하나뿐</em>이었습니다",
           lines=["하나님이 나그네들을 위해 준비하신 고향", "노인이 편히 앉고 아이들이 뛰노는 나라, 눈물 없는 영원한 집",
                  "그 대문은 — <b>예수님을 믿어 다시 태어나는 것</b>", "그리고 남은 질문 하나: <b class=\"gold\">“그런데 나 같은 사람도?”</b>"],
           fr=True, notes=m.ln(23, 24)),
      dict(t="text", eb="여는 이야기 · 누가복음 15장", h="집을 나간 <em>작은아들</em>",
           lines=["“아버지, 내 몫의 재산을 지금 주십시오”", "먼 나라에서 재산을 다 탕진하고", "돼지가 먹는 쥐엄 열매로라도 배를 채우고 싶을 만큼 비참해졌습니다"],
           fr=True, notes=m.ln(25)),
      dict(t="text", eb="여는 이야기", h="“품꾼 하나로<br/><em>써 주십시오</em>”",
           lines=["누더기를 걸치고, 맨발로, 고개를 숙이고", "“아버지가 문을 열어 주실까?”", "“동네 사람들이 뭐라고 할까? 형은 나를 받아 줄까?”"],
           fr=True, notes=m.ln(26)),
      V(28, "누가복음 15장"),
      W(31, "WOW", "<em>“아직도 거리가 먼데”</em>"),
      dict(t="divider", num="첫째 이야기", h="유월절 밤, <em>두 집</em>", sub="“내 믿음은 너무 작은데…”", notes=m.ln(34, 35)),
      V(37, "출애굽기 12장"),
      dict(t="cols", eb="첫째 이야기", h="그날 밤 <em>어느 집</em>이 안전했습니까?",
           cols=[["첫째 집", "믿음이 강한 아버지 — 피를 바르고 “걱정 마라” 하며 편히 앉아 먹습니다"],
                 ["둘째 집", "겁 많은 아버지 — 피를 바르고도 밤새 떨며 맏아들을 끌어안고 있습니다"]],
           foot="<b>두 집 다 안전했습니다</b> — “내가 <em>피를</em> 볼 때에 넘어가리니”", notes=m.ln(39, 40)),
      W(42, "WOW", "믿음의 크기가 아니라 <em>믿음이 붙잡은 분</em>"),
      dict(t="text", eb="첫째 이야기", h="꽁꽁 언 강을<br/><em>건너는 두 사람</em>",
           lines=["한 사람은 성큼성큼 걸어가고, 한 사람은 무서워서 엉금엉금 기어갑니다", "둘 다 무사히 건넜습니다 — <b>얼음이 두꺼웠기 때문</b>입니다",
                  "중요한 것은 내 믿음의 두께가 아니라 <b>내가 올라선 얼음의 두께</b>", "예수님이라는 얼음은 <b>온 세상의 죄를 실어도 깨지지 않습니다</b>"],
           fr=True, notes=m.ln(44)),
      dict(t="text", eb="첫째 이야기 · 막 9:24", h="“내가 믿나이다,<br/><em>나의 믿음 없는 것을 도와주소서</em>”",
           lines=["믿는다고 하면서 동시에 믿음 없음을 고백한 아버지", "예수님은 꾸짖지 않으시고 <b>그 아들을 고쳐 주셨습니다</b>",
                  "예수님은 작은 믿음을 비웃지 않으십니다 — <b>그 믿음을 들고 온 사람을 받아 주십니다</b>"], fr=True, notes=m.ln(45)),
      dict(t="text", eb="첫째 이야기 · 여호수아 2장", h="라합의 창문에 걸린<br/><em>붉은 줄</em>",
           lines=["이스라엘 사람도 아니고, 손가락질받던 여인", "여리고성이 무너지던 날 — 그 집만 구원받았습니다", "착해서가 아니라 <b>붉은 줄 때문</b>이었습니다",
                  "그리고 그 이름이 <b>예수님의 족보</b>에 올랐습니다 (마 1:5)"], fr=True, notes=m.ln(46, 47)),
      dict(t="divider", num="둘째 이야기", h="<em>셋째 칸</em>은 없습니다", sub="“들어가도 반쯤만 들어가는 건 아닐까?”", notes=m.ln(49)),
      V(51, "요한계시록 20장"),
      dict(t="table", eb="둘째 이야기", h="성경은 사람을 <em>두 무리</em>로만 나눕니다",
           head=["칸", "누구", "결과"],
           rows=[["첫째 칸", "예수님을 믿어 다시 태어난 모든 사람 — 믿음이 크든 작든, 일찍 믿었든 늦게 믿었든", "첫째 부활 → 천 년 동안 함께 다스림 → 영원한 집"],
                 ["둘째 칸", "끝까지 예수님을 거절한 사람", "크고 흰 보좌 심판 → 둘째 사망"],
                 ["셋째 칸?", "“구원은 받았지만 그 나라에서 제외된 사람”", "성경에 없음"]],
           notes=m.ln(53)),
      dict(t="text", eb="둘째 이야기", h="대문을 지났으면<br/><em>집 안</em>에 있는 것입니다",
           lines=["탕자의 아버지는 “행랑채에서 지내다 나중에 들어오너라” 하지 않았습니다", "제일 좋은 옷, 가락지, 신, 살진 송아지 잔치 (눅 15:22~23)",
                  "노아의 방주 — 위층이든 아래층이든 <b>방주 안에 있던 사람은 다 살았습니다</b>", "그 문은 <b>하나님이 직접 닫으셨습니다</b> (창 7:16)"],
           fr=True, notes=m.ln(60, 61)),
      dict(t="divider", num="셋째 이야기", h="<em>넘어졌던</em> 사람도?", sub="“교회에서 상처받고 몇 년 동안 떠나 있었습니다”", notes=m.ln(63)),
      dict(t="text", eb="셋째 이야기", h="세 번 부인한 <em>베드로</em>",
           lines=["“주와 함께 옥에도, 죽는 데에도 가겠습니다”", "그날 밤 여종 앞에서 세 번 “나는 그 사람을 모른다”", "닭이 울고, 예수님이 돌이켜 보시고 — <b>밖에 나가 심히 통곡했습니다</b>"],
           fr=True, notes=m.ln(64, 65)),
      V(67, "누가복음 22장"),
      W(70, "WOW", "<em>“내가 너를 위하여 기도하였노니”</em>"),
      dict(t="text", eb="셋째 이야기", h="사람들은 잊어도<br/><em>예수님은 잊지 않으십니다</em>",
           lines=["“깨어 있든지 자든지 자기와 함께 살게 하려 하셨느니라” (살전 5:10)", "“그들은 혹시 잊을지라도 나는 너를 잊지 아니할 것이라” (사 49:15)",
                  "“내가 너를 <b>내 손바닥에 새겼고</b>” (사 49:16)", "못 자국 난 그 손바닥에 <b>당신의 이름</b>이 새겨져 있습니다"],
           fr=True, notes=m.ln(72, 73)),
      dict(t="divider", num="넷째 이야기", h="들어가는 것은 같고,<br/><em>상은 다릅니다</em>", sub="“그럼 열심히 할 필요가 없지 않습니까?”", notes=m.ln(75)),
      dict(t="cols", eb="넷째 이야기", h="잔칫집과 <em>집 짓기</em>",
           cols=[["잔칫집", "초대받은 사람은 다 잔치에 들어갑니다. 며칠 동안 전을 부치고 손님을 맞은 사람은 주인의 특별한 인사와 선물을 받습니다"],
                 ["집 짓기 (고전 3:11~15)", "모두 예수님이라는 같은 기초 위에 짓습니다. 불로 시험하면 금·은은 남고 짚은 탑니다 — <b>상은 잃을 수 있어도 구원은 잃지 않습니다</b>"]],
           notes=m.ln(76, 77)),
      W(79, "WOW", "오늘 드린 감사 한 마디가 <em>금</em>이 되어 남습니다"),
      dict(t="divider", num="다섯째 이야기", h="십자가 옆의 <em>강도</em>", sub="가장 늦게 믿은 사람의 이야기", notes=m.ln(83)),
      dict(t="text", eb="다섯째 이야기", h="처음에는 <em>둘 다</em> 욕했습니다",
           lines=["“함께 십자가에 못 박힌 강도들도 이와 같이 욕하더라” (마 27:44)", "“아버지 저들을 사하여 주옵소서” (눅 23:34) — 그런 사람을 그는 처음 보았습니다",
                  "한 강도가 다른 강도를 꾸짖습니다 — <b>“이 사람이 행한 것은 옳지 않은 것이 없느니라”</b>"], fr=True, notes=m.ln(83, 84)),
      V(86, "누가복음 23장"),
      dict(t="text", eb="다섯째 이야기", h="“당신의 나라에<br/><em>임하실 때에</em>”",
           lines=["피투성이로 죽어 가시는 분, 제자들은 다 도망갔습니다", "그런데 이 강도는 그분이 <b>왕으로 다시 오셔서 나라를 세우실 것</b>을 믿었습니다",
                  "그 자리에서 <b>가장 큰 믿음</b>을 보인 사람이었습니다"], fr=True, notes=m.ln(88)),
      dict(t="text", eb="다섯째 이야기 · 마 20:1~16", h="해 지기 한 시간 전에 온 <em>포도원 품꾼</em>",
           lines=["하루 종일 아무도 써 주지 않아 장터에 서 있던 사람들", "주인은 마지막에 온 사람부터 <b>하루 품삯을 다</b> 주었습니다",
                  "구원은 일한 시간만큼 받는 월급이 아니라 <b>주인의 선하심으로 받는 선물</b>", "해 지기 한 시간 전도 <b>늦지 않습니다</b>"],
           fr=True, notes=m.ln(89, 90)),
      dict(t="text", eb="다섯째 이야기", h="“나를 <em>기억하소서</em>”",
           lines=["좋은 자리를 달라고 하지 않았습니다", "세례도, 예배도, 헌금도, 봉사도 — 내세울 것이 하나도 없었습니다", "못 박힌 손발로 할 수 있는 것은 단 하나",
                  "<b>“나를 잊지 말아 주십시오”</b>"], fr=True, notes=m.ln(91)),
      W(93, "WOW", "<em>“오늘”</em> 그리고 <em>“나와 함께”</em>"),
      dict(t="text", eb="다섯째 이야기", h="그 강도도 <em>그 나라에</em> 들어갑니다",
           lines=["그는 예수님을 믿고 죽은 사람입니다 — 첫째 부활", "추수 때가 조금 다를 수는 있어도 <b>모두 같은 들판의 곡식</b>",
                  "아브라함, 야곱, 베드로가 앉은 식탁 — 그 사이에 <b>손목에 못 자국이 있는 한 사람</b>", "그리고 그 자리 어딘가에 <b class=\"gold\">당신의 자리</b>가 있습니다"],
           fr=True, notes=m.ln(95, 96)),
      dict(t="text", eb="맺는 말", h="오늘 말씀을 <em>정리</em>하면",
           lines=["믿음의 크기가 아니라 <b>믿음이 붙잡은 예수님의 피</b>", "그 나라에는 <b>셋째 칸이 없습니다</b>", "넘어졌던 베드로를 위해 <b>미리 기도하셨습니다</b>",
                  "상은 다르지만 <b>구원은 같습니다</b>", "마지막 몇 시간에 믿은 강도에게도 <b>“오늘 나와 함께”</b>"], fr=True, notes=m.ln(98)),
      dict(t="text", eb="맺는 말", h="그 아버지가 기다리는 사람은<br/><em>바로 당신</em>입니다",
           lines=["믿음이 작다고 부끄러워하는 당신", "너무 늦었다고 생각하는 당신", "교회에서 상처받고 돌아갈 용기가 없던 당신"],
           fr=True, notes=m.ln(99)),
      V(101, "요한복음 6장"),
      W(104, "WOW", "<em>“결코 내쫓지 아니하리라”</em>"),
      dict(t="prayer", eb="함께 드리는 기도", h="마음으로 <em>따라 하십시오</em>", lines=prayer, notes=m.ln(108)),
      dict(t="title", eb="마침", h="아버지 집 대문은<br/><em>지금도 열려 있습니다</em>",
           lines=["불도 켜져 있습니다", "<b class=\"gold\">그 고향 집, 그 나라에서 우리 꼭 함께 만납시다</b>"], notes=m.ln(112)),
    ]
    return dict(key="2", slug="ext-lecture-jmc2", pptx="ext-jmc-lecture2-father-at-the-gate",
                title="아버지는 대문 앞에서 기다리고 계셨습니다", series="예수선교교회 특강 · 천년왕국과 부활 2강", slides=S)

# ───────────────────────── HTML 생성 ─────────────────────────
EXTRA_CSS = """
    /* ===== 외부특강 테마 — 노을 진 고향 집(따뜻한 저녁빛) · 어르신용 큰 글씨 ===== */
    :root{ --bg:#1c1511; --bg2:#2a1f18; --ink:#fff7ec; --sub:#ecd9bf; --dim:#a8927a; --gold:#f5bd62; --gold-deep:#e09a3e; --line:rgba(255,236,210,.16); }
    .slide{background:radial-gradient(1300px 900px at 78% -10%, #3a2a1d 0%, var(--bg) 62%)}
    #gate{background:radial-gradient(1200px 700px at 70% -10%, #3a2a1d 0%, var(--bg) 60%)}
    h2{font-size:clamp(30px,8vmin,88px)}
    .lines p{font-size:clamp(19px,3.9vmin,42px); line-height:1.55}
    .lines .gold, b.gold{color:var(--gold)}
    .vtext p{font-size:clamp(20px,4vmin,46px); line-height:1.7}
    .vtext .ven{font-family:'Pretendard',sans-serif; font-size:clamp(12px,2vmin,21px); color:var(--dim); line-height:1.55; margin-top:1.6vmin; font-style:italic}
    .wow{margin-top:3.4vmin; border:2px solid var(--gold); border-radius:22px; padding:3.6vmin 4.2vmin; background:rgba(245,189,98,.07); max-width:46em}
    .wow p{font-family:'Noto Serif KR','Pretendard',serif; font-size:clamp(17px,3.35vmin,38px); line-height:1.75; color:var(--ink)}
    .tbl th,.tbl td{font-size:clamp(16px,3.3vmin,36px); padding:1.7vmin 2.3vmin}
    .col h3{font-size:clamp(19px,3.9vmin,42px)} .col p{font-size:clamp(16px,3.3vmin,36px)}
    .keyRound{width:auto; min-width:clamp(150px,26vmin,280px); height:clamp(70px,11vmin,120px); border-radius:999px; padding:0 4vmin}
    .keyRound .kn{font-size:clamp(26px,5vmin,54px)}
    .divsub{margin-top:2.4vmin; font-size:clamp(17px,3.2vmin,34px); color:var(--sub)}
    .prayer p{font-family:'Noto Serif KR','Pretendard',serif; font-size:clamp(18px,3.5vmin,40px); line-height:1.6; color:var(--ink)}
"""

def h(s): return s  # 데이터 안의 <em>/<b>/<br/> 는 그대로 쓴다

def slide_html(i, s):
    t = s["t"]; eb = s.get("eb"); notes = html.escape(s.get("notes", "")).replace("\n\n", "<br/><br/>")
    eyebrow = f'<p class="eyebrow">{eb}</p>' if eb else ""
    fr = ' fr' if s.get("fr") else ''
    body = ""
    cls = "slide"
    if t == "title":
        cls += " center"
        body = f'{eyebrow}<h2 class="serif">{s["h"]}</h2><div class="lines">' + "".join(
            f'<p{" style=\"color:var(--dim); font-size:clamp(14px,2.4vmin,24px)\"" if "인사이트 브리핑" in l else ""}>{l}</p>' for l in s["lines"]) + "</div>"
    elif t == "text":
        body = f'{eyebrow}<h2 class="serif">{s["h"]}</h2><div class="lines">' + "".join(f'<p class="{fr.strip()}">{l}</p>' for l in s["lines"]) + "</div>"
    elif t == "verse":
        ref, en, ko = s["v"]
        hh = f'<h2 class="serif" style="font-size:clamp(24px,5vmin,56px)">{s["h"]}</h2>' if s.get("h") else ""
        body = f'{eyebrow}{hh}<div class="vtext"><p>{html.escape(ko)}</p><cite>{ko_ref(ref)}</cite><p class="ven">{html.escape(ref)} (KJV) — {html.escape(en)}</p></div>'
    elif t == "wow":
        hh = f'<h2 class="serif" style="font-size:clamp(26px,6vmin,66px)">{s["h"]}</h2>' if s.get("h") else ""
        body = f'{eyebrow}{hh}<div class="wow"><p>{html.escape(s["text"])}</p></div>'
    elif t == "table":
        head = "".join(f"<th>{x}</th>" for x in s["head"])
        rows = "".join("<tr class=\"fr\">" + "".join(f'<td class="{"gd" if j==0 else ""}">{c}</td>' for j, c in enumerate(r)) + "</tr>" for r in s["rows"])
        foot = f'<div class="lines"><p class="fr">{s["foot"]}</p></div>' if s.get("foot") else ""
        body = f'{eyebrow}<h2 class="serif">{s["h"]}</h2><table class="tbl"><tr>{head}</tr>{rows}</table>{foot}'
    elif t == "divider":
        cls += " center"
        body = f'<div class="keyRound"><span class="kn">{s["num"]}</span></div><h2 class="serif">{s["h"]}</h2><p class="divsub">{s.get("sub","")}</p>'
    elif t == "cols":
        cols = "".join(f'<div class="col{" gold" if j==0 else ""} fr"><h3>{a}</h3><p>{b}</p></div>' for j, (a, b) in enumerate(s["cols"]))
        foot = f'<div class="lines"><p class="fr">{s["foot"]}</p></div>' if s.get("foot") else ""
        body = f'{eyebrow}<h2 class="serif">{s["h"]}</h2><div class="cols">{cols}</div>{foot}'
    elif t == "prayer":
        body = f'{eyebrow}<h2 class="serif">{s["h"]}</h2><div class="vtext prayer">' + "".join(f'<p class="fr">{html.escape(l)}</p>' for l in s["lines"]) + "</div>"
    return f'\n    <!-- {i}. -->\n    <section class="{cls}">\n      {body}\n      <aside class="notes">{notes}</aside>\n    </section>\n'

def build_html(L):
    tpl = open(os.path.join(ROOT, "maranatha-lecture1.html"), encoding="utf-8").read()
    a = tpl.index("    <!-- 1. 타이틀 -->"); b = tpl.index('    <div id="notes">')
    head, tail = tpl[:a], tpl[b:]
    head = re.sub(r"<title>.*?</title>", f"<title>{L['title']} · {L['series']} 슬라이드</title>", head, count=1)
    head = head.replace("<h1>마라나타 특강 1강 슬라이드</h1>", f"<h1>{L['series'].split(' · ')[0]} {L['key']}강 슬라이드</h1>")
    head = head.replace('<meta name="theme-color" content="#0b1530"/>', '<meta name="theme-color" content="#1c1511"/>')
    head = head.replace("  </style>", EXTRA_CSS + "  </style>", 1)
    slides = "".join(slide_html(i+1, s) for i, s in enumerate(L["slides"]))
    out = head + slides.lstrip("\n") + "\n" + tail
    fn = os.path.join(ROOT, L["slug"] + ".html")
    open(fn, "w", encoding="utf-8", newline="\n").write(out)
    return fn

# ───────────────────────── PPTX 생성 ─────────────────────────
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

C = dict(bg=RGBColor(0x1C,0x15,0x11), ink=RGBColor(0xFF,0xF7,0xEC), sub=RGBColor(0xEC,0xD9,0xBF), dim=RGBColor(0xA8,0x92,0x7A),
         gold=RGBColor(0xF5,0xBD,0x62), box=RGBColor(0x2A,0x1F,0x18), line=RGBColor(0x4A,0x3A,0x2E))
SANS, SERIF = "맑은 고딕", "바탕"

def runs(par, text, size, color, font=SANS, bold=False):
    """<em>…</em>(금색), <b>…</b>(굵게), <b class="gold">, <br/> 를 런으로 바꾼다"""
    text = text.replace("<br/>", "\n")
    parts = re.split(r'(<em>.*?</em>|<b(?: class="gold")?>.*?</b>)', text)
    first = True
    for p in parts:
        if not p: continue
        col, bd = color, bold
        if p.startswith("<em>"): p, col = p[4:-5], C["gold"]
        elif p.startswith('<b class="gold">'): p, col, bd = p[16:-4], C["gold"], True
        elif p.startswith("<b>"): p, bd = p[3:-4], True
        p = html.unescape(re.sub(r"<[^>]+>", "", p))
        segs = p.split("\n")
        for k, seg in enumerate(segs):
            if k > 0:
                par = par._parent.add_paragraph(); par.alignment = par_align_of(par)
            r = par.add_run(); r.text = seg
            f = r.font; f.size = Pt(size); f.color.rgb = col; f.bold = bd; f.name = font
            r._r.get_or_add_rPr().set("lang", "ko-KR")
            ea = r._r.get_or_add_rPr().find('{http://schemas.openxmlformats.org/drawingml/2006/main}ea')
    return par

_ALIGN = {}
def par_align_of(p): return _ALIGN.get(id(p._parent), PP_ALIGN.LEFT)

def tb(slide, x, y, w, hgt, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(hgt))
    tf = box.text_frame; tf.word_wrap = True; tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Inches(0.05); tf.margin_top = tf.margin_bottom = Inches(0.03)
    _ALIGN[id(tf)] = align
    tf.paragraphs[0].alignment = align
    return tf

def para(tf, first=False, space=8, align=None):
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    p.alignment = align if align is not None else _ALIGN.get(id(tf), PP_ALIGN.LEFT)
    p.space_after = Pt(space)
    return p

def rect(slide, x, y, w, hgt, fill=None, line=None, lw=1.5, shape=MSO_SHAPE.ROUNDED_RECTANGLE):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(hgt))
    if fill is None: s.fill.background()
    else: s.fill.solid(); s.fill.fore_color.rgb = fill
    if line is None: s.line.fill.background()
    else: s.line.color.rgb = line; s.line.width = Pt(lw)
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        s.adjustments[0] = 0.08
    s.shadow.inherit = False
    return s

def eyebrow(slide, txt):
    tf = tb(slide, 0.8, 0.45, 11.7, 0.5)
    runs(para(tf, True), txt, 18, C["gold"], bold=True)

def title(slide, txt, y=1.0, size=40, align=PP_ALIGN.LEFT, w=11.7, x=0.8, hgt=1.6):
    tf = tb(slide, x, y, w, hgt, align=align)
    runs(para(tf, True, 0), txt, size, C["ink"], bold=True)
    return tf

def add_slide_pptx(prs, s):
    sl = prs.slides.add_slide(prs.slide_layouts[6])
    sl.background.fill.solid(); sl.background.fill.fore_color.rgb = C["bg"]
    t = s["t"]
    if t in ("title",):
        tf = tb(sl, 0.8, 1.2, 11.7, 0.5, PP_ALIGN.CENTER); runs(para(tf, True), s["eb"], 16, C["gold"], bold=True)
        title(sl, s["h"], y=1.9, size=60, align=PP_ALIGN.CENTER, hgt=2.6)
        tf = tb(sl, 1.0, 4.45, 11.3, 2.7, PP_ALIGN.CENTER)
        big = 30 if len(s["lines"]) <= 2 else 25
        for k, l in enumerate(s["lines"]):
            small = "인사이트 브리핑" in l
            runs(para(tf, k == 0, 10), l, 20 if small else big, C["dim"] if small else C["sub"])
    elif t == "divider":
        pill = rect(sl, 4.67, 1.7, 4.0, 1.0, fill=C["gold"])
        tfp = pill.text_frame; tfp.vertical_anchor = MSO_ANCHOR.MIDDLE
        runs(para(tfp, True, 0, PP_ALIGN.CENTER), s["num"], 34, RGBColor(0x2A, 0x1A, 0x05), bold=True)
        title(sl, s["h"], y=2.95, size=58, align=PP_ALIGN.CENTER, hgt=2.3)
        tf = tb(sl, 1.2, 5.4, 10.9, 0.8, PP_ALIGN.CENTER); runs(para(tf, True), s.get("sub", ""), 30, C["sub"])
    elif t == "text":
        eyebrow(sl, s["eb"]); title(sl, s["h"], size=44, hgt=1.9)
        n = len(s["lines"]); size = 32 if n <= 3 else 28
        tf = tb(sl, 0.8, 3.0, 11.9, 4.3)
        for k, l in enumerate(s["lines"]):
            p = para(tf, k == 0, 14); runs(p, "•  " + l if not l.startswith("“") else l, size if len(re.sub(r"<[^>]+>","",l)) < 44 else size - 3, C["sub"])
    elif t == "verse":
        ref, en, ko = s["v"]
        eyebrow(sl, s["eb"])
        rect(sl, 0.8, 1.25, 0.09, 4.6, fill=C["gold"], shape=MSO_SHAPE.RECTANGLE)
        size = 38 if len(ko) < 90 else 32 if len(ko) < 170 else 27
        tf = tb(sl, 1.15, 1.2, 11.2, 4.4, anchor=MSO_ANCHOR.MIDDLE)
        runs(para(tf, True, 12), ko, size, C["ink"], font=SERIF)
        runs(para(tf, False, 0), ko_ref(ref), 22, C["gold"], bold=True)
        tf2 = tb(sl, 1.15, 5.95, 11.2, 1.2)
        runs(para(tf2, True, 0), f"{ref} (KJV) — {en}", 13 if len(en) < 260 else 11, C["dim"])
    elif t == "wow":
        eyebrow(sl, s["eb"])
        if s.get("h"): title(sl, s["h"], size=40, hgt=1.0)
        txt = s["text"]; size = 27 if len(txt) < 200 else 25 if len(txt) < 250 else 23 if len(txt) < 300 else 21 if len(txt) < 350 else 19.5
        box = rect(sl, 0.7, 2.05, 11.9, 5.1, fill=RGBColor(0x2C, 0x21, 0x18), line=C["gold"], lw=2)
        tfb = box.text_frame; tfb.word_wrap = True; tfb.vertical_anchor = MSO_ANCHOR.MIDDLE
        tfb.margin_left = tfb.margin_right = Inches(0.45); tfb.margin_top = tfb.margin_bottom = Inches(0.25)
        runs(para(tfb, True, 0, PP_ALIGN.LEFT), txt, size, C["ink"], font=SERIF)
    elif t == "table":
        eyebrow(sl, s["eb"]); title(sl, s["h"], size=40, hgt=1.0)
        rows, cols = len(s["rows"]) + 1, len(s["head"])
        top = 2.15; hgt = 0.7 + (0.95 if s.get("foot") else 1.2) * len(s["rows"])
        gt = sl.shapes.add_table(rows, cols, Inches(0.8), Inches(top), Inches(11.7), Inches(hgt)).table
        widths = {3: [3.3, 5.6, 2.8], 2: [5.85, 5.85]}.get(cols, [11.7 / cols] * cols)
        if cols == 3 and s["head"][0] == "": widths = [1.6, 5.3, 4.8]
        if cols == 3 and s["head"][0] == "칸": widths = [1.7, 5.6, 4.4]
        for j, wv in enumerate(widths): gt.columns[j].width = Inches(wv)
        fs = 22 if cols == 3 else 28
        for j, hv in enumerate(s["head"]):
            c = gt.cell(0, j); c.fill.solid(); c.fill.fore_color.rgb = RGBColor(0x3A, 0x2A, 0x1A)
            c.text_frame.paragraphs[0].text = ""; runs(c.text_frame.paragraphs[0], hv, fs, C["gold"], bold=True)
        for i, r in enumerate(s["rows"]):
            for j, v in enumerate(r):
                c = gt.cell(i + 1, j); c.fill.solid(); c.fill.fore_color.rgb = C["box"] if i % 2 == 0 else RGBColor(0x24, 0x1B, 0x15)
                c.text_frame.word_wrap = True
                runs(c.text_frame.paragraphs[0], v, fs, C["gold"] if j == 0 else C["sub"], bold=(j == 0))
        if s.get("foot"):
            tf = tb(sl, 0.8, top + hgt + 0.2, 11.9, 1.2); runs(para(tf, True), s["foot"], 22, C["sub"])
    elif t == "cols":
        eyebrow(sl, s["eb"]); title(sl, s["h"], size=40, hgt=1.0)
        n = len(s["cols"]); gap = 0.3; w = (11.7 - gap * (n - 1)) / n
        hgt = 3.75 if s.get("foot") else 4.75
        for j, (a, b) in enumerate(s["cols"]):
            box = rect(sl, 0.8 + j * (w + gap), 2.3, w, hgt, fill=C["box"], line=C["gold"] if j == 0 else C["line"], lw=1.5)
            tfb = box.text_frame; tfb.word_wrap = True; tfb.vertical_anchor = MSO_ANCHOR.TOP
            tfb.margin_left = tfb.margin_right = Inches(0.3); tfb.margin_top = Inches(0.3)
            runs(para(tfb, True, 12, PP_ALIGN.LEFT), a, 28 if n == 3 else 32, C["gold"] if j == 0 else C["ink"], bold=True)
            runs(para(tfb, False, 0, PP_ALIGN.LEFT), b, 23 if n == 3 else 25, C["sub"])
        if s.get("foot"):
            tf = tb(sl, 0.8, 6.25, 11.9, 1.0); runs(para(tf, True), s["foot"], 26, C["sub"])
    elif t == "prayer":
        eyebrow(sl, s["eb"]); title(sl, s["h"], size=40, hgt=1.0)
        rect(sl, 0.8, 2.2, 0.09, 4.8, fill=C["gold"], shape=MSO_SHAPE.RECTANGLE)
        tf = tb(sl, 1.15, 2.15, 11.2, 5.0)
        for k, l in enumerate(s["lines"]): runs(para(tf, k == 0, 8), l, 26, C["ink"], font=SERIF)
    # 쪽 번호
    tfn = tb(sl, 11.3, 7.0, 1.6, 0.35, PP_ALIGN.RIGHT); runs(para(tfn, True, 0), f"{len(prs.slides)}", 11, C["dim"])
    # 발표자 노트 = 원고 문단
    if s.get("notes"):
        sl.notes_slide.notes_text_frame.text = s["notes"]

def build_pptx(L):
    prs = Presentation(); prs.slide_width = Inches(13.333); prs.slide_height = Inches(7.5)
    for s in L["slides"]: add_slide_pptx(prs, s)
    fn = os.path.join(ROOT, "files", L["pptx"] + ".pptx")
    prs.save(fn); return fn

if __name__ == "__main__":
    which = sys.argv[1:] or ["1", "2"]
    for L in (lecture1(), lecture2()):
        if L["key"] not in which: continue
        print("HTML:", build_html(L), f"({len(L['slides'])}장)")
        print("PPTX:", build_pptx(L))
