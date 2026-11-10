#!/usr/bin/env bash
# Rebuilds every model output and the website from raw data. Run from the repo root.
# Needs the raw data described in data/README.md. Takes about 10-20 minutes, mostly the bootstraps.
set -euo pipefail
mkdir -p out
step(){ echo; echo "== $1"; shift; python "$@"; }
step "1  ingest Cricsheet ball-by-ball"            pipeline/01_ingest.py data/IPL-DATASET/json/ipl_match out
step "2  match 2026 contracts to Cricsheet names"  pipeline/02_match_names.py
step "3  run-expectancy table and ball values"     pipeline/03_model.py
step "4  bowling types, matchups, base site data"  pipeline/04_export.py
step "5  WAR per player-match (2021+)"             pipeline/06_war.py
step "6  WAR per player-match (2018+, for prices)" pipeline/06b_war_2018.py
step "7  2027 projection, fair price, backtest"    pipeline/07_value.py
if [ ! -f data/tracking/ipl_tracking_2021_2026.csv ]; then
  if [ -n "${TRACKING_CSV:-}" ]; then step "8a cut Kaggle tracking file to IPL" pipeline/08a_filter_tracking.py "$TRACKING_CSV"
  else echo "Missing data/tracking/ipl_tracking_2021_2026.csv - set TRACKING_CSV=<Kaggle ball-by-ball CSV> (see data/README.md)"; exit 1; fi
fi
step "8  line-and-length grids"                    pipeline/08_linelen.py
step "9  what the auction market pays"             pipeline/09_auction_model.py
step "9b auction model with nationality fixes"     pipeline/09b_auction_model.py
step "10 mock-auction market values"               pipeline/10_market_value.py
step "11 build the website -> docs/index.html"     pipeline/05_build.py
