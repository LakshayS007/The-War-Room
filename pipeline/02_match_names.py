import pandas as pd, json, unicodedata, re
pr=pd.read_csv('pipeline/prices_2026.csv'); pdx=pd.read_csv('data/IPL-DATASET/csv/2024_players_details.csv')
mt=pd.read_parquet('out/matches.parquet')
cs=set()
for s,pl in zip(mt.season,mt.players):
    if s>=2022:
        for t,v in json.loads(pl).items(): cs.update(v)
norm=lambda s: re.sub(r'[^a-z ]','',unicodedata.normalize('NFKD',s).lower()).strip()
long2cs={norm(l):n for l,n in zip(pdx.longName,pdx.Name)}
out=[];unres=[]
for _,r in pr.iterrows():
    n=norm(r.player); hit=None
    if n in long2cs and long2cs[n] in cs: hit=long2cs[n]
    elif r.player in cs: hit=r.player
    else:
        parts=n.split(); sur=parts[-1]; fi=parts[0][0]
        c=[x for x in cs if norm(x).split()[-1]==sur and norm(x)[0]==fi]
        if len(c)==1: hit=c[0]
        else:
            c2=[x for x in cs if norm(x).split()[-1]==sur]
            unres.append((r.player,c or c2))
    out.append(hit)
pr['cs_name']=out
# Names the automatic matcher gets wrong or can't find (checked by hand against Cricsheet's registry).
# None = no IPL appearance yet, so the player is left unmatched rather than paired with the wrong person.
OVERRIDES={'Aman Khan':'Aman Hakim Khan','Amit Kumar':None,'Finn Allen':'FH Allen','Kamindu Mendis':'PHKD Mendis',
  'Mangesh Yadav':None,'Mukul Choudhary':'MD Choudhary','Rasikh Dar':'Rasikh Salam','Shahrukh Khan':'M Shahrukh Khan',
  'Smaran Ravichandran':'R Smaran','Varun Chakaravarthy':'CV Varun','Wanindu Hasaranga':'PWH de Silva','Yudhvir Singh Charak':'Yudhvir Singh'}
for k,v in OVERRIDES.items(): pr.loc[pr.player==k,'cs_name']=v
unres=[u for u in unres if u[0] not in OVERRIDES]
pr.to_csv('out/prices_matched.csv',index=False)
print('matched',pr.cs_name.notna().sum(),'of',len(pr))
for u in unres: print(u)
