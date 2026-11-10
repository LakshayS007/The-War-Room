import json, glob, sys, os
import pandas as pd
SRC = sys.argv[1]; OUT = sys.argv[2]
rows=[]; matches=[]; reg={}
for f in glob.glob(os.path.join(SRC,'*.json')):
    m=json.load(open(f)); info=m['info']; mid=os.path.basename(f)[:-5]
    date=info['dates'][0]; season=int(date[:4])
    teams=info['teams']
    reg.update(info.get('registry',{}).get('people',{}))
    matches.append(dict(match_id=mid,date=date,season=season,venue=info.get('venue'),team1=teams[0],team2=teams[1],
        winner=info.get('outcome',{}).get('winner'),players=json.dumps(info['players'])))
    for i,inn in enumerate(m.get('innings',[])):
        if inn.get('super_over'): continue
        bat=inn['team']; bowl=[t for t in teams if t!=bat][0]
        for ov in inn.get('overs',[]):
            o=ov['over']
            for b,d in enumerate(ov['deliveries']):
                ex=d.get('extras',{})
                w=d.get('wickets',[])
                rows.append(dict(match_id=mid,season=season,date=date,innings=i+1,bat_team=bat,bowl_team=bowl,over=o,ball_seq=b,
                    batter=d['batter'],bowler=d['bowler'],non_striker=d['non_striker'],
                    bat_runs=d['runs']['batter'],extras=d['runs']['extras'],total=d['runs']['total'],
                    wides=ex.get('wides',0),noballs=ex.get('noballs',0),byes=ex.get('byes',0),legbyes=ex.get('legbyes',0),
                    wicket=len(w)>0,wkt_kind=w[0]['kind'] if w else None,player_out=w[0]['player_out'] if w else None,
                    n_wkts=len(w)))
df=pd.DataFrame(rows); mt=pd.DataFrame(matches)
df.to_parquet(os.path.join(OUT,'deliveries.parquet')); mt.to_parquet(os.path.join(OUT,'matches.parquet'))
pd.Series(reg).rename('cricsheet_id').to_csv(os.path.join(OUT,'registry.csv'))
print(df.shape, mt.shape); print(mt.groupby('season').size().tail(8))
