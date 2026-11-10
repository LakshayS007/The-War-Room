import pandas as pd, numpy as np, json
d=pd.read_parquet('out/deliveries.parquet'); mt=pd.read_parquet('out/matches.parquet')
pdx=pd.read_csv('data/IPL-DATASET/csv/2024_players_details.csv')
d=d.sort_values(['match_id','innings','over','ball_seq']).reset_index(drop=True)
d['legal']=((d.wides==0)&(d.noballs==0)).astype(int)
g=d.groupby(['match_id','innings'])
d['legal_before']=g.legal.cumsum()-d.legal
d['wk_before']=g.n_wkts.cumsum()-d.n_wkts
d['runs_before']=g.total.cumsum()-d.total
d['inn_total']=g.total.transform('sum')
d['phase']=pd.cut(d.over,[-1,5,14,19],labels=['PP','Middle','Death']).astype(str)
BOWLER_KINDS={'bowled','caught','lbw','stumped','caught and bowled','hit wicket'}
d['bowler_wkt']=d.wkt_kind.isin(BOWLER_KINDS)

# ---------- run expectancy (first innings, 2023-2026 impact-player era) ----------
fi=d[(d.innings==1)&(d.season>=2023)].copy()
fi['bl']=120-fi.legal_before; fi['rem']=fi.inn_total-fi.runs_before
fi=fi[fi.bl>0]
fi['ob']=(fi.legal_before//6).clip(0,19); fi['w']=fi.wk_before.clip(0,9)
cell=fi.groupby(['ob','w']).agg(rem=('rem','sum'),bl=('bl','sum'),n=('rem','size')).reset_index()
cell['rate']=cell.rem/cell.bl
# pooled rate per wicket band, used to shrink sparse cells
pool=fi.groupby('w').apply(lambda x:x.rem.sum()/x.bl.sum())
R=np.zeros((20,11))
for ob in range(20):
    for w in range(10):
        c=cell[(cell.ob==ob)&(cell.w==w)]
        n=int(c.n.iloc[0]) if len(c) else 0; r=float(c.rate.iloc[0]) if len(c) else pool.get(w,pool.iloc[-1])
        k=40; R[ob,w]=(n*r+k*pool.get(w,pool.iloc[-1]))/(n+k)
    for w in range(1,10): R[ob,w]=min(R[ob,w],R[ob,w-1])  # monotone in wickets
def RE(legal,wk):
    legal=np.asarray(legal); wk=np.asarray(wk)
    bl=120-legal; ob=np.clip(legal//6,0,19); w=np.clip(wk,0,10)
    out=bl*R[ob,np.minimum(w,10)]
    return np.where((bl<=0)|(w>=10),0.0,out)
d['re_before']=RE(d.legal_before,d.wk_before)
d['re_after_now']=RE(d.legal_before+d.legal,d.wk_before)             # ball consumed, no wicket
d['re_after']=RE(d.legal_before+d.legal,d.wk_before+d.n_wkts)
d['re_after_bowl']=RE(d.legal_before+d.legal,d.wk_before+d.bowler_wkt.astype(int))
d['wkt_cost']=d.re_after_now-d.re_after
# batter (striker) credit: own runs + ball-consumption change ; wicket cost goes to player_out
faced=d[d.wides==0].copy()
faced['bat_val']=faced.bat_runs+(faced.re_after_now-faced.re_before)
# bowler: runs charged + state change (bowler-credited wickets only)
d['charged']=d.bat_runs+d.wides+d.noballs
d['bowl_val']=d.charged+(d.re_after_bowl-d.re_before)
# baselines by season x phase
bb=faced.groupby(['season','phase']).bat_val.mean().rename('bat_base')
wk_rows=d[d.wicket&d.player_out.notna()]
wkb=wk_rows.groupby(['season','phase']).wkt_cost.sum()/faced.groupby(['season','phase']).size()
bob=d.groupby(['season','phase']).bowl_val.mean().rename('bowl_base')
faced=faced.join(bb,on=['season','phase']).join(wkb.rename('wk_base'),on=['season','phase'])
faced['bat_raa']=faced.bat_val-faced.bat_base+faced.wk_base     # average wicket cost per ball added back
d=d.join(bob,on=['season','phase']); d['bowl_raa']=-(d.bowl_val-d.bowl_base)
bat_s=faced.groupby(['batter','season']).agg(bat_raa=('bat_raa','sum'),runs=('bat_runs','sum'),balls=('legal','size')).reset_index().rename(columns={'batter':'player'})
outs=wk_rows.groupby(['player_out','season']).agg(wk_pen=('wkt_cost','sum'),outs=('wkt_cost','size')).reset_index().rename(columns={'player_out':'player'})
bowl_s=d.groupby(['bowler','season']).agg(bowl_raa=('bowl_raa','sum'),bballs=('legal','sum'),conceded=('charged','sum'),wkts=('bowler_wkt','sum')).reset_index().rename(columns={'bowler':'player'})
# appearances
app=[]
for s,pl in zip(mt.season,mt.players):
    for t,v in json.loads(pl).items():
        for x in v: app.append((x,s))
app=pd.DataFrame(app,columns=['player','season']).value_counts().rename('matches').reset_index()
ps=app.merge(bat_s,how='left').merge(outs,how='left').merge(bowl_s,how='left').fillna(0)
ps['bat_raa']=ps.bat_raa-ps.wk_pen
ps['raa']=ps.bat_raa+ps.bowl_raa
ps.to_csv('out/player_seasons.csv',index=False)
# sanity: totals by season should be ~0
print(ps.groupby('season')[['bat_raa','bowl_raa']].sum().tail(4).round(0))
# RE sanity
print('RE start',round(RE(0,0).item(),1),' RE 10ov/2wk',round(RE(60,2).item(),1),' RE 15ov/5wk',round(RE(90,5).item(),1))
wv=d[(d.season>=2023)].groupby('phase').apply(lambda x:(x.re_after_now-RE(x.legal_before+x.legal,x.wk_before+1)).mean())
print('avg wicket value by phase',wv.round(1).to_dict())
d.to_parquet('out/deliveries_valued.parquet'); faced.to_parquet('out/faced.parquet')
json.dump({'wicket_value':wv.round(2).to_dict()},open('out/re_meta.json','w'))
