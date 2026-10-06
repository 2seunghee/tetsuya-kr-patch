import json,glob,re,collections,sys
ents=[]
for f in sorted(glob.glob('assets/translation/segments/*.json')):
    for e in json.load(open(f,encoding='utf-8'))['entries']:
        e['bank']=f[-11:-5]; ents.append(e)
ents.sort(key=lambda e:int(e['id'],16))
TOK=re.compile(r'<[^<>]+>|\{[A-Z0-9]+\}')
def plain(s): return TOK.sub('',s)
rep={}
# 1. same source -> different targets
by=collections.defaultdict(list)
for e in ents: by[plain(e['source']).strip()].append(e)
dup=[]
for s,es in by.items():
    ts=set(plain(x['target']).strip() for x in es)
    if len(ts)>1: dup.append({'source':s,'variants':[(x['id'],plain(x['target']).strip()) for x in es]})
rep['dup_source']=dup
# 2. glossary term check
gl=[]
for line in open('assets/translation/glossary.md',encoding='utf-8'):
    m=re.match(r'\|\s*(T\d+)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|',line)
    if m: gl.append((m.group(1),m.group(2),m.group(3)))
def alts(s):
    s=re.sub(r'\([^)]*\)|（[^）]*）|\*\*|—','',s)
    return [a.strip() for a in re.split(r'/|,|、',s) if a.strip()]
miss=[]
for tid,jp,kr in gl:
    jps=[j for j in alts(jp) if j and len(j)>=2 and not re.search(r'[A-Za-z]',j)]
    krs=[k for k in alts(kr) if k and not re.search(r'[A-Za-z]',k)]
    if not jps or not krs: continue
    for e in ents:
        src=plain(e['source'])
        if any(j in src for j in jps):
            tg=plain(e['target'])
            if not any(k.replace(' ','') in tg.replace(' ','') for k in krs):
                miss.append((tid,jp,kr,e['id'],src.replace('\n','/')[:60],tg.replace('\n','/')[:60]))
rep['glossary_miss']=miss
# 3. korean variants
VAR=[r'테츠',r'타짜',r'바이닝',r'속임수',r'\{L\}버튼',r'마작집',r'마작장',r'츠모',r'쓰모',r'롱\b',r'야쿠만',r'릿치',r'텐빠이',r'왼손기술',r'제비 뒤집기',r'겐로쿠쌓기',r'패쌓기',r'통시 ',r'오히끼',r'호구새끼',r'카모',r'단나',r'텐호',r'천화 ',r'친\b',r'자\(子\)',r'반장전',r'한장',r'도라패',r'만수패|삭수패|통수패',r'치바현',r'보소반도',r'삼배만관|배만관',r'역만관',r'형씨님',r'보슈씨',r'유우씨',r'토비씨',r'토쿠씨',r'테쯔형님',r'테쯔씨',r'단치씨',r'단치 씨',r'리사누님',r'아저씨들',r'\.\.\.',r'…{2,}',r'　',r'[ぁ-んァ-ン一-龥]',r'  ',r' \n',r'\n ',r'!\?',r'\?!',r'~',r'〜']
var=collections.defaultdict(list)
for e in ents:
    tg=e['target']
    body=TOK.sub('',tg)
    for v in VAR:
        for m in re.finditer(v,body):
            var[v].append((e['id'],body.replace('\n','/')[:70]))
rep['variants']={k:v for k,v in var.items()}
# 4. speaker speech level
NAME={'00':'테쯔야','01':'테쯔야','05':'보슈','15':'보슈','1e':'보슈?','0b':'단치','12':'단치','0c':'인나미','0d':'신','09':'토쿠조','0a':'토쿠파트너','07':'쌍둥이형','08':'쌍둥이동생','06':'토비','1a':'점장','19':'점장','10':'네즈남','11':'네즈녀','1d':'단치아버지','13':'빡빡머리','0f':'미국물','16':'나카','14':'유우','18':'마담','20':'종이브로커'}
face=None; sub=None
sp=[]
for e in ents:
    s=e['source']
    for m in re.finditer(r'<(FACE|NOFACE)(?::([0-9a-f]+))?>',s):
        face=m.group(2) if m.group(1)=='FACE' else None
    e['face']=face
    nm=NAME.get(face,face)
    body=TOK.sub('',e['target'])
    lines=[l for l in body.split('\n') if l.strip()]
    def has(p): return re.search(p,body)
    if nm=='단치':
        if has(r'습니다|ㅂ니다|습니까|십니까|십시오|세요'): sp.append(('단치-격식체',e['id'],body[:70]))
        if has(r'테쯔 씨|테쯔야 씨'): sp.append(('단치-호칭',e['id'],body[:70]))
    elif nm=='테쯔야':
        if has(r'습니다|ㅂ니다|습니까|세요|해요|어요|아요|예요|이에요|죠[」\s.!?…]|네요|거든요|라고요|니까요|데요'): sp.append(('테쯔야-존대',e['id'],body[:70]))
        if has(r'테쯔 형님'): sp.append(('테쯔야-자칭형님',e['id'],body[:70]))
    elif nm in('보슈','보슈?','인나미','유우','마담','신','토쿠조','토비'):
        if has(r'습니다|ㅂ니다|습니까|세요|어요|아요|예요|이에요|거든요|라고요|니까요'): sp.append((nm+'-존대',e['id'],body[:70]))
    if nm not in ('단치','빡빡머리',None) and has(r'테쯔 형님'): sp.append((str(nm)+'-테쯔형님',e['id'],body[:70]))
rep['speech']=sp
# 5. punctuation count mismatch
pm=[]
for e in ents:
    s=plain(e['source']); t=plain(e['target'])
    for a,b in [('「','「'),('」','」'),('『','『'),('』','』'),('！','!'),('？','?'),('【','【'),('】','】'),('（','('),('）',')')]:
        cs=s.count(a); ct=t.count(b)+ (t.count(a) if a!=b else 0)
        if a=='？': ct+=t.count('⁉')
        if a=='！': ct+=t.count('⁉')
        if cs!=ct: pm.append((a,cs,ct,e['id'],s.replace('\n','/')[:50],t.replace('\n','/')[:50]))
rep['punct']=pm
json.dump(rep,open('work/review2/audit.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
print('dup_source',len(dup)); print('glossary_miss',len(miss)); print('variants',{k:len(v) for k,v in var.items()}); print('speech',len(sp)); print('punct',len(pm))
