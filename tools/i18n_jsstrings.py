# -*- coding: utf-8 -*-
"""i18n_jsstrings.py — 스크립트 안에만 있는 화면 글자(로그인 뒤 화면·오류 안내·빈 목록 안내 등) 보충 추출

브라우저 추출(tools/i18n_extract.js)은 '열었을 때 그려진 화면'만 잡는다. 로그인해야 보이는 문구,
버튼을 눌러야 나오는 안내처럼 스크립트 문자열 안에만 있는 글자는 여기서 뽑는다.

사용: python tools/i18n_jsstrings.py <파일> [<파일> ...]   → JSON [{k, type:'text'|'attr', ctx}] 를 표준출력
  - '…', "…", `…` 문자열 중 한글이 든 것만. alert/confirm/prompt/console 인자는 뺀다(화면 글자가 아님).
  - 문자열 안 태그로 글자를 나누고, ${…} 가 숫자로 보이면 {n}, 아니면(이름·제목 같은 콘텐츠) 그 마디는 버린다.
  - 굵게·링크 같은 인라인 태그에 붙어 있는 조각(문장 일부)은 뺀다 — 조각 번역은 문장을 망친다.
"""
import sys, re, json, os, html as H

KO = re.compile('[가-힣]')
NUMERIC = re.compile(r'(length|count|cnt|total|num|^n$|^i$|^k$|pct|percent|done|min|sec|day|days|hour|idx|index|score|rank|size|left|remain|won|price|amount|qty|page|year|month|date|week|\+\s*1|toLocaleString|Math\.)', re.I)
INLINE = r'(?:b|strong|em|a|span|i|u|small|mark|sup|sub)'

def literals(src):
    """(문자열 내용, 앞쪽 120자) — 주석은 건너뛴다. 템플릿의 ${…} 는 \x00식\x01 로 표시."""
    i, n, out = 0, len(src), []
    while i < n:
        c = src[i]
        if src.startswith('//', i) and (i == 0 or src[i-1] != ':'):
            j = src.find('\n', i); i = n if j < 0 else j; continue
        if src.startswith('/*', i):
            j = src.find('*/', i + 2); i = n if j < 0 else j + 2; continue
        if c in '\'"':
            j, buf = i + 1, []
            while j < n and src[j] != c and src[j] != '\n':
                if src[j] == '\\' and j + 1 < n: buf.append(src[j:j+2]); j += 2; continue
                buf.append(src[j]); j += 1
            out.append((''.join(buf), src[max(0, i-120):i])); i = j + 1; continue
        if c == '`':
            j, buf = i + 1, []
            while j < n and src[j] != '`':
                if src[j] == '\\' and j + 1 < n: buf.append(src[j:j+2]); j += 2; continue
                if src.startswith('${', j):
                    d, k = 1, j + 2
                    while k < n and d:
                        if src[k] == '{': d += 1
                        elif src[k] == '}': d -= 1
                        k += 1
                    buf.append('\x00' + src[j+2:k-1] + '\x01'); j = k; continue
                buf.append(src[j]); j += 1
            out.append((''.join(buf), src[max(0, i-120):i])); i = j + 1; continue
        i += 1
    return out

def unesc(s):
    return s.replace("\\'", "'").replace('\\"', '"').replace('\\n', ' ').replace('\\`', '`').replace('\\\\', '\\')

def segments(s):
    """문자열 → [(마디, 왼쪽 인라인태그에 붙음, 오른쪽 인라인태그에 붙음)]"""
    parts = re.split(r'(<[^>]*>)', s)
    res = []
    for idx, p in enumerate(parts):
        if idx % 2 == 1 or not p.strip(): continue
        left = parts[idx-1] if idx > 0 else ''
        right = parts[idx+1] if idx + 1 < len(parts) else ''
        li = bool(re.match(r'</?' + INLINE + r'\b', left)) and bool(p[:1].strip())
        ri = bool(re.match(r'</?' + INLINE + r'\b', right)) and bool(p[-1:].strip())
        res.append((p, li, ri))
    return res

def main(files):
    out, seen = [], set()
    def add(k, t, ctx):
        if (k, t) in seen: return
        seen.add((k, t)); out.append({'k': k, 'type': t, 'ctx': ctx[:200]})
    for f in files:
        src = open(f, encoding='utf-8').read()
        if f.endswith('.html'):
            src = '\n'.join(re.findall(r'<script(?![^>]*\bsrc=)[^>]*>([\s\S]*?)</script>', src))
        for s, before in literals(src):
            if not KO.search(s): continue
            if re.search(r'(alert|confirm|prompt|console\.\w+|throw new Error)\s*\(\s*$', before): continue
            s = unesc(s)
            for m in re.finditer(r'\b(placeholder|title|aria-label|alt)="([^"\x00]*[가-힣][^"\x00]*)"', s):
                add(H.unescape(m.group(2)).strip(), 'attr', f)
            for seg, li, ri in segments(s):
                if li or ri: continue
                t = H.unescape(seg)
                ok = True
                def rep(m):
                    nonlocal ok
                    if NUMERIC.search(m.group(1)): return '{n}'
                    ok = False; return ''
                t = re.sub(r'\x00([\s\S]*?)\x01', rep, t)
                if not ok: continue
                t = re.sub(r'\s+', ' ', t).strip()
                m = re.match(r'^([\s└·•▶►→←↑↓※✓✔★☆▲▼○●◆◇■□\-–—]*)([\s\S]*?)([\s→←↑↓▶►›»]*)$', t)
                if m and m.group(2): t = m.group(2).strip()
                if len(KO.findall(t)) < 2 or '{n}{n}' in t: continue
                if re.search(r'[{}<>=;]|\bfunction\b|=>', t.replace('{n}', '')): continue
                add(t, 'text', os.path.basename(f) + ': ' + s.replace('\x00', '${').replace('\x01', '}'))
    return out

if __name__ == '__main__':

    sys.stdout.reconfigure(encoding='utf-8')
    print(json.dumps(main(sys.argv[1:]), ensure_ascii=False, indent=0))
