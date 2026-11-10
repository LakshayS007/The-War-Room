# Method

How The War Room values players, plans bowling and runs the mock auction. This is the same text as the Method tab on the site.

## Why "The War Room"

Franchises plan their auctions from a war room. The name also nods to WAR, wins above replacement, the measure every valuation on this site is built on.

## What this is

Two decision tools built on every IPL delivery from 2023 to 2026 (the impact-player era): an auction valuation that compares each 2026 contract with what the player actually contributed, and a bowling planner for a captain choosing the next over.

## Step 1. Value every ball

A run-expectancy table, built from first innings, gives the runs a side should still score from any state of balls left and wickets lost. At the start of an innings that is `191` runs. Every ball changes that state, so each delivery is worth its runs plus the change in expected runs:

`ball value = runs + RE(after) − RE(before)`

A wicket's cost depends on when it falls. On average it is worth 9.9 runs in the powerplay, 4.8 in the middle overs and 1.2 at the death. Batters are credited with their own runs and charged for their dismissal. Bowlers are charged runs off the bat, wides and no-balls, and credited for the wickets they take (run-outs excluded). Each ball is compared with the league average for that season and phase, then adjusted for the venue and for batting first or chasing, so a 40 at Chinnaswamy and a 40 at Chepauk are not treated alike [5,6].

## Step 2. Compare with a replacement player

The right baseline is not the average player but the cheap one a team can always find [4]. Replacement level is set at the 20th-percentile regular: the weakest fifth of players with real game time that season (at least 100 balls faced or 120 bowled). In 2026 that was -0.13 (batting) and -0.16 (bowling) runs per ball.

## Step 3. Turn runs into wins

Across the 40 team-seasons from 2023 to 2026, every **101** runs of net run difference was worth one extra win. Value over replacement divided by that number gives wins above replacement (WAR) [4].

## Step 4. Project next season

An auction price is a bet on next season, and a single season's WAR repeats only weakly [4]. Projected 2027 WAR weights 2026, 2025 and 2024 at 5, 4 and 3, then pulls every player toward replacement level in proportion to how little we have seen of him. The strength of that pull (120 weighted matches) was chosen by testing which setting best predicted the 2024 and 2025 seasons.

## Step 5. Price it, with uncertainty

Teams spent ₹32.4 crore above the ₹0.3 cr minimum for every projected win, so fair price = ₹0.3 cr + projected WAR × that rate. Each player's matches are resampled 1,000 times to get a range. **Underpriced** means at least 80% of simulations put fair price above his 2026 price. **Overpriced** means at least 80% put it below. Everything in between is **balanced** [4,8]. A minimum-price player can't be overpriced, because he can't be bought any cheaper.

## Step 6. The market lens

Prices also reflect things the model leaves out [1,2,7]. A second model explains price from projected WAR, overseas status, role, keeping and how the player was signed. It finds overseas players cost **37%** more and keepers **53%** more for the same projected output. That overseas premium is in line with the 22–41% reported by Chowdhury and Bansal [7]. "Market expects" in the table is what this model says the market usually pays for a profile like his. An overpriced player tagged *market premium* costs no more than about 1.25× what the market expects for his profile, so the gap is the usual premium rather than an outlier.

The 187 contracted players with at least 5 IPL matches in 2024–26 are valued.

## Mock auction AI

The AI franchises bid what IPL teams actually pay, not what the model thinks a player is worth. An auction-price model was fitted on 615 real sales from the 2022 and 2025 mega auctions and the 2023, 2024 and 2026 mini auctions. It uses projected value going into each auction, IPL experience, overseas status and previous price. In mega auctions overseas players carry only a small premium and 8 of the top 10 buys were Indian. In mini auctions overseas players dominate because teams are short of overseas places, so the mock auction follows the mega-auction pattern. Players are ranked by that model blended with their 2026 contract, which carries the star value statistics can't see, and the ranking is priced on the real 2025 mega-auction ladder. On every lot, three franchises are interested, each with its own view within about 20% of the expected price.

## Matchups and the next-over ranking

Small samples mislead: a batter on 18 off 4 balls against leg-spin has not "solved" leg-spin. Every matchup cell is shrunk toward the batter's overall form in that phase, scaled by how the whole league scores off that bowling type. Thin samples lean on the prior and big samples speak for themselves. Bowlers get the same treatment for their economy and wicket rate in each phase.

Expected runs in an over = league runs per ball in the phase × bowler's economy factor × the batters' factor against that bowling type, with the striker weighted 55% and the non-striker 45%. Wicket chance uses the same structure. The ranking subtracts the run value of expected wickets from expected runs.

## Where to bowl

Line and length come from Cricinfo's ball-by-ball tracking for IPL 2023–26, joined to the Cricsheet data delivery by delivery. Every cell is pulled toward what the league scores off that line and length, adjusted for how good the batter is against that kind of bowling overall, so a cell with 6 balls leans on the league and a cell with 200 balls speaks for itself. The best plan is the cell with the lowest expected runs after crediting the run value of a wicket, among cells where the batter has faced at least 10 balls. Outcomes describe what happened when the ball landed there. They don't say how easy it is to land it there, so a yorker plan still needs a bowler who can hit it.

## Limits

- Fielding, wicket-keeping and captaincy are not valued, so keepers and captains will look overpriced. The market lens shows how much of that is the usual premium.
- No age curve yet: young players will usually beat their projection and older players fall short of it.
- Price alone ranked 2026 output slightly better than the projection. Teams see things box scores don't (fitness, role, form), so treat this as one input alongside scouting.
- The run-expectancy table comes from first innings and is applied to chases too.
- Bowling types come from player profiles plus a manual mapping. About 1.6% of balls have an unclassified bowler.
- Prices are each player's 2026 contract: retention, trade or auction fee. Mid-season replacements are not included, and players released before the season (such as Mustafizur Rahman) are removed.
- This is a model, not a verdict on any player. Use it to ask better questions.

## Sources

- Ball-by-ball data: [Cricsheet](https://cricsheet.org), via the daily-updated [IPL-DATASET](https://github.com/ritesh-ojha/IPL-DATASET) mirror. Bowling styles from that mirror's player list.
- 2026 retentions and trades: [Sportskeeda](https://widgets.sportskeeda.com/cricket/news-ipl-2026-retentions-full-list-players-retained-franchises-price-tags-inr-ahead-ipl-2026-auction). 2026 auction fees: [India TV](https://www.indiatvnews.com/sports/cricket/full-squads-of-all-teams-after-ipl-2026-auction-green-most-expensive-buy-prashant-kartik-create-records-2025-12-16-1022008).
- Past auction results 2013–2026: [IPL Auction Dataset](https://www.kaggle.com/datasets/sunnyyadav754/ipl-auction-dataset-20132026) (Kaggle, CC BY-NC-SA 4.0). Five nationality errors in it were corrected from the 2026 squad list.
- Line and length: Cricinfo ball tracking via [The Ultimate Ball-by-Ball Cricket Dataset](https://www.kaggle.com/datasets/ariadaikalam/the-ultimate-ball-by-ball-cricket-dataset) (Kaggle). Shared for non-commercial use with credit to Cricinfo, so a licensed feed would be needed before this app could be sold.
- Not affiliated with the IPL, the BCCI or any franchise.

## References

1. Karnik A. Valuing cricketers using hedonic price models. J Sports Econ. 2010;11(4):456–69. [Link](https://econpapers.repec.org/RePEc:sae:jospec:v:11:y:2010:i:4:p:456-469)
2. Lenten L, Geerling W, Kónya L. A hedonic model of player wage determination from the Indian Premier League auction: further evidence. Sport Manag Rev. 2012;15(1):60–71. [Link](https://econpapers.repec.org/RePEc:taf:rsmrxx:v:15:y:2012:i:1:p:60-71)
3. Davis J, Perera H, Swartz TB. Player evaluation in Twenty20 cricket. J Sports Anal. 2015. [Link](https://www.sfu.ca/~tswartz/papers/moneyball.pdf)
4. Rafique H. cricWAR: a reproducible system for evaluating player performance in limited-overs cricket. [Link](https://www.stat.cmu.edu/cmsac/conference/2022/assets/pdf/HassanRafique.pdf)
5. Rafique H. cricWAR. MIT Sloan Sports Analytics Conference. [Link](https://www.sloansportsconference.com/research-papers/cricwar-a-reproducible-system-for-evaluating-player-performance-in-limited-overs-cricket)
6. Bandyopadhyay R. Context-adjusted player evaluation for Twenty20 cricket. arXiv:2608.18020. 2026. [Link](https://arxiv.org/pdf/2608.18020)
7. Chowdhury A, Bansal P. Return on investment and player valuation effectiveness in the Indian Premier League. Sport Bus Manag. 2026. doi:10.1108/sbm-01-2026-0014. [Link](https://www.citedrive.com/en/discovery/return-on-investment-and-player-valuation-effectiveness-in-the-indian-premier-league-a-comprehensive-analysis-of-foreign-versus-domestic-player-economics/)
8. Value for Money — IPL 2026 ROI: bargains vs busts. [Link](https://cricket-website.pages.dev/blogs/valuation-2026/index.html)
