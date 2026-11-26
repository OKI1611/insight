# -*- coding: utf-8 -*-
"""휴거와 재림 문답 코너(rapture.html)를 5개 언어 원고로 만든다.

원고: tools/rapture/<lang>.json  (ko · en · es · ja · zh)
성경 인용: 원고에는 위치만 적는다({"v": "1Th 4:16-17"}). 본문은 자동으로 끼운다.
  ko = 킹제임스 성경 정본역 bible/kr · en = KJV 전체 본문 bible/kjv
  es = Reina-Valera 1909 · ja = 文語訳 · zh = 和合本  → i18n/bible-verses.json (위키문헌 원문, 퍼블릭 도메인)
용어는 i18n/GLOSSARY.md 를 따른다.

사용:  python tools/build_rapture.py          → rapture.html 생성
       python tools/build_rapture.py --check  → 검사만
"""
import json, re, sys, html, os
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANGS = ['ko', 'en', 'es', 'ja', 'zh']
HTML_LANG = {'ko': 'ko', 'en': 'en', 'es': 'es', 'ja': 'ja', 'zh': 'zh-Hant'}
BOOK_FILE = {'Php': 'Philippians', 'Jas': 'James', 'Rom': 'Romans', '2Pe': '2Peter', 'Heb': 'Hebrews', 'Jer': 'Jeremiah',
             'Dan': 'Daniel', 'Eph': 'Ephesians', 'Eze': 'Ezekiel', '1Jo': '1John', '2Co': '2Corinthians', 'Isa': 'Isaiah',
             'Gen': 'Genesis', 'Zec': 'Zechariah', 'Mat': 'Matthew', 'Luk': 'Luke', 'Joh': 'John', 'Act': 'Acts',
             '1Co': '1Corinthians', 'Col': 'Colossians', '1Th': '1Thessalonians', '2Th': '2Thessalonians',
             'Tit': 'Titus', 'Rev': 'Revelation'}
BOOK_NAME = {
    'ko': {'Php': '빌립보서', 'Jas': '야고보서', 'Rom': '로마서', '2Pe': '베드로후서', 'Heb': '히브리서', 'Jer': '예레미야', 'Dan': '다니엘', 'Eph': '에베소서', 'Eze': '에스겔', '1Jo': '요한일서', '2Co': '고린도후서', 'Isa': '이사야', 'Gen': '창세기', 'Zec': '스가랴', 'Mat': '마태복음', 'Luk': '누가복음', 'Joh': '요한복음', 'Act': '사도행전', '1Co': '고린도전서',
           'Col': '골로새서', '1Th': '데살로니가전서', '2Th': '데살로니가후서', 'Tit': '디도서', 'Rev': '요한계시록'},
    'en': {'Php': 'Philippians', 'Jas': 'James', 'Rom': 'Romans', '2Pe': '2 Peter', 'Heb': 'Hebrews', 'Jer': 'Jeremiah', 'Dan': 'Daniel', 'Eph': 'Ephesians', 'Eze': 'Ezekiel', '1Jo': '1 John', '2Co': '2 Corinthians', 'Isa': 'Isaiah', 'Gen': 'Genesis', 'Zec': 'Zechariah', 'Mat': 'Matthew', 'Luk': 'Luke', 'Joh': 'John', 'Act': 'Acts', '1Co': '1 Corinthians',
           'Col': 'Colossians', '1Th': '1 Thessalonians', '2Th': '2 Thessalonians', 'Tit': 'Titus', 'Rev': 'Revelation'},
    'es': {'Php': 'Filipenses', 'Jas': 'Santiago', 'Rom': 'Romanos', '2Pe': '2 Pedro', 'Heb': 'Hebreos', 'Jer': 'Jeremías', 'Dan': 'Daniel', 'Eph': 'Efesios', 'Eze': 'Ezequiel', '1Jo': '1 Juan', '2Co': '2 Corintios', 'Isa': 'Isaías', 'Gen': 'Génesis', 'Zec': 'Zacarías', 'Mat': 'Mateo', 'Luk': 'Lucas', 'Joh': 'Juan', 'Act': 'Hechos', '1Co': '1 Corintios',
           'Col': 'Colosenses', '1Th': '1 Tesalonicenses', '2Th': '2 Tesalonicenses', 'Tit': 'Tito', 'Rev': 'Apocalipsis'},
    'ja': {'Php': 'ピリピ人への手紙', 'Jas': 'ヤコブの手紙', 'Rom': 'ローマ人への手紙', '2Pe': 'ペテロの手紙 第二', 'Heb': 'ヘブル人への手紙', 'Jer': 'エレミヤ書', 'Dan': 'ダニエル書', 'Eph': 'エペソ人への手紙', 'Eze': 'エゼキエル書', '1Jo': 'ヨハネの手紙 第一', '2Co': 'コリント人への手紙 第二', 'Isa': 'イザヤ書', 'Gen': '創世記', 'Zec': 'ゼカリヤ書', 'Mat': 'マタイの福音書', 'Luk': 'ルカの福音書', 'Joh': 'ヨハネの福音書', 'Act': '使徒の働き',
           '1Co': 'コリント人への手紙 第一', 'Col': 'コロサイ人への手紙', '1Th': 'テサロニケ人への手紙 第一', '2Th': 'テサロニケ人への手紙 第二',
           'Tit': 'テトスへの手紙', 'Rev': 'ヨハネの黙示録'},
    'zh': {'Php': '腓立比書', 'Jas': '雅各書', 'Rom': '羅馬書', '2Pe': '彼得後書', 'Heb': '希伯來書', 'Jer': '耶利米書', 'Dan': '但以理書', 'Eph': '以弗所書', 'Eze': '以西結書', '1Jo': '約翰一書', '2Co': '哥林多後書', 'Isa': '以賽亞書', 'Gen': '創世記', 'Zec': '撒迦利亞書', 'Mat': '馬太福音', 'Luk': '路加福音', 'Joh': '約翰福音', 'Act': '使徒行傳', '1Co': '哥林多前書',
           'Col': '歌羅西書', '1Th': '帖撒羅尼迦前書', '2Th': '帖撒羅尼迦後書', 'Tit': '提多書', 'Rev': '啟示錄'},
}
VERSION = {'ko': '정본역', 'en': 'KJV', 'es': 'RV1909', 'ja': '文語訳', 'zh': '和合本'}
LANG_NAME = {'ko': '한국어', 'en': 'English', 'es': 'Español', 'ja': '日本語', 'zh': '中文(繁體)'}

_cache = {}
def chapter(lang, book, c):
    k = (lang, book, c)
    if k not in _cache:
        if lang == 'ko':
            _cache[k] = json.load(open(f'{ROOT}/bible/kr/{BOOK_FILE[book]}-{c}.json', encoding='utf-8'))
        else:
            # 영어는 전체 KJV(bible/kjv/<책>.json). bible/en 의 'en' 은 학습용으로 줄인 절이 섞여 있어 쓰지 않는다(2026-11-26)
            _cache[k] = json.load(open(f'{ROOT}/bible/kjv/{BOOK_FILE[book]}.json', encoding='utf-8'))[str(c)]
    return _cache[k]

FOREIGN = json.load(open(f'{ROOT}/i18n/bible-verses.json', encoding='utf-8'))

def parse_ref(ref):
    m = re.match(r'^(\w+) (\d+):([\d,\-]+)$', ref)
    if not m: raise ValueError('잘못된 구절 표기: ' + ref)
    book, c, spec = m.group(1), int(m.group(2)), m.group(3)
    vs = []
    for part in spec.split(','):
        if '-' in part:
            a, b = part.split('-'); vs += list(range(int(a), int(b) + 1))
        else:
            vs.append(int(part))
    return book, c, vs, spec

def verse_texts(lang, ref):
    book, c, vs, spec = parse_ref(ref)
    out = []
    for v in vs:
        if lang in ('ko', 'en'):
            t = chapter(lang, book, c)[v - 1]
        else:
            t = (FOREIGN.get(f'{book} {c}:{v}') or {}).get(lang)
            if not t: raise KeyError(f'{lang} 성경 본문 없음: {book} {c}:{v} — i18n/bible-verses.json 에 추가할 것')
        out.append((v, t.strip()))
    return book, c, spec, out

def esc(s): return html.escape(str(s), quote=True)

def inline(s, lang, fn_seen):
    s = esc(s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s)
    def fn(m):
        n = m.group(1); fn_seen.add(int(n))
        return f'<sup class="fr"><a href="#{lang}-fn{n}" id="{lang}-fr{n}">{n}</a></sup>'
    return re.sub(r'\[\^(\d+)\]', fn, s)

def block(b, lang, fn_seen, D):
    if 'p' in b: return f'<p>{inline(b["p"], lang, fn_seen)}</p>'
    if 'h3' in b: return f'<h3>{inline(b["h3"], lang, fn_seen)}</h3>'
    if 'note' in b: return f'<div class="callout">{inline(b["note"], lang, fn_seen)}</div>'
    if 'v' in b:
        book, c, spec, vv = verse_texts(lang, b['v'])
        body = ' '.join((f'<sup class="vn">{v}</sup>' if len(vv) > 1 else '') + esc(t) for v, t in vv)
        sep = ' ' if lang in ('en', 'es') else ' '
        cite = f'{BOOK_NAME[lang][book]}{sep}{c}:{spec}'
        return (f'<blockquote class="vs" lang="{HTML_LANG[lang]}"><p>{body}</p>'
                f'<cite>{esc(cite)} · {esc(D.get("verse_label", VERSION[lang]))}</cite></blockquote>')
    if 'ul' in b:
        return '<ul class="bl">' + ''.join(f'<li>{inline(x, lang, fn_seen)}</li>' for x in b['ul']) + '</ul>'
    if 'table' in b:
        t = b['table']
        h = '<div class="tw"><table><thead><tr>' + ''.join(f'<th>{inline(x, lang, fn_seen)}</th>' for x in t['head']) + '</tr></thead><tbody>'
        for r in t['rows']:
            h += '<tr>' + ''.join(f'<td data-h="{esc(t["head"][i]) if i < len(t["head"]) else ""}">{inline(x, lang, fn_seen)}</td>' for i, x in enumerate(r)) + '</tr>'
        return h + '</tbody></table></div>'
    if 'qa' in b:
        h = ''
        for i, q in enumerate(b['qa']):
            h += (f'<div class="qa"><p class="q"><span>Q</span>{inline(q["q"], lang, fn_seen)}</p><div class="a">'
                  + ''.join(block(x, lang, fn_seen, D) for x in q['a']) + '</div></div>')
        return h
    raise ValueError('알 수 없는 블록: ' + json.dumps(b, ensure_ascii=False)[:80])

def article(D):
    lang = D['lang']; fn_seen = set()
    secs = D['sections']
    toc = ''.join(f'<a href="#{lang}-{s["id"]}">{esc(s["h"])}</a>' for s in secs)
    toc += f'<a href="#{lang}-notes">{esc(D["notes_label"])} · {esc(D["refs_label"])}</a>'
    body = ''
    for s in secs:
        body += f'<section id="{lang}-{s["id"]}"><h2>{esc(s["h"])}</h2>' + ''.join(block(b, lang, fn_seen, D) for b in s['body']) + '</section>'
    notes = D['notes']
    missing = set(range(1, len(notes) + 1)) - fn_seen
    extra = {n for n in fn_seen if n > len(notes)}
    if missing or extra: raise ValueError(f'{lang}: 각주 번호 불일치 — 본문에 없는 각주 {sorted(missing)}, 각주 없는 참조 {sorted(extra)}')
    nh = ''.join(f'<li id="{lang}-fn{i}">{inline(n, lang, set())} <a class="bk" href="#{lang}-fr{i}" aria-label="{esc(D["back_label"])}">↩</a></li>'
                 for i, n in enumerate(notes, 1))
    rh = ''.join(f'<h4>{esc(g["g"])}</h4><ul>' + ''.join(f'<li>{esc(x)}</li>' for x in g['items']) + '</ul>' for g in D['refs'])
    see = ''.join(f'<a href="{esc(x["u"])}">{esc(x["t"])} →</a>' for x in D['see'])
    return f'''
  <article class="rp" data-l="{lang}" lang="{HTML_LANG[lang]}">
    <header class="hero">
      <p class="kicker">{esc(D["kicker"])}</p>
      <h1>{esc(D["title"])}<small>{esc(D["subtitle"])}</small></h1>
      <p class="lead">{esc(D["lead"])}</p>
      <p class="upd">{esc(D["updated"])}</p>
    </header>
    <nav class="toc"><p>{esc(D["toc_label"])}</p>{toc}</nav>
    {body}
    <section id="{lang}-notes" class="notes">
      <h2>{esc(D["notes_label"])}</h2><ol>{nh}</ol>
      <h2>{esc(D["refs_label"])}</h2><div class="refs">{rh}</div>
    </section>
    <nav class="see"><p>{esc(D["see_label"])}</p>{see}</nav>
  </article>'''

def main():
    check = '--check' in sys.argv
    docs = {}
    for L in LANGS:
        p = f'{ROOT}/tools/rapture/{L}.json'
        if not os.path.exists(p):
            print(f'  (원고 없음: {L}.json — 건너뜀)'); continue
        D = json.load(open(p, encoding='utf-8'))
        assert D['lang'] == L, p
        docs[L] = D
    arts = ''.join(article(docs[L]) for L in LANGS if L in docs)
    ko = docs['ko']
    if check:
        print('검사 통과:', ', '.join(docs)); return
    metas = ''.join(f'\n  <meta name="title:{L}" content="{esc(docs[L]["meta_title"])}" />\n  <meta name="desc:{L}" content="{esc(docs[L]["meta_desc"])}" />'
                    for L in docs if L != 'ko')
    alts = ''.join(f'\n  <link rel="alternate" hreflang="{HTML_LANG[L]}" href="https://biblynote.com/rapture{"" if L == "ko" else "?lang=" + L}" />' for L in docs)
    show = '\n    '.join(f'html[data-ui="{L}"] .rp[data-l="{L}"]{{display:block}}' for L in docs)
    tpl = open(f'{ROOT}/tools/rapture/template.html', encoding='utf-8').read()
    out = (tpl.replace('{{TITLE}}', esc(ko['meta_title'])).replace('{{DESC}}', esc(ko['meta_desc']))
              .replace('{{METAS}}', metas + alts).replace('{{SHOW}}', show).replace('{{ARTICLES}}', arts))
    open(f'{ROOT}/rapture.html', 'w', encoding='utf-8', newline='\r\n').write(out)
    print('rapture.html 생성:', ', '.join(docs), f'({len(out)//1024}KB)')

if __name__ == '__main__':
    main()
