# -*- coding: utf-8 -*-
"""외국어 성경 인용(퍼블릭 도메인)을 위키문헌 원문에서 가져와 i18n/bible-verses.json 에 채운다.

  es = Reina-Valera 1909 (es.wikisource 'Biblia Reina-Valera 1909/<책>/<장>')
  ja = 文語訳 (ja.wikisource '<책>(文語訳)' — 신약 大正改訳·구약 明治元訳)
  zh = 和合本 神版 繁體 (zh.wikisource '聖經 (和合本)/<책>')
  ※ 일본어 口語訳은 저작권 분쟁 소지로 쓰지 않는다.

사용: python tools/fetch_ws_verses.py tools/rapture/ko.json [다른 원고 …]
  원고의 {"v": "Book 장:절"} 을 모두 모아, bible-verses.json 에 없는 절만 가져온다. 못 가져온 절은 목록으로 알려 준다.
"""
import json, re, sys, os, urllib.request, urllib.parse
try: sys.stdout.reconfigure(encoding='utf-8')
except Exception: pass
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = f'{ROOT}/i18n/bible-verses.json'
B = {  # 약호: (es, zh, ja)
 'Gen': ('Génesis', '創世記', '創世記(文語訳)'), 'Isa': ('Isaías', '以賽亞書', 'イザヤ書(文語訳)'),
 'Jer': ('Jeremías', '耶利米書', 'ヱレミヤ記(文語訳)'), 'Eze': ('Ezequiel', '以西結書', 'エゼキエル書(文語訳)'),
 'Dan': ('Daniel', '但以理書', 'ダニエル書(文語訳)'), 'Zec': ('Zacarías', '撒迦利亞書', 'ゼカリヤ書(文語訳)'),
 'Mat': ('Mateo', '馬太福音', 'マタイ傳福音書(文語訳)'), 'Luk': ('Lucas', '路加福音', 'ルカ傳福音書(文語訳)'),
 'Joh': ('Juan', '約翰福音', 'ヨハネ傳福音書(文語訳)'), 'Act': ('Hechos', '使徒行傳', '使徒行傳(文語訳)'),
 'Rom': ('Romanos', '羅馬書', 'ロマ人への書(文語訳)'), '1Co': ('1_Corintios', '哥林多前書', 'コリント人への前の書(文語訳)'),
 '2Co': ('2_Corintios', '哥林多後書', 'コリント人への後の書(文語訳)'), 'Eph': ('Efesios', '以弗所書', 'エペソ人への書(文語訳)'),
 'Php': ('Filipenses', '腓立比書', 'ピリピ人への書(文語訳)'), 'Col': ('Colosenses', '歌羅西書', 'コロサイ人への書(文語訳)'),
 '1Th': ('1_Tesalonicenses', '帖撒羅尼迦前書', 'テサロニケ人への前の書(文語訳)'),
 '2Th': ('2_Tesalonicenses', '帖撒羅尼迦後書', 'テサロニケ人への後の書(文語訳)'),
 'Tit': ('Tito', '提多書', 'テトスへの書(文語訳)'), 'Heb': ('Hebreos', '希伯來書', 'ヘブル人への書(文語訳)'),
 'Jas': ('Santiago', '雅各書', 'ヤコブの書(文語訳)'), '2Pe': ('2_Pedro', '彼得後書', 'ペテロの後の書(文語訳)'),
 '1Jo': ('1_Juan', '約翰一書', 'ヨハネの第一の書(文語訳)'), 'Rev': ('Apocalipsis', '啟示錄', 'ヨハネの默示録(文語訳)'),
}
_cache = {}
def raw(site, title):
    k = (site, title)
    if k in _cache: return _cache[k]
    t = ''
    for _ in range(3):
        u = f'https://{site}.wikisource.org/wiki/{urllib.parse.quote(title)}?action=raw'
        t = urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0 (bible-study site; verse lookup)'})).read().decode('utf-8')
        m = re.match(r'\s*#(?:転送|REDIRECT|重定向)\s*\[\[([^\]]+)\]\]', t, re.I)
        if not m: break
        title = m.group(1)
    _cache[k] = t
    return t
def clean(s):
    s = re.sub(r'<ref.*?</ref>|<[^>]+>', '', s, flags=re.S)
    s = re.sub(r'\{\{(?:udots|ruby|r)\|([^{}|]*)(?:\|[^{}]*)?\}\}', r'\1', s)
    s = re.sub(r'\{\{[^{}]*\}\}', '', s)
    s = re.sub(r'\[\[(?:[^|\]]*\|)?([^\]]*)\]\]', r'\1', s)
    return re.sub(r'[ \t\r\n]+', ' ', s).strip()
def verse(site, text, c, v):
    if site == 'es':
        m = re.search(r'\{\{vers\|%d\|%d\}\}(.*?)(?=\{\{vers\||</poem>|$)' % (c, v), text, re.S)
    elif site == 'zh':
        m = re.search(r'\{\{verse\|%d\|%d\}\}(.*?)(?=\{\{verse\||==|$)' % (c, v), text, re.S)
    else:
        m = (re.search(r'=+\s*%d:%d\s*=+\s*\n(.*?)(?=\n=+|$)' % (c, v), text, re.S)
             or re.search(r'\{\{verse\|%d\|%d\}\}(.*?)(?=\{\{verse\||\n==|$)' % (c, v), text, re.S))
    return clean(m.group(1)) if m else None
def refs_in(o, acc):
    if isinstance(o, dict):
        if isinstance(o.get('v'), str): acc.append(o['v'])
        for x in o.values(): refs_in(x, acc)
    elif isinstance(o, list):
        for x in o: refs_in(x, acc)
def expand(ref):
    m = re.match(r'^(\w+) (\d+):([\d,\-]+)$', ref); book, c = m.group(1), int(m.group(2)); vs = []
    for part in m.group(3).split(','):
        if '-' in part: a, b = part.split('-'); vs += range(int(a), int(b) + 1)
        else: vs.append(int(part))
    return [(book, c, v) for v in vs]
def main():
    db = json.load(open(OUT, encoding='utf-8')) if os.path.exists(OUT) else {}
    refs = []
    for p in sys.argv[1:]: refs_in(json.load(open(p, encoding='utf-8')), refs)
    todo = sorted({x for r in refs for x in expand(r)}, key=lambda t: (t[0], t[1], t[2]))
    miss = []
    for book, c, v in todo:
        key = f'{book} {c}:{v}'; cur = db.get(key, {})
        if all(cur.get(L) for L in ('es', 'ja', 'zh')): continue
        es, zh, ja = B[book]
        try:
            if not cur.get('es'): cur['es'] = verse('es', raw('es', f'Biblia Reina-Valera 1909/{es}/{c}'), c, v)
            if not cur.get('zh'): cur['zh'] = verse('zh', raw('zh', f'聖經 (和合本)/{zh}'), c, v)
            if not cur.get('ja'): cur['ja'] = verse('ja', raw('ja', ja), c, v)
        except Exception as e:
            print('  오류', key, e)
        for L in ('es', 'ja', 'zh'):
            if not cur.get(L): miss.append(f'{key} {L}')
        db[key] = {k: x for k, x in cur.items() if x}
        print(key, '·'.join(L for L in ('es', 'ja', 'zh') if cur.get(L)))
    json.dump(db, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('못 가져온 절:', miss or '없음')
if __name__ == '__main__':
    main()
