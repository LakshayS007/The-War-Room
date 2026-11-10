# Raw data

The raw data is not committed: it is about 2 GB, and two of the sources only allow non-commercial use. Download it into this folder so it looks like this:

```
data/
├── IPL-DATASET/            Cricsheet ball-by-ball and player list
│   ├── json/ipl_match/*.json
│   └── csv/2024_players_details.csv
├── auction_hist/
│   └── IPL_Auction/IPL_Auction_<year>_Sold_Player.csv   (2013-2026)
└── tracking/
    └── ipl_tracking_2021_2026.csv   (made by step 8a below)
```

| Folder | Where to get it | Licence |
|---|---|---|
| `IPL-DATASET/` | `git clone https://github.com/ritesh-ojha/IPL-DATASET data/IPL-DATASET` (a daily-updated mirror of [Cricsheet](https://cricsheet.org)) | Open; credit Cricsheet |
| `auction_hist/` | [IPL Auction Dataset 2013–2026](https://www.kaggle.com/datasets/sunnyyadav754/ipl-auction-dataset-20132026) on Kaggle. Unzip so the yearly CSVs sit in `data/auction_hist/IPL_Auction/` | CC BY-NC-SA 4.0 |
| `tracking/` | [The Ultimate Ball-by-Ball Cricket Dataset](https://www.kaggle.com/datasets/ariadaikalam/the-ultimate-ball-by-ball-cricket-dataset) on Kaggle (Cricinfo line, length and shot data). The ball-by-ball file is several GB, so cut it down to IPL matches with step 8a | Non-commercial; credit Cricinfo |

Step 8a needs the Cricsheet data ingested first, because it keeps only the matches Cricsheet has (the two sources share match IDs). `run_pipeline.sh` handles the order:

```bash
TRACKING_CSV=/path/to/the/kaggle/ball_by_ball.csv ./run_pipeline.sh
```

**Known fixes applied in the pipeline**

- 12 player names in the 2026 contract list don't match Cricsheet automatically. They are fixed by hand-checked overrides in `pipeline/02_match_names.py`.
- 5 players in the auction dataset have the wrong nationality. They are corrected from the 2026 squad list in `pipeline/09b_auction_model.py`.
- Bowling styles missing from the player list are filled from a small manual map in `pipeline/04_export.py`.
