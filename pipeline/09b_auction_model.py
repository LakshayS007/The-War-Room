import pandas as pd, numpy as np, json, glob, re, unicodedata
from scipy.stats import spearmanr
A=pd.read_csv('out/auction_sales.csv'); pm=pd.read_parquet('out/player_match_war_2018.parquet')
site=json.load(open('out/site_data.json')); OS26={p['n']:p['os'] for p in site['players']}; CS2OS={p['cs']:p['os'] for p in site['players'] if p['cs']}
key=lambda s:' '.join(re.sub(r'[^a-z ]','',unicodedata.normalize('NFKD',str(s)).lower()).split())
# 1) nationality: trust the verified 2026 squad list where the player is in it
fixed=0
for i,r in A.iterrows():
    v=CS2OS.get(r.cs) if isinstance(r.cs,str) else None
    if v is None: v=next((OS26[n] for n in OS26 if key(n)==key(r['name'])),None)
    if v is not None and bool(v)!=bool(r.os): A.at[i,'os']=v; fixed+=1
print('nationality corrections:',fixed)
# 2) previous auction price (most recent sale before this auction), 2014+
hist=[]
for f in glob.glob('data/auction_hist/IPL_Auction/*.csv'):
    y=int(re.search(r'(20\d\d)',f).group(1))
    if y<2014: continue
    a=pd.read_csv(f); a.columns=[c.strip() for c in a.columns]
    pc=[c for c in a.columns if 'Winning' in c or c.startswith('Price')][0]
    for _,r in a.iterrows():
        p=float(re.sub(r'[^0-9]','',str(r[pc])) or 0)/1e7
        if p>0: hist.append((key(r['Name']),y,p))
H=pd.DataFrame(hist,columns=['k','y','p'])
def prev(name,y):
    x=H[(H.k==key(name))&(H.y<y)]
    return (x.sort_values('y').p.iloc[-1], y-x.y.max()) if len(x) else (np.nan,np.nan)
pp=[prev(n,y) for n,y in zip(A['name'],A.year)]; A['prev']=[a for a,_ in pp]; A['prev_age']=[b for _,b in pp]
# 3) role from ball-by-ball share in the 3 seasons before the auction
sh={}
for y in A.year.unique():
    x=pm[pm.season.between(y-3,y-1)].groupby('player')[['bb','ob']].sum(); sh[y]=x
def role(cs,y):
    if not isinstance(cs,str) or cs not in sh[y].index: return 'Unknown'
    b,o=sh[y].loc[cs]; t=b+o
    if t<30: return 'Unknown'
    s=o/t; return 'Bowler' if s>0.7 else ('Batter' if s<0.2 else 'All-rounder')
A['role2']=[role(c,y) for c,y in zip(A.cs,A.year)]
PURSE={2022:90,2023:95,2024:100,2025:120,2026:120}; MEGA={2022,2025}
A['lp']=np.log(A.price/A.year.map(PURSE)*120)
def X_of(d):
    lp=np.log(d.prev.fillna(1)); hp=d.prev.notna().astype(float)
    return pd.DataFrame({'c':1.0,'projp':d.proj.clip(lower=0),'projn':d.proj.clip(upper=0),'exp':np.log1p(d.mprior),
      'os':d.os.astype(float),'mega':d.year.isin(MEGA).astype(float),'os_mini':(d.os&~d.year.isin(MEGA)).astype(float),
      'hasprev':hp,'lprev':lp*hp,'bowl':(d.role2=='Bowler').astype(float),'ar':(d.role2=='All-rounder').astype(float)},index=d.index)
def fit(d):b,*_=np.linalg.lstsq(X_of(d).values,d.lp.values,rcond=None);return b
pred=lambda b,d:X_of(d).values@b
def oos(test):
    tr,te=A[A.year!=test],A[A.year==test]; b=fit(tr); r=tr.lp-pred(b,tr); sm=np.exp(r).mean()
    pt=np.exp(pred(b,te))*sm*PURSE[test]/120
    return round(spearmanr(pt,te.price)[0],3), round(np.median(np.abs(pt-te.price)),2), round(np.median(pt/te.price),2), round(np.mean(np.abs(np.log(pt/te.price))),2)
for t in [2025,2026,2022]: print('holdout',t,'spearman, median abs err cr, median pred/actual, mean |log ratio|:',oos(t))
b=fit(A); r=A.lp-pred(b,A); sm=float(np.exp(r).mean()); sd=float(r.std())
cols=list(X_of(A).columns); print('coef',dict(zip(cols,np.round(b,3))),' resid sd',round(sd,3),' R2',round(1-r.var()/A.lp.var(),3))
A['pred']=np.exp(pred(b,A))*sm*A.year.map(PURSE)/120
print(A[A.year==2025].sort_values('price',ascending=False)[['name','os','role2','proj','prev','price','pred']].head(12).round(2).to_string(index=False))
A.to_csv('out/auction_sales2.csv',index=False)
json.dump({'cols':cols,'coef':[float(x) for x in b],'smear':sm,'sd':sd},open('out/auction_model.json','w'))
