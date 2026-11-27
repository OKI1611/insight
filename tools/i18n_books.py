# -*- coding: utf-8 -*-
"""성경 66권 이름(스·일·중)과 장·절 표기를 i18n/common.json 에 채운다.
기준: i18n/GLOSSARY.md §5 — 스페인어 Reina-Valera 표기, 일본어 新改訳 계열(인용 출처만 文語訳), 중국어 和合本(번체).
사용: python tools/i18n_books.py   (영어 값은 건드리지 않는다)"""
import json, os, re, sys
try: sys.stdout.reconfigure(encoding='utf-8')
except Exception: pass
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = [l.split('|') for l in '''창세기|Génesis|創世記|創世記
출애굽기|Éxodo|出エジプト記|出埃及記
레위기|Levítico|レビ記|利未記
민수기|Números|民数記|民數記
신명기|Deuteronomio|申命記|申命記
여호수아|Josué|ヨシュア記|約書亞記
사사기|Jueces|士師記|士師記
룻기|Rut|ルツ記|路得記
사무엘상|1 Samuel|サムエル記 第一|撒母耳記上
사무엘하|2 Samuel|サムエル記 第二|撒母耳記下
열왕기상|1 Reyes|列王記 第一|列王紀上
열왕기하|2 Reyes|列王記 第二|列王紀下
역대상|1 Crónicas|歴代誌 第一|歷代志上
역대하|2 Crónicas|歴代誌 第二|歷代志下
에스라|Esdras|エズラ記|以斯拉記
느헤미야|Nehemías|ネヘミヤ記|尼希米記
에스더|Ester|エステル記|以斯帖記
욥기|Job|ヨブ記|約伯記
시편|Salmos|詩篇|詩篇
잠언|Proverbios|箴言|箴言
전도서|Eclesiastés|伝道者の書|傳道書
아가|Cantares|雅歌|雅歌
이사야|Isaías|イザヤ書|以賽亞書
예레미야|Jeremías|エレミヤ書|耶利米書
예레미야애가|Lamentaciones|哀歌|耶利米哀歌
에스겔|Ezequiel|エゼキエル書|以西結書
다니엘|Daniel|ダニエル書|但以理書
호세아|Oseas|ホセア書|何西阿書
요엘|Joel|ヨエル書|約珥書
아모스|Amós|アモス書|阿摩司書
오바댜|Abdías|オバデヤ書|俄巴底亞書
요나|Jonás|ヨナ書|約拿書
미가|Miqueas|ミカ書|彌迦書
나훔|Nahúm|ナホム書|那鴻書
하박국|Habacuc|ハバクク書|哈巴谷書
스바냐|Sofonías|ゼパニヤ書|西番雅書
학개|Hageo|ハガイ書|哈該書
스가랴|Zacarías|ゼカリヤ書|撒迦利亞書
말라기|Malaquías|マラキ書|瑪拉基書
마태복음|Mateo|マタイの福音書|馬太福音
마가복음|Marcos|マルコの福音書|馬可福音
누가복음|Lucas|ルカの福音書|路加福音
요한복음|Juan|ヨハネの福音書|約翰福音
사도행전|Hechos|使徒の働き|使徒行傳
로마서|Romanos|ローマ人への手紙|羅馬書
고린도전서|1 Corintios|コリント人への手紙 第一|哥林多前書
고린도후서|2 Corintios|コリント人への手紙 第二|哥林多後書
갈라디아서|Gálatas|ガラテヤ人への手紙|加拉太書
에베소서|Efesios|エペソ人への手紙|以弗所書
빌립보서|Filipenses|ピリピ人への手紙|腓立比書
골로새서|Colosenses|コロサイ人への手紙|歌羅西書
데살로니가전서|1 Tesalonicenses|テサロニケ人への手紙 第一|帖撒羅尼迦前書
데살로니가후서|2 Tesalonicenses|テサロニケ人への手紙 第二|帖撒羅尼迦後書
디모데전서|1 Timoteo|テモテへの手紙 第一|提摩太前書
디모데후서|2 Timoteo|テモテへの手紙 第二|提摩太後書
디도서|Tito|テトスへの手紙|提多書
빌레몬서|Filemón|ピレモンへの手紙|腓利門書
히브리서|Hebreos|ヘブル人への手紙|希伯來書
야고보서|Santiago|ヤコブの手紙|雅各書
베드로전서|1 Pedro|ペテロの手紙 第一|彼得前書
베드로후서|2 Pedro|ペテロの手紙 第二|彼得後書
요한일서|1 Juan|ヨハネの手紙 第一|約翰一書
요한이서|2 Juan|ヨハネの手紙 第二|約翰二書
요한삼서|3 Juan|ヨハネの手紙 第三|約翰三書
유다서|Judas|ユダの手紙|猶大書
요한계시록|Apocalipsis|ヨハネの黙示録|啟示錄'''.split('\n')]
FMT = {  # 한국어 꼬리 → 언어별 꼬리
    '': ('', '', ''),
    ' {n}장': (' {n}', ' {n}章', ' 第{n}章'),
    ' {n}:{n}': (' {n}:{n}', ' {n}:{n}', ' {n}:{n}'),
    ' {n}:{n}-{n}': (' {n}:{n}-{n}', ' {n}:{n}-{n}', ' {n}:{n}-{n}'),
    ' {n}장 {n}절': (' {n}:{n}', ' {n}章{n}節', ' {n}章{n}節'),
}
if __name__ == '__main__':
    p = f'{ROOT}/i18n/common.json'
    d = json.load(open(p, encoding='utf-8')); n = 0
    for ko, es, ja, zh in B:
        for tail, (te, tj, tz) in FMT.items():
            k = ko + tail
            if k in d and isinstance(d[k], dict):
                d[k].update({'es': es + te, 'ja': ja + tj, 'zh': zh + tz}); n += 1
    json.dump(d, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, indent=1)
    print('채움:', n)
