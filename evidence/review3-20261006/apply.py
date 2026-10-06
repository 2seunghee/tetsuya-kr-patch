"""Apply approved fixes (id->target JSON files given as args) into the matching r??p?.reviewed.json drafts."""
import json,glob,sys
fix={}
for p in sys.argv[1:]:
    fix.update(json.load(open(p,encoding='utf-8')))
files={}
for p in sorted(glob.glob('assets/translation/drafts/r*.reviewed.json')):
    files[p]=json.load(open(p,encoding='utf-8'))
n=0; missing=[]
for i,t in fix.items():
    hit=[p for p,d in files.items() if i in d]
    if not hit: missing.append(i); continue
    for p in hit:
        if files[p][i]!=t: files[p][i]=t; n+=1
for p,d in files.items():
    json.dump(d,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=1)
print('applied',n,'missing',missing)
