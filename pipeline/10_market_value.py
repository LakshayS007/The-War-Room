"""Market value for the mock auction: rank by auction model + 2026 contract, price on the real 2025 mega-auction ladder."""
import pandas as pd, numpy as np, json
A=pd.read_csv('out/auction_sales2.csv'); M=json.load(open('out/auction_model.json'))
site=json.load(open('out/site_data.json')); v=pd.read_csv('out/value_2027.csv').set_index('player')
b=np.array(M['coef'])
rows=[]
for p in site['players']:
    r=v.loc[p['n']]
    if r.verdict=='na': continue
    role={'WK-Batter':'Batter'}.get(p['role'],p['role'])
    # mega-auction pattern for established players (fit on 2022 + 2025 mega auctions; see 10b output)
    model=float(np.exp(-1.43+1.64*max(r.proj,0)+0.24*float(p['os'])+0.63*np.log1p(r.mprior)+0.32))
    score=0.4*np.log(model)+0.6*np.log(p['p'])  # the 2026 contract carries reputation the stats can't see
    rows.append(dict(n=p['n'],t=p['t'],os=p['os'],role=p['role'],price26=p['p'],fair=r.fair,proj=r.proj,model=model,score=score))
D=pd.DataFrame(rows).sort_values('score',ascending=False).reset_index(drop=True)
ladder=np.sort(A[A.year==2025].price.values)[::-1]          # real 2025 mega-auction prices, high to low
D['auc']=[ladder[i] if i<len(ladder) else 0.3 for i in range(len(D))]
D['auc']=D.auc.round(2)
print('ladder top 10',ladder[:10]); print('players valued',len(D))
print(D[['n','t','os','price26','fair','model','auc']].head(25).round(2).to_string(index=False))
print('...'); print(D[['n','price26','fair','auc']].iloc[[40,60,80,100,140]].round(2).to_string(index=False))
# sanity: compare with 2026 contract and fair price
from scipy.stats import spearmanr
print('top-10 overseas share',D.head(10).os.mean(),' top-25',D.head(25).os.mean())
print('rank corr auc vs 2026 price',round(spearmanr(D.auc,D.price26)[0],3),' vs fair',round(spearmanr(D.auc,D.fair)[0],3))
D[['n','auc','model']].to_csv('out/market_value.csv',index=False)
