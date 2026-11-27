"""낭독용 숫자 읽기 변환 — 음성 합성(TTS)에 넣기 직전에만 쓴다(화면·쇼노트 글자는 그대로).

TTS 는 '11장'을 '열한 장'처럼 고유어로 읽는 일이 있다. 성경 장·절·편과 연도는
한자어로 읽어야 하므로('십일 장') 숫자를 미리 한글로 바꿔 넣는다.

  sino(11)            → '십일'
  for_tts('요한복음 11장 6절, 시편 27편') → '요한복음 십일장 육절, 시편 이십칠편'
  for_tts('요한복음 11:6')  → '요한복음 십일장 육절'
"""
import re

_D = '영일이삼사오육칠팔구'


def sino(n):
    """정수 → 한자어 수 읽기(만 단위까지). 0 → '영'."""
    n = int(n)
    if n == 0:
        return '영'
    out = ''
    for unit, word in ((10000, '만'), (1000, '천'), (100, '백'), (10, '십')):
        q, n = divmod(n, unit)
        if q:
            out += ('' if q == 1 and unit != 10000 else sino(q) if unit == 10000 else _D[q]) + word
    if n:
        out += _D[n]
    return out


# 한자어로 읽는 단위(성경 장·절·편, 연·월·일 등). '번·개·명·사람' 같은 고유어 단위는 건드리지 않는다.
_UNITS = '장|절|편|년|월|일|세기|대|권|퍼센트|%'


def for_tts(text):
    # 1) '11:6' / '11:6-8' 꼴 장절 표기 → '십일장 육절(부터 팔절까지)'
    def chv(m):
        s = f'{sino(m.group(1))}장 {sino(m.group(2))}절'
        if m.group(3):
            s += f'부터 {sino(m.group(3))}절까지'
        return s
    text = re.sub(r'(\d+)\s*:\s*(\d+)(?:\s*[-~]\s*(\d+))?', chv, text)
    # 2) 숫자 + 한자어 단위
    text = re.sub(rf'(\d+)\s*({_UNITS})', lambda m: sino(m.group(1)) + ('퍼센트' if m.group(2) == '%' else m.group(2)), text)
    return text


if __name__ == '__main__':
    for t in ['요한복음 11장 6절', '시편 27편 14절', '요한계시록 22장 20절', '요 11:6', '롬 8:28-30',
              '아브라함은 25년, 요셉은 13년', '고린도후서 12장 9절', '시편 119편 105절', '2026년']:
        print(t, '→', for_tts(t))
