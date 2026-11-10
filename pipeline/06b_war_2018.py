"""Projected WAR valuation: context adjustment, replacement level, runs per win, projection, bootstrap."""
import pandas as pd, numpy as np, json, warnings; warnings.filterwarnings('ignore')
d=pd.read_parquet('out/deliveries_valued.parquet'); faced=pd.read_parquet('out/faced.parquet'); mt=pd.read_parquet('out/matches.parquet')
mt['vn']=mt.venue.str.split(',').str[0].str.replace(r'\s*\(.*\)','',regex=True).str.strip()
d=d.merge(mt[['match_id','vn']],on='match_id'); faced=faced.merge(mt[['match_id','vn']],on='match_id')
d=d[d.season>=2018]; faced=faced[faced.season>=2018]
# ---------- 1. context adjustment: venue + innings x phase (shrunk additive effects, runs per ball)
def eff(df,col,keys,k):
    g=df.groupby(keys)[col].agg(['sum','size']); return (g['sum']/(g['size']+k)).rename('e')
faced['bres']=faced.bat_val-faced.bat_base
d['wres']=d.bowl_val-d.bowl_base
for keys,k in [(['vn'],3000),(['innings','phase'],3000)]:
    fe=eff(faced,'bres',keys,k); faced=faced.join(fe,on=keys); faced['bres']-=faced.e; faced['bat_raa']-=faced.e; faced=faced.drop(columns='e')
    de=eff(d,'wres',keys,k); d=d.join(de,on=keys); d['wres']-=d.e; d['bowl_raa']+=d.e; d=d.drop(columns='e')
# ---------- player-match values
wk=d[d.wicket&d.player_out.notna()]
bm=faced.groupby(['batter','match_id','season']).agg(bat=('bat_raa','sum'),bb=('legal','size')).reset_index().rename(columns={'batter':'player'})
wm=wk.groupby(['player_out','match_id','season']).wkt_cost.sum().rename('wpen').reset_index().rename(columns={'player_out':'player'})
om=d.groupby(['bowler','match_id','season']).agg(bowl=('bowl_raa','sum'),ob=('legal','sum')).reset_index().rename(columns={'bowler':'player'})
app=[]
for mid,s,pl in zip(mt.match_id,mt.season,mt.players):
    if s>=2018:
        for t,v in json.loads(pl).items():
            for x in v: app.append((x,mid,s,t))
pm=pd.DataFrame(app,columns=['player','match_id','season','team'])
pm=pm.merge(bm,how='left').merge(wm,how='left').merge(om,how='left').fillna({'bat':0,'bb':0,'wpen':0,'bowl':0,'ob':0})
pm['bat']-=pm.wpen
# ---------- 2. replacement level per season: 20th-percentile per-ball value among regulars (>=100 balls faced / >=120 bowled)
rep={}
for s,x in pm.groupby('season'):
    ps=x.groupby('player')[['bat','bb','bowl','ob']].sum()
    B=ps[ps.bb>=100]; O=ps[ps.ob>=120]
    rep[s]=(float(np.percentile(B.bat/B.bb,20)), float(np.percentile(O.bowl/O.ob,20)))
pm['vorp_bat']=pm.bat-pm.season.map(lambda s:rep[s][0])*pm.bb
pm['vorp_bowl']=pm.bowl-pm.season.map(lambda s:rep[s][1])*pm.ob
# ---------- 3. runs per win (team-season run differential vs wins), 2023-2026
tm=[]
for _,m in mt[mt.season>=2023].iterrows():
    x=d[d.match_id==m.match_id]
    for t in (m.team1,m.team2):
        rf=x[x.bat_team==t].total.sum(); ra=x[x.bowl_team==t].total.sum()
        w=1.0 if m.winner==t else (0.5 if pd.isna(m.winner) else 0.0)
        tm.append((m.season,t,rf-ra,w))
tm=pd.DataFrame(tm,columns=['season','team','rd','w']).groupby(['season','team']).agg(rd=('rd','sum'),w=('w','sum'),g=('w','size')).reset_index()
tm['wpct']=tm.w/tm.g; tm['rdpg']=tm.rd/tm.g
b=np.polyfit(tm.rdpg,tm.wpct,1)[0]; RPW=1/b    # wins per game per run-per-game -> runs per win
r2=np.corrcoef(tm.rdpg,tm.wpct)[0,1]**2
pm['war']=(pm.vorp_bat+pm.vorp_bowl)/RPW; pm['war_bat']=pm.vorp_bat/RPW; pm['war_bowl']=pm.vorp_bowl/RPW
print('replacement (bat, bowl runs/ball):',{k:(round(v[0],3),round(v[1],3)) for k,v in rep.items() if k>=2023})
print(f'runs per win {RPW:.1f} (team-season R2 {r2:.2f}, n={len(tm)})')
pm.to_parquet('out/player_match_war_2018.parquet')
json.dump({'rpw':RPW,'rpw_r2':r2,'rep':{int(k):v for k,v in rep.items()}},open('out/war_meta_2018.json','w'))
