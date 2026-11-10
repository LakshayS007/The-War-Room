"""Cut the Kaggle 'Ultimate Ball-by-Ball' Cricinfo tracking file (several GB) down to IPL matches.

Usage: python pipeline/08a_filter_tracking.py <path to the Kaggle ball-by-ball CSV>
Keeps only matches that appear in the Cricsheet IPL data (Cricsheet and Cricinfo share match IDs)
and writes data/tracking/ipl_tracking_2021_2026.csv for 08_linelen.py.
"""
import sys, os, pandas as pd
src = sys.argv[1]
ids = set(pd.read_parquet('out/matches.parquet').query('season>=2021').match_id.astype(int))
cols = ['match_id','innings','delivery_number','ball_line','ball_length','shot_played','shot_control','wagon_x','wagon_y',
        'wagon_zone','wagon_angle','wagon_distance','wagon_in_ring','shot_direction','ball_timestamp','win_probability',
        'predicted_score','ball_events']
os.makedirs('data/tracking', exist_ok=True)
out = 'data/tracking/ipl_tracking_2021_2026.csv'; first = True; n = 0
for ch in pd.read_csv(src, chunksize=500_000, low_memory=False):
    ch = ch[ch.match_id.astype(str).str.isdigit()]
    ch = ch[ch.match_id.astype(int).isin(ids)]
    if len(ch):
        ch[[c for c in cols if c in ch.columns]].to_csv(out, mode='w' if first else 'a', header=first, index=False)
        first = False; n += len(ch)
print('kept', n, 'IPL deliveries ->', out)
