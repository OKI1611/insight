# -*- coding: utf-8 -*-
"""ISBN(13자리) → 인쇄용 EAN-13 바코드 PNG 생성기.

  사용:  python tools/make_isbn_barcode.py 9791198765432
         python tools/make_isbn_barcode.py 979-11-987654-3-2 --price 38000

  · 체크디지트를 검증한다(틀리면 거부하고 올바른 값을 알려 준다)
  · 600dpi 인쇄용 PNG + 화면 확인용 PNG를 함께 만든다
  · 산출: 책원고/출판준비/barcode/
  외부 라이브러리 없이 EAN-13 인코딩을 직접 구현했다(Pillow만 사용).
"""
import os, re, sys
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "책원고", "출판준비", "barcode")

# EAN-13 인코딩 표
L = ["0001101", "0011001", "0010011", "0111101", "0100011",
     "0110001", "0101111", "0111011", "0110111", "0001011"]
G = ["0100111", "0110011", "0011011", "0100001", "0111001",
     "0000101", "0010001", "0001001", "0010111", "0001111"]
R = ["1110010", "1100110", "1101100", "1000010", "1011100",
     "1001110", "1010000", "1000100", "1001000", "1110100"]
PARITY = ["LLLLLL", "LLGLGG", "LLGGLG", "LLGGGL", "LGLLGG",
          "LGGLLG", "LGGGLL", "LGLGLG", "LGLGGL", "LGGLGL"]


def check_digit(d12):
    s = sum(int(c) * (3 if i % 2 else 1) for i, c in enumerate(d12))
    return (10 - s % 10) % 10


def normalize(raw):
    d = re.sub(r"[^0-9]", "", raw)
    if len(d) == 12:
        d += str(check_digit(d))
        print("  체크디지트 자동 계산 → %s" % d)
    if len(d) != 13:
        sys.exit("오류: ISBN은 하이픈 제외 13자리여야 합니다 (입력 %d자리)" % len(d))
    if not d.startswith(("978", "979")):
        sys.exit("오류: 도서 ISBN은 978 또는 979로 시작합니다 (입력 %s)" % d[:3])
    ok = check_digit(d[:12])
    if int(d[12]) != ok:
        sys.exit("오류: 체크디지트가 틀립니다. 마지막 자리는 %d 이어야 합니다 → %s%d"
                 % (ok, d[:12], ok))
    return d


def encode(d):
    """13자리 → 95모듈 비트열"""
    bits = "101"
    for i, c in enumerate(d[1:7]):
        bits += (L if PARITY[int(d[0])][i] == "L" else G)[int(c)]
    bits += "01010"
    for c in d[7:]:
        bits += R[int(c)]
    return bits + "101"


def hyphenate(d):
    """한국 ISBN 관례 표기 979-11-XXXXXX-X-X (구간 길이는 발행자번호에 따라 다를 수 있음)"""
    return "%s-%s-%s-%s-%s" % (d[:3], d[3:5], d[5:11], d[11:12], d[12:])


def font(size):
    """바코드 숫자·ISBN 표기용(라틴)"""
    for p in (r"C:\Windows\Fonts\arial.ttf", r"C:\Windows\Fonts\malgun.ttf"):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def font_kr(size):
    """‘정가 …원’ 등 한글 표기용"""
    for p in (r"C:\Windows\Fonts\malgun.ttf", r"C:\Windows\Fonts\gulim.ttc"):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return font(size)


def render(d, module=3, height=200, quiet=11, price=None):
    bits = encode(d)
    # 여백·글자는 모듈 크기에 비례해야 인쇄용(큰 모듈)에서 숫자가 잘리지 않는다
    pad_top = module
    pad_bot = int(module * 14)
    W = (len(bits) + quiet * 2) * module
    H = height + pad_top + pad_bot
    im = Image.new("RGB", (W, H), "white")
    dr = ImageDraw.Draw(im)

    # 가드바(양끝·중앙)는 아래로 더 길게 내린다 — EAN 규격
    guards = set(range(0, 3)) | set(range(45, 50)) | set(range(92, 95))
    for i, b in enumerate(bits):
        if b != "1":
            continue
        x = (quiet + i) * module
        h = height + (int(module * 1.8) if i in guards else 0)
        dr.rectangle([x, pad_top, x + module - 1, pad_top + h], fill="black")

    f = font(int(module * 9))
    y = pad_top + height + int(module * 2.4)
    dr.text((quiet * module - dr.textlength(d[0], font=f) - module * 2, y), d[0], font=f, fill="black")
    dr.text(((quiet + 4) * module, y), d[1:7], font=f, fill="black")
    dr.text(((quiet + 51) * module, y), d[7:], font=f, fill="black")

    # 상단 표기 — 왼쪽에 ISBN, 오른쪽에 정가(겹치지 않도록 좌/우 정렬)
    ft = font(int(module * 7.5))
    fp = font_kr(int(module * 6.5))
    label = "ISBN " + hyphenate(d)
    # ISBN 은 첫 줄, 정가는 둘째 줄 오른쪽 — 한 줄에 몰면 긴 ISBN과 겹친다
    band = int(module * (21 if price else 12))
    top = Image.new("RGB", (W, H + band), "white")
    dt = ImageDraw.Draw(top)
    x0 = quiet * module
    dt.text((x0, module * 2), label, font=ft, fill="black")
    if price:
        pl = "정가 %s원" % format(int(price), ",")
        dt.text((W - x0 - dt.textlength(pl, font=fp), module * 11), pl, font=fp, fill="black")
    top.paste(im, (0, band))
    return top


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        sys.exit(__doc__)
    price = None
    if "--price" in sys.argv:
        price = sys.argv[sys.argv.index("--price") + 1]

    d = normalize(args[0])
    os.makedirs(OUT, exist_ok=True)

    print("ISBN  %s  (%s)" % (hyphenate(d), d))
    # 인쇄용: 모듈 폭을 크게 잡아 600dpi 상당 해상도 확보
    for name, mod, h in (("인쇄용_600dpi", 8, 520), ("미리보기", 3, 200)):
        im = render(d, module=mod, height=h, price=price)
        p = os.path.join(OUT, "ISBN_%s_%s.png" % (d, name))
        im.save(p, "PNG", dpi=(600, 600) if mod == 8 else (150, 150))
        print("  %-16s %-12s %.0fKB  %s" % (name, "%dx%d" % im.size,
                                            os.path.getsize(p) / 1024, p))
    print("\n표지 뒤표지 우측 하단에 배치하십시오. 바코드 좌우 여백(quiet zone)을 침범하지 마십시오.")


if __name__ == "__main__":
    main()
