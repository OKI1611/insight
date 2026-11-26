# 번역 검사: python i18n/pages/_work/check.py <lang>
import json,re,sys
sys.stdout.reconfigure(encoding='utf-8')
L=sys.argv[1]
items=json.load(open('i18n/pages/_work/index.items.json',encoding='utf-8'))
tr=json.load(open(f'i18n/pages/_work/index.{L}.json',encoding='utf-8'))
bad=0
tags=lambda s:re.findall(r'<[^>]+>',s)
for it in items:
    k=it['k']; v=tr.get(k)
    if v is None: print('MISSING:',k[:80]); bad+=1; continue
    if not v.strip(): print('EMPTY:',k[:80]); bad+=1
    if re.search('[가-힣]',v): print('KOREAN LEFT:',k[:50],'=>',v[:80]); bad+=1
    if k.count('{n}')!=v.count('{n}'): print('{n} COUNT:',k[:60]); bad+=1
    if it['type']=='html' and sorted(tags(k))!=sorted(tags(v)): print('TAGS DIFFER:',k[:70]); bad+=1
extra=set(tr)-{i['k'] for i in items}
if extra: print('EXTRA KEYS:',len(extra)); bad+=1
print('OK' if not bad else f'{bad} problems')
