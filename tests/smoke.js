// Smoke test: every view renders without a page error, the team strip filters, and a solo mock auction runs.
// Usage: npm test   (after `npm install` and `npx playwright install chromium`)
const { chromium } = require('playwright'); const path = require('path');
const URL = 'file://' + path.resolve(__dirname, '../docs/index.html');
const ok = (c, m) => { if (!c) { console.error('FAIL', m); process.exitCode = 1; } else console.log('ok  ', m); };
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1280, height: 900 }, acceptDownloads: true });
  const errs = []; p.on('pageerror', e => errs.push(e.message));
  await p.goto(URL); await p.waitForTimeout(800);
  ok(await p.isVisible('#v-home'), 'home view shows on load');
  ok(Number(await p.textContent('#hub-n')) > 0, 'bargain count on the hub tile');
  ok((await p.$$('#hub-cards .pc')).length === 5, 'five top-bargain cards');
  for (const v of ['auction', 'matchups', 'analyst', 'mock', 'method']) {
    await p.goto(URL + '#' + v); await p.waitForTimeout(300); ok(await p.isVisible('#v-' + v), `${v} view renders`);
  }
  await p.goto(URL + '#auction'); await p.waitForTimeout(300);
  ok((await p.$$('#tbl tbody tr')).length > 100, 'player table filled');
  await p.click('#teamstrip button[data-t="CSK"]'); await p.waitForTimeout(300);
  const teams = await p.$$eval('#tbl tbody tr', rs => [...new Set(rs.map(r => r.querySelector('.tchip')?.textContent))]);
  ok(teams.length === 1 && teams[0] === 'CSK', 'team strip filters the table to CSK');
  await p.click('#teamstrip button[data-t="CSK"]');
  await p.goto(URL + '#matchups'); await p.waitForTimeout(300);
  ok((await p.$$('#rank li')).length > 0, 'next-over ranking filled');
  ok((await p.$$('#ll-grid td')).length > 0, 'line-and-length grid filled');
  await p.goto(URL + '#mock'); await p.waitForTimeout(300);
  await p.selectOption('#mk-pool', '30'); await p.selectOption('#mk-timer', '6'); await p.click('#mk-solo'); await p.waitForTimeout(4000);
  ok(await p.isVisible('.lot'), 'solo auction starts');
  ok(await p.isVisible('#nav-live'), 'LIVE badge shows during an auction');
  await p.goto(URL + '#analyst'); await p.waitForTimeout(300);
  await p.fill('#chat-in', 'Is Rishabh Pant worth ₹27 cr?'); await p.click('#chat-send'); await p.waitForTimeout(300);
  ok(/overpriced/i.test(await p.textContent('#chat-log')), 'quick answers reply without AI');
  await p.fill('#chat-in', 'Where should spinners bowl to Abhishek Sharma?'); await p.click('#chat-send'); await p.waitForTimeout(300);
  ok((await p.$$('#chat-log table')).length >= 1, 'quick answers return a table');
  await p.goto(URL + '#auction'); await p.waitForTimeout(300);
  const [dl] = await Promise.all([p.waitForEvent('download'), p.click('#tbl-export')]);
  ok(dl.suggestedFilename() === 'auction-value.csv', 'CSV export downloads in the browser');
  ok(errs.length === 0, 'no page errors' + (errs.length ? ': ' + errs.join(' | ') : ''));
  await b.close();
})();
