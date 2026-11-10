// Lets the nine AI franchises run a full 60-player auction with no human bids and saves every sale to out/mock_sim.json.
// Then run:  python pipeline/compare_sim.py   to compare the prices with the real 2025 mega auction.
const { chromium } = require('playwright'); const path = require('path'); const fs = require('fs');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1280, height: 1000 } });
  await p.goto('file://' + path.resolve(__dirname, '../docs/index.html') + '#mock'); await p.waitForTimeout(300);
  await p.selectOption('#mk-pool', '60'); await p.selectOption('#mk-timer', '6'); await p.selectOption('#mk-team', 'MI');
  await p.click('#mk-solo');
  for (let i = 0; i < 160; i++) { await p.waitForTimeout(5000); if (await p.$eval('#mk-done', e => !e.hidden)) break; }
  const out = await p.evaluate(() => { const S = MK.S, sales = [];
    for (const k in S.teams) for (const x of S.teams[k].players) { const q = byName[x.n]; sales.push({ n: x.n, price: x.price, auc: q.auc, fair: +(q.fair ?? 0).toFixed(1), team: k }); }
    return { lots: S.pool.length, sold: sales.length, sales, unsold: S.pool.length - sales.length }; });
  fs.writeFileSync(path.resolve(__dirname, '../out/mock_sim.json'), JSON.stringify(out));
  console.log('lots', out.lots, 'sold', out.sold, 'unsold', out.unsold); await b.close();
})();
