"""Projection, bootstrap p(bargain), rupees-per-win fair price, hedonic market lens, and 2026 backtest."""
import pandas as pd, numpy as np, json, warnings; warnings.filterwarnings('ignore')
from scipy.stats import spearmanr
pm=pd.read_parquet('out/player_match_war.parquet'); pr=pd.read_csv('out/prices_matched.csv')
site=json.load(open('out/site_data.json')); roles={p['n']:p['role'] for p in site['players']}
OS={p['n'] for p in site['players'] if p['os']}
ps_old=pd.read_csv('out/player_seasons.csv')
W={1:5,2:4,3:3}; MIN=0.3; rng=np.random.default_rng(7)
season=pm.groupby(['player','season']).agg(war=('war','sum'),wb=('war_bat','sum'),wo=('war_bowl','sum'),m=('match_id','size')).reset_index()
def project(T,k):
    x=season[season.season.between(T-3,T-1)].copy(); x['w']=(T-x.season).map(W)
    g=x.assign(ww=x.w*x.war,wb_=x.w*x.wb,wo_=x.w*x.wo,wm=x.w*x.m).groupby('player')[['ww','wb_','wo_','wm','m']].sum()
    out=pd.DataFrame({'proj':g.ww/(g.wm+k)*14,'pb':g.wb_/(g.wm+k)*14,'po':g.wo_/(g.wm+k)*14,'mprior':g.m})
    return out
# ---------- tune k on 2024 and 2025 targets (2026 kept out of sample)
def score(T,k):
    p=project(T,k); r=season[season.season==T].set_index('player').war
    j=p.join(r,how='inner'); j=j[j.mprior>=5]; return spearmanr(j.proj,j.war)[0]
ks=[0,4,8,14,20,30,40,60,80,120]
tune={k:np.mean([score(2024,k),score(2025,k)]) for k in ks}; K=max(tune,key=tune.get)
print('k tuning (mean Spearman 2024,2025):',{k:round(v,3) for k,v in tune.items()},'-> k =',K)
# ---------- bootstrap
pmx=pm.set_index('player')
def boot(T,players,n=1000):
    res={}
    for pl in players:
        if pl not in pmx.index: continue
        x=pm[(pm.player==pl)&pm.season.between(T-3,T-1)]
        if x.empty: continue
        num=np.zeros(n); den=np.zeros(n)
        for s,xs in x.groupby('season'):
            v=xs.war.values; w=W[T-s]; idx=rng.integers(0,len(v),(n,len(v)))
            num+=w*v[idx].sum(1); den+=w*len(v)
        res[pl]=num/(den+K)*14
    return res
def value(T,price_df):
    p=project(T,K); df=price_df.merge(p,left_on='cs_name',right_index=True,how='left')
    df['mprior']=df.mprior.fillna(0); el=df.mprior>=5
    R=(df.loc[el,'price_cr']-MIN).sum()/df.loc[el,'proj'].clip(lower=0).sum()
    df['fair']=np.where(el,MIN+R*df.proj.clip(lower=0),np.nan)
    B=boot(T,df.loc[el,'cs_name'])
    lo=[];hi=[];pb=[];po=[]
    for _,r in df.iterrows():
        if r.cs_name in B and r.mprior>=5:
            f=MIN+R*np.clip(B[r.cs_name],0,None); lo.append(np.percentile(f,10)); hi.append(np.percentile(f,90)); pb.append((f>r.price_cr).mean()); po.append((f<r.price_cr).mean())
        else: lo.append(np.nan); hi.append(np.nan); pb.append(np.nan); po.append(np.nan)
    df['lo']=lo; df['hi']=hi; df['pbar']=pb; df['pover']=po   # ties at the minimum price count as neither
    df['verdict']=np.select([df.pbar>=0.8,df.pover>=0.8,df.pbar.notna()],['under','over','balanced'],'na')
    return df,R
# ---------- 2026 backtest: prices are 2026 contracts (set before the season); projection uses 2023-25 only
bt,R26=value(2026,pr)
real=season[season.season==2026].set_index('player')
bt=bt.join(real[['war','m']].rename(columns={'war':'war26','m':'m26'}),on='cs_name'); bt[['war26','m26']]=bt[['war26','m26']].fillna(0)
el26=bt.mprior>=5
Rr=(bt.loc[el26,'price_cr']-MIN).sum()/bt.loc[el26,'war26'].clip(lower=0).sum()   # realised market rate, cr per realised WAR
bt['surplus']=MIN+Rr*bt.war26.clip(lower=0)-bt.price_cr   # realised value minus price
# old method on same information set
o=ps_old[ps_old.season.between(2023,2025)].copy(); o['w']=o.season.map({2025:1,2024:.6,2023:.3})
og=o.assign(a=o.w*o.raa,b=o.w*o.matches).groupby('player').agg(a=('a','sum'),b=('b','sum'),m3=('matches','sum'))
og['old']=og.a/(og.b+4)*14
bt=bt.join(og[['old','m3']],on='cs_name')
E=bt[(bt.mprior>=5)].copy()
def sp(a,b): return round(spearmanr(a,b)[0],3)
last=season[season.season==2025].set_index('player').war
E['last']=E.cs_name.map(last).fillna(0)
res={'n':len(E),
 'spearman_vs_realised_war':{'new_projection':sp(E.proj,E.war26),'old_method':sp(E.old.fillna(0),E.war26),'last_season_only':sp(E.last,E.war26),'price':sp(E.price_cr,E.war26)},
}
# old verdicts (rank-matched fair, +-3cr) for comparison
eo=E[E.m3>=8].copy(); ps_=np.sort(eo.price_cr.values)[::-1]; rk=eo.old.rank(ascending=False,method='first').astype(int)
eo['oldfair']=[ps_[r-1] for r in rk]; eo['oldv']=np.select([eo.oldfair-eo.price_cr>=3,eo.oldfair-eo.price_cr<=-3],['under','over'],'balanced')
E=E.join(eo['oldv'])
grp=lambda col:{v:{'n':int((E[col]==v).sum()),'avg_realised_surplus_cr':round(E.loc[E[col]==v,'surplus'].mean(),2),
                   'war_per_cr':round(E.loc[E[col]==v,'war26'].sum()/E.loc[E[col]==v,'price_cr'].sum(),3)} for v in ['under','balanced','over']}
res['new_verdicts']=grp('verdict'); res['old_verdicts']=grp('oldv')
res['hit_rate']={'new_under_positive_surplus':round((E[E.verdict=='under'].surplus>0).mean(),3),'new_over_negative_surplus':round((E[E.verdict=='over'].surplus<0).mean(),3),
 'old_under_positive_surplus':round((E[E.oldv=='under'].surplus>0).mean(),3),'old_over_negative_surplus':round((E[E.oldv=='over'].surplus<0).mean(),3)}
res['k']=K; res['rate_2026']=round(R26,3)
print(json.dumps(res,indent=1))
# ---------- live valuation: 2024-26 data projects 2027, against 2026 contracts
lv,R=value(2027,pr)
lv['role']=lv.player.map(roles); lv['os']=lv.player.isin(OS)
# hedonic market lens: log(price) ~ proj + overseas + role + keeper + acquisition route
h=lv[lv.mprior>=5].copy()
X=pd.DataFrame({'c':1.0,'proj':h.proj.clip(lower=0),'os':h.os.astype(float),'wk':(h.role=='WK-Batter').astype(float),
  'ar':(h.role=='All-rounder').astype(float),'bowl':(h.role=='Bowler').astype(float),
  'ret':(h['how']=='Retained').astype(float),'trd':(h['how']=='Traded').astype(float)})
y=np.log(h.price_cr); beta,*_=np.linalg.lstsq(X.values,y.values,rcond=None); resid=y-X.values@beta
smear=np.exp(resid).mean(); h['mkt']=np.exp(X.values@beta)*smear
hr2=1-resid.var()/y.var()
lv=lv.merge(h[['player','mkt']],on='player',how='left')
lv['premium']=(lv.verdict=='over')&(lv.price_cr<=1.25*lv.mkt)
coef=dict(zip(X.columns,np.round(beta,3)))
print('rate 2027 (cr per WAR):',round(R,2),' hedonic R2',round(hr2,3),coef)
print(lv.verdict.value_counts().to_dict(),' premium tags',int(lv.premium.sum()))
print(lv.sort_values('pbar',ascending=False)[['player','team','price_cr','proj','fair','lo','hi','pbar']].head(8).round(2).to_string(index=False))
print(lv[lv.verdict=='over'].sort_values('pbar')[['player','team','price_cr','proj','fair','lo','hi','pbar','mkt','premium']].head(10).round(2).to_string(index=False))
lv.to_csv('out/value_2027.csv',index=False)
res.update({'rate_2027':round(R,3),'hedonic_r2':round(hr2,3),'hedonic_coef':{k:float(v) for k,v in coef.items()},
            'os_premium_pct':round((np.exp(coef['os'])-1)*100,1),'wk_premium_pct':round((np.exp(coef['wk'])-1)*100,1),
            'rho_price_proj':sp(h.price_cr,h.proj),'n_elig':int((lv.mprior>=5).sum())})
json.dump(res,open('out/backtest.json','w'),indent=1)
