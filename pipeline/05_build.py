import json, pandas as pd, numpy as np
d=json.load(open('out/site_data.json')); d['league']['re0']=191.2
v=pd.read_csv('out/value_2027.csv').set_index('player'); bt=json.load(open('out/backtest.json')); wm=json.load(open('out/war_meta.json'))
num=lambda x:None if pd.isna(x) else round(float(x),3)
for p in d['players']:
    r=v.loc[p['n']]
    ok=r.verdict!='na'
    p.update(proj=num(r.proj) if ok else None,pb=num(r.pb) if ok else None,po=num(r.po) if ok else None,
             fair=num(r.fair) if ok else None,lo=num(r.lo) if ok else None,hi=num(r.hi) if ok else None,
             pbar=num(r.pbar) if ok else None,verdict=r.verdict,mkt=num(r.mkt) if ok else None,prem=bool(r.premium),mprior=int(r.mprior))
    for k in ('imp','ib','iw','m3'): p.pop(k,None)
maxp=max(x['p'] for x in d['players'])
for x in d['players']:
    if x.get('mkt') is not None: x['mkt']=round(min(x['mkt'],maxp),3)
mv=pd.read_csv('out/market_value.csv').set_index('n')
for x in d['players']:
    x['auc']=float(mv.auc[x['n']]) if x['n'] in mv.index else None
ps=pd.read_csv('out/player_seasons.csv')
s26=ps[ps.season==2026].set_index('player'); o3=ps[ps.season.between(2024,2026)].groupby('player').outs.sum()
for x in d['players']:
    c=x.get('cs')
    if c and c in s26.index:
        r=s26.loc[c]; x['s26']=[int(r.matches),int(r.runs),int(r.balls),int(r.outs),int(r.wkts),int(r.bballs),int(r.conceded)]
    else: x['s26']=[0,0,0,0,0,0,0]
    x['o3']=int(o3.get(c,0)) if c else 0
d['val']={'rate_2027':bt['rate_2027'],'n_elig':bt['n_elig'],'os_premium_pct':bt['os_premium_pct'],'wk_premium_pct':bt['wk_premium_pct'],
          'rpw':wm['rpw'],'k':bt['k'],'rep26':wm['rep']['2026'],'bt':{k:bt[k] for k in ['spearman_vs_realised_war','new_verdicts','old_verdicts','hit_rate']}}
d['ll']=json.load(open('out/linelen.json'))
t=open('pipeline/template.html').read().replace('__DATA__',json.dumps(d,separators=(',',':')))
import os; os.makedirs('docs',exist_ok=True)
# Standalone page: proper document head, and a message for viewers that block scripts (e.g. file preview panes)
NOSCRIPT=('<noscript><div style="position:relative;z-index:99;margin:16px;padding:16px 20px;border-radius:12px;background:#d7ff1f;color:#0a0c02;'
  'font:600 16px/1.5 system-ui,sans-serif">The War Room needs JavaScript, and this viewer has it switched off. '
  'Download the file and open it in Chrome, Edge, Safari or Firefox.</div></noscript>\n')
t=('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
   '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'+t.replace('<div class="teamstrip">',NOSCRIPT+'<div class="teamstrip">',1))
open('docs/index.html','w',encoding='utf-8').write(t); print('docs/index.html', len(t)//1024,'KB')
