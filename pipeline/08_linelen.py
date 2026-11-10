"""Line & length: batter x length x line by pace/spin, phase, bowler arm (IPL 2023-2026, Cricinfo tracking)."""
import pandas as pd, numpy as np, json, sys
t=pd.read_csv(sys.argv[1] if len(sys.argv)>1 else 'data/tracking/ipl_tracking_2021_2026.csv')
d=pd.read_parquet('out/deliveries_valued.parquet'); d['match_id']=d.match_id.astype(int)
d=d.sort_values(['match_id','innings','over','ball_seq']); d['delivery_number']=d.groupby(['match_id','innings']).cumcount()+1
site=json.load(open('out/site_data.json'))
btype={}
for cs,b in site['bowl'].items(): btype[cs]=b['t']
# full bowling-type map from export step (all bowlers, not just squads)
src=open('pipeline/04_export.py').read()
code_block=src[src.index("CODE="):src.index("W=d[d.season>=2023]")]
ns={'pd':pd,'pdx':pd.read_csv('data/IPL-DATASET/csv/2024_players_details.csv')}; exec(code_block,ns); BT=ns['btype']
j=d[(d.season>=2023)&(d.wides==0)].merge(t,on=['match_id','innings','delivery_number'],how='inner')
j['bt']=j.bowler.map(BT); j=j[j.bt.notna()&j.ball_line.notna()&j.ball_length.notna()]
j['kind']=np.where(j.bt.str.startswith('Pace'),'Pace','Spin')
j['arm']=np.where(j.bt.isin(['Pace (L)','Left-arm orthodox','Left-arm wrist']),'L','R')
LEN={'yorker':'Yorker','full toss':'Full toss','full':'Full','good length':'Good length','short of a good length':'Back of length','short':'Short'}
LINE={'wide outside offstump':'Wide outside off','outside offstump':'Outside off','on the stumps':'On the stumps','down leg':'Down leg','wide down leg':'Down leg'}
j['len']=j.ball_length.map(LEN); j['line']=j.ball_line.map(LINE)
j['out']=(j.player_out==j.batter)&j.bowler_wkt
L=list(LEN.values()); N=['Wide outside off','Outside off','On the stumps','Down leg']; K=['Pace','Spin']; P=['PP','Middle','Death']; A=['R','L']
idx=lambda k,p,a,l,n: (((K.index(k)*3+P.index(p))*2+A.index(a))*6+L.index(l))*4+N.index(n)
j['ci']=[idx(*r) for r in zip(j.kind,j.phase,j.arm,j.len,j.line)]
lg=j.groupby('ci').agg(b=('bat_runs','size'),r=('bat_runs','sum'),o=('out','sum'))
league=[[0,0,0] for _ in range(288)]
for ci,r in lg.iterrows(): league[ci]=[int(r.b),int(r.r),int(r.o)]
S=set(p['cs'] for p in site['players'] if p['cs'])
bat={}
for b,x in j[j.batter.isin(S)].groupby('batter'):
    g=x.groupby('ci').agg(b=('bat_runs','size'),r=('bat_runs','sum'),o=('out','sum'))
    bat[b]=[[int(ci),int(r.b),int(r.r),int(r.o)] for ci,r in g.iterrows()]
out={'L':L,'N':N,'K':K,'P':P,'A':A,'league':league,'bat':bat,'n_balls':int(len(j)),'seasons':'2023–2026'}
json.dump(out,open('out/linelen.json','w'),separators=(',',':'))
import os; print('balls',len(j),' batters',len(bat),' KB',os.path.getsize('out/linelen.json')//1024)
# sanity: league SR & wicket% by length (pace)
x=j[j.kind=='Pace'].groupby('len').agg(b=('out','size'),sr=('bat_runs','mean'),w=('out','mean'))
print((x.assign(sr=x.sr*100,w=x.w*100)).round(1).loc[L].to_string())
k=j[j.batter=='V Kohli']; print('Kohli balls',len(k)); print(k[k.kind=='Pace'].pivot_table(index='len',columns='line',values='bat_runs',aggfunc='size').reindex(L)[N].fillna(0).astype(int).to_string())
