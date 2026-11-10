import pandas as pd, numpy as np, json
d=pd.read_parquet('out/deliveries_valued.parquet'); faced=pd.read_parquet('out/faced.parquet')
ps=pd.read_csv('out/player_seasons.csv'); pr=pd.read_csv('out/prices_matched.csv')
pdx=pd.read_csv('data/IPL-DATASET/csv/2024_players_details.csv'); meta=json.load(open('out/re_meta.json'))
CODE={'rf':'Pace (R)','rfm':'Pace (R)','rmf':'Pace (R)','rm':'Pace (R)','lf':'Pace (L)','lfm':'Pace (L)','lmf':'Pace (L)','lm':'Pace (L)',
      'ob':'Off-spin','sla':'Left-arm orthodox','lb':'Leg-spin','lbg':'Leg-spin','lws':'Left-arm wrist'}
btype={n:CODE.get(c) for n,c in zip(pdx.Name,pdx.bowlingStyles) if CODE.get(c)}
manual={'JC Archer':'rf','JR Hazlewood':'rfm','DS Rathi':'lb','Vijaykumar Vyshak':'rm','E Malinga':'rf','Prince Yadav':'rm','PWH de Silva':'lb',
 'JO Holder':'rfm','Akash Madhwal':'rm','Nithish Kumar Reddy':'rm','V Nigam':'lb','Brijesh Sharma':'rfm','XC Bartlett':'rfm','Shivang Kumar':'lws',
 'J Little':'lfm','J Overton':'rf','Zeeshan Ansari':'lb','Harsh Dubey':'sla','Ashwani Kumar':'lfm','AJ Hosein':'sla','C Bosch':'rfm','PP Hinge':'rfm',
 'WD Parnell':'lfm','Gurjapneet Singh':'lfm','JA Duffy':'rfm','Mayank Dagar':'sla','KA Jamieson':'rfm','CJ Jordan':'rfm','Ashok Sharma':'rf',
 'RP Meredith':'rf','HR Shokeen':'ob','Arjun Tendulkar':'lfm','Raghu Sharma':'lb','KM Asif':'rfm','Auqib Nabi':'rm','SR Dubey':'rm',
 'V Puthur':'lws','Abhinandan Singh':'rfm','MW Short':'ob','M Tiwari':'rm','MG Bracewell':'ob',"W O'Rourke":'rf'}
for k,v in manual.items(): btype[k]=CODE[v]
W=d[d.season>=2023]; F=faced[faced.season>=2023].copy()
cov=W.bowler.map(btype).notna().mean(); print('ball coverage with bowler type: %.1f%%'%(100*cov))
missing=W[W.bowler.map(btype).isna()].groupby('bowler').size().sort_values(ascending=False); print('top unclassified:',missing.head(8).to_dict())
F['btype']=F.bowler.map(btype); W=W.assign(btype=W.bowler.map(btype))
F['out']=(F.player_out==F.batter)&F.bowler_wkt
F['isdot']=(F.total==0); F['bnd']=F.bat_runs.isin([4,6])
TYPES=['Pace (R)','Pace (L)','Off-spin','Left-arm orthodox','Leg-spin','Left-arm wrist']; PH=['PP','Middle','Death']
Ft=F[F.btype.notna()]
L=Ft.groupby(['btype','phase']).bat_runs.mean(); O=Ft.groupby(['btype','phase']).out.mean()
Lp=F.groupby('phase').bat_runs.mean(); Op=F.groupby('phase').out.mean()
LB=W.groupby('phase').apply(lambda x:x.charged.sum()/x.legal.sum()); WR=W.groupby('phase').apply(lambda x:x.bowler_wkt.sum()/x.legal.sum())
squad=pr[pr.cs_name.notna()]; S=set(squad.cs_name)
# ---- batter matchups
bat={}
for b,x in F[F.batter.isin(S)].groupby('batter'):
    rec={}
    for p in PH:
        xp=x[x.phase==p]; n=len(xp)
        bf=(xp.bat_runs.sum()+60*Lp[p])/(n+60)/Lp[p]; of=(xp.out.sum()+150*Op[p])/(n+150)/Op[p]
        cells={}
        for t in TYPES:
            c=xp[xp.btype==t]; nb=len(c); pr_r=bf*L[(t,p)]; pr_o=of*O[(t,p)]
            r=(c.bat_runs.sum()+30*pr_r)/(nb+30); o=(c.out.sum()+80*pr_o)/(nb+80)
            cells[t]=[nb,int(c.bat_runs.sum()),int(c.out.sum()),int(c.isdot.sum()),int(c.bnd.sum()),round(r/L[(t,p)],3),round(o/O[(t,p)],3)]
        rec[p]={'n':n,'r':int(xp.bat_runs.sum()),'o':int(xp.out.sum()),'c':cells}
    bat[b]=rec
# ---- bowler phase factors
bowl={}
for j,x in W[W.bowler.isin(S)].groupby('bowler'):
    rec={'t':btype.get(j)}
    for p in PH:
        xp=x[x.phase==p]; n=int(xp.legal.sum()); ch=int(xp.charged.sum()); wk=int(xp.bowler_wkt.sum())
        rec[p]=[n,ch,wk,round((ch+90*LB[p])/(n+90)/LB[p],3),round((wk+180*WR[p])/(n+180)/WR[p],3)]
    bowl[j]=rec
# ---- valuation
wts={2026:1.0,2025:0.6,2024:0.3}
v=ps[ps.season.isin(wts)].copy(); v['w']=v.season.map(wts)
agg=v.groupby('player').apply(lambda x:pd.Series({'wr':(x.w*x.raa).sum(),'wb':(x.w*x.bat_raa).sum(),'wbo':(x.w*x.bowl_raa).sum(),'wm':(x.w*x.matches).sum(),'m3':x.matches.sum()}))
for c,src in [('imp','wr'),('imp_bat','wb'),('imp_bowl','wbo')]: agg[c]=agg[src]/(agg.wm+4)*14
P=squad.merge(agg,left_on='cs_name',right_index=True,how='left')
OS=set("""Phil Salt|Josh Hazlewood|Tim David|Romario Shepherd|Nuwan Thushara|Jacob Bethell|Jordan Cox|Jacob Duffy|Marcus Stoinis|Marco Jansen|Lockie Ferguson|Azmatullah Omarzai|Xavier Bartlett|Mitchell Owen|Cooper Connolly|Ben Dwarshuis|Rashid Khan|Kagiso Rabada|Jos Buttler|Glenn Phillips|Tom Banton|Jason Holder|Luke Wood|Trent Boult|Ryan Rickelton|Allah Ghazanfar|Will Jacks|Mitchell Santner|Corbin Bosch|Sherfane Rutherford|Quinton de Kock|Pat Cummins|Travis Head|Heinrich Klaasen|Brydon Carse|Kamindu Mendis|Eshan Malinga|Liam Livingstone|Jack Edwards|Nicholas Pooran|Aiden Markram|Mitchell Marsh|Shamar Joseph|Matthew Breetzke|Josh Inglis|Wanindu Hasaranga|Anrich Nortje|Tristan Stubbs|Mitchell Starc|Dushmantha Chameera|David Miller|Pathum Nissanka|Ben Duckett|Sunil Narine|Rovman Powell|Finn Allen|Tim Seifert|Cameron Green|Rachin Ravindra|Matheesha Pathirana|Shimron Hetmyer|Lhuan-dre Pretorius|Jofra Archer|Nandre Burger|Kwena Maphaka|Sam Curran|Donovan Ferreira|Adam Milne|Dewald Brevis|Jamie Overton|Noor Ahmad|Nathan Ellis|Matthew Short|Zak Foulkes|Akeal Hosein|Matt Henry""".split('|'))
assert OS<=set(pr.player), OS-set(pr.player)
all_p=pr.merge(P[['player','imp','imp_bat','imp_bowl','m3']],on='player',how='left')
elig=all_p[(all_p.m3>=8)].copy()
order_imp=elig.imp.rank(ascending=False,method='first').astype(int)
prices_sorted=np.sort(elig.price_cr.values)[::-1]
elig['fair']=[prices_sorted[r-1] for r in order_imp]
all_p=all_p.merge(elig[['player','fair']],on='player',how='left')
rho=elig[['price_cr','imp']].corr(method='spearman').iloc[0,1]; print('eligible',len(elig),'spearman',round(rho,3))
# season stats 2026 + 3yr
st=ps[ps.season>=2024].groupby('player').agg(runs=('runs','sum'),balls=('balls','sum'),wk=('wkts','sum'),bb=('bballs','sum'),con=('conceded','sum'),m=('matches','sum'))
WK={'Phil Salt','Jitesh Sharma','Jordan Cox','Prabhsimran Singh','Vishnu Vinod','Jos Buttler','Kumar Kushagra','Anuj Rawat','Tom Banton',
 'Ryan Rickelton','Quinton de Kock','Robin Minz','Heinrich Klaasen','Ishan Kishan','Rishabh Pant','Nicholas Pooran','Josh Inglis',
 'KL Rahul','Abishek Porel','Tim Seifert','Dhruv Jurel','MS Dhoni','Sanju Samson','Urvil Patel','Kartik Sharma'}   # 2026 squad keepers (source role column holds bowling styles)
out=[]
for _,r in all_p.iterrows():
    cs=r.cs_name if isinstance(r.cs_name,str) else None; s=st.loc[cs] if cs in st.index else None
    role=None
    if s is not None and (s.balls+s.bb)>0:
        sh=s.bb/(s.balls+s.bb); role='Bowler' if sh>0.7 else ('Batter' if sh<0.2 else 'All-rounder')
    if r.player in WK: role='WK-Batter'
    out.append(dict(n=r.player,cs=cs,t=r.team,p=r.price_cr,h=r['how'],os=r.player in OS,role=role,bt=btype.get(cs),
        m=int(s.m) if s is not None else 0,runs=int(s.runs) if s is not None else 0,balls=int(s.balls) if s is not None else 0,
        wk=int(s.wk) if s is not None else 0,bb=int(s.bb) if s is not None else 0,con=int(s.con) if s is not None else 0,
        imp=None if pd.isna(r.imp) else round(r.imp,1),ib=None if pd.isna(r.imp_bat) else round(r.imp_bat,1),
        iw=None if pd.isna(r.imp_bowl) else round(r.imp_bowl,1),fair=None if pd.isna(r.fair) else float(r.fair),m3=0 if pd.isna(r.m3) else int(r.m3)))
league={'L':{t:{p:round(L[(t,p)],4) for p in PH} for t in TYPES},'O':{t:{p:round(O[(t,p)],5) for p in PH} for t in TYPES},
        'LB':LB.round(4).to_dict(),'WR':WR.round(5).to_dict(),'wv':meta['wicket_value'],'rho':round(rho,3),'n_elig':len(elig)}
json.dump({'players':out,'bat':bat,'bowl':bowl,'league':league},open('out/site_data.json','w'),separators=(',',':'))
import os; print('json KB',os.path.getsize('out/site_data.json')//1024)
print(pd.DataFrame(out).query('fair==fair').assign(gap=lambda x:x.fair-x.p).sort_values('gap')[['n','t','p','fair','imp','m']].head(8).to_string(index=False))
print(pd.DataFrame(out).query('fair==fair').assign(gap=lambda x:x.fair-x.p).sort_values('gap')[['n','t','p','fair','imp','m']].tail(8).to_string(index=False))
print('no bowler type among squad bowlers:',[x['n'] for x in out if x['bb']>=60 and not x['bt']])
