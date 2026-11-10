"""What does the IPL auction market actually pay? Fit on real 2022-2026 auction sales."""
import pandas as pd, numpy as np, json, glob, re, unicodedata
from scipy.stats import spearmanr
pm=pd.read_parquet('out/player_match_war_2018.parquet'); pdx=pd.read_csv('data/IPL-DATASET/csv/2024_players_details.csv')
PURSE={2022:90,2023:95,2024:100,2025:120,2026:120}; MEGA={2022,2025}
rows=[]
for y in PURSE:
    f=glob.glob(f'data/auction_hist/IPL_Auction/*{y}*')[0]; a=pd.read_csv(f)
    a.columns=[c.strip() for c in a.columns]
    pc=[c for c in a.columns if 'Winning' in c or c.startswith('Price')][0]; bc=[c for c in a.columns if 'Base' in c]
    for _,r in a.iterrows():
        num=lambda s: float(re.sub(r'[^0-9]','',str(s)) or 0)/1e7
        rows.append(dict(year=y,name=str(r['Name']).strip(),os=str(r['Nationality']).strip().lower().startswith('over'),price=num(r[pc]),
             base=num(r[bc[0]]) if bc else np.nan,role=str(r.get('Role','')).strip(),team=str(r['TeamName']).strip(),
             capped=(str(r.get('Capped/UnCapped','')).strip().lower()=='capped') if 'Capped/UnCapped' in a.columns else np.nan))
A=pd.DataFrame(rows); A=A[A.price>0]
print('sales by year',A.groupby('year').size().to_dict(),' median price',A.groupby('year').price.median().round(2).to_dict())
# ---- name matching to Cricsheet names (players seen 2018-2026) ----
norm=lambda s: re.sub(r'[^a-z ]','',unicodedata.normalize('NFKD',s).lower()).split()
cs=set(pm.player)
long2cs={' '.join(norm(l)):n for l,n in zip(pdx.longName,pdx.Name)}
fix={'Rasikh Dar':'Rasikh Salam','Wanindu Hasaranga':'PWH de Silva','Varun Chakaravarthy':'CV Varun','Varun Chakravarthy':'CV Varun','Kamindu Mendis':'PHKD Mendis','Finn Allen':'FH Allen',
     'Yudhvir Singh Charak':'Yudhvir Singh','Aman Khan':'Aman Hakim Khan','Mukul Choudhary':'MD Choudhary','Shahrukh Khan':'M Shahrukh Khan','Ravichandaran Ashwin':'R Ashwin','Ravichandran Ashwin':'R Ashwin',
     'Rahmanullah Gurbaz':'Rahmanullah Gurbaz','Noor Ahmad':'Noor Ahmad','Washington Sundar':'Washington Sundar'}
def match(n):
    if n in fix and fix[n] in cs: return fix[n]
    k=' '.join(norm(n))
    if k in long2cs and long2cs[k] in cs: return long2cs[k]
    if n in cs: return n
    p=norm(n)
    if not p: return None
    sur=p[-1]; c=[x for x in cs if norm(x) and norm(x)[-1]==sur and norm(x)[0][0]==p[0][0]]
    if len(c)==1: return c[0]
    c2=[x for x in cs if ' '.join(norm(x))==k]
    return c2[0] if len(c2)==1 else None
A['cs']=A.name.map(match)
print('matched to IPL record:',round(A.cs.notna().mean(),3))
# ---- pre-auction projection (same method as the site: 5/4/3 weights, shrink k=120) ----
season=pm.groupby(['player','season']).agg(war=('war','sum'),m=('match_id','size')).reset_index()
W={1:5,2:4,3:3}; K=120
def proj(T):
    x=season[season.season.between(T-3,T-1)].copy(); x['w']=(T-x.season).map(W)
    g=x.assign(ww=x.w*x.war,wm=x.w*x.m).groupby('player')[['ww','wm','m']].sum()
    return pd.DataFrame({'proj':g.ww/(g.wm+K)*14,'mprior':g.m})
P_={y:proj(y) for y in PURSE}
A['proj']=[P_[y].proj.get(c,0.0) if isinstance(c,str) else 0.0 for y,c in zip(A.year,A.cs)]
A['mprior']=[P_[y].mprior.get(c,0) if isinstance(c,str) else 0 for y,c in zip(A.year,A.cs)]
RM={'batsman':'Batter','batter':'Batter','wicket keeper':'WK-Batter','wicket-keeper':'WK-Batter','wicketkeeper':'WK-Batter','all-rounder':'All-rounder','allrounder':'All-rounder','bowler':'Bowler'}
A['role']=A.role.str.lower().map(RM)
A.to_csv('out/auction_sales.csv',index=False)
# ---- features ----
def X_of(d):
    return pd.DataFrame({'c':1.0,'projp':d.proj.clip(lower=0),'projn':d.proj.clip(upper=0),'exp':np.log1p(d.mprior),'noipl':(d.mprior==0).astype(float),
        'os':d.os.astype(float),'mega':d.year.isin(MEGA).astype(float),'os_mini':(d.os&~d.year.isin(MEGA)).astype(float)},index=d.index)
A['lp']=np.log(A.price/A.year.map(PURSE)*120)   # prices in 2025-26 purse terms
def fit(d):
    X=X_of(d); b,*_=np.linalg.lstsq(X.values,d.lp.values,rcond=None); return b
def pred(b,d): return X_of(d).values@b
# out-of-sample: train 2022-2025, test 2026
tr,te=A[A.year<=2025],A[A.year==2026]
b=fit(tr); res=tr.lp-pred(b,tr); smear=np.exp(res).mean(); sd=res.std()
pt=np.exp(pred(b,te))*smear
print('OOS 2026: Spearman',round(spearmanr(pt,te.price)[0],3),' median abs error cr',round(np.median(np.abs(pt-te.price)),2),' median ratio pred/actual',round(np.median(pt/te.price),2))
# baseline: predict median price
print('   baseline (median) MAE',round(np.median(np.abs(te.price.median()-te.price)),2))
# final model on everything
b=fit(A); res=A.lp-pred(b,A); smear=float(np.exp(res).mean()); sd=float(res.std())
coef=dict(zip(X_of(A).columns,np.round(b,3))); print('coef',coef,' resid sd',round(sd,3),' R2',round(1-res.var()/A.lp.var(),3))
# base price relation (2025-26)
bb=A[A.base.notna()]; print('base price vs final: median final/base by base slab', bb.groupby('base').price.apply(lambda s:round((s/s.name).median(),2)).to_dict(), ' share sold at base',round((bb.price<=bb.base+1e-9).mean(),3))
# distribution facts for calibration
for y in [2025,2026]:
    x=A[A.year==y].price; print(y,'price quantiles',x.quantile([.25,.5,.75,.9,.97,1]).round(2).to_dict())
json.dump({'coef':{k:float(v) for k,v in coef.items()},'smear':smear,'sd':sd,'purse':PURSE},open('out/auction_model.json','w'))
print(A.assign(pred=np.exp(pred(b,A))*smear).query('year==2025').sort_values('price',ascending=False)[['name','os','role','proj','mprior','price','pred']].head(12).round(2).to_string(index=False))
