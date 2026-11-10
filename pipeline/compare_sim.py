import json, numpy as np, pandas as pd
from scipy.stats import spearmanr
s=json.load(open('out/mock_sim.json')); S=pd.DataFrame(s['sales'])
A=pd.read_csv('out/auction_sales2.csv'); real=np.sort(A[A.year==2025].price.values)[::-1][:len(S)]
sim=np.sort(S.price.values)[::-1]
print('lots',s['lots'],'sold',s['sold'],'unsold',s['lots']-s['sold'])
print('median sale / expected auction price',round((S.price/S.auc).median(),2),' rank corr',round(spearmanr(S.price,S.auc)[0],2))
q=[0,4,9,19,29,39,49]
print(pd.DataFrame({'rank':[i+1 for i in q if i<len(sim)],'mock price':[sim[i] for i in q if i<len(sim)],'real 2025 price at same rank':[real[i] for i in q if i<len(sim)]}).to_string(index=False))
print('total spent mock',round(S.price.sum(),1),' real 2025 top-%d total'%len(S),round(real.sum(),1))
print(S.sort_values('price',ascending=False).head(10)[['n','team','price','auc','fair']].to_string(index=False))
