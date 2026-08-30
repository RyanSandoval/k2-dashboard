// Drives the real index.html with a real k2-data fixture and checks the launcher
// actually built. A diff that looks right and a page that renders are different claims.
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { withChrome, withTab, load } from './cdp.mjs';

const PORT = 9341;
const url = 'file://' + resolve('../../index.html');
const data = JSON.parse(readFileSync('/Users/ryansandoval/k2-data/data.json', 'utf8'));

await withChrome(PORT, async () => {
  await withTab(PORT, url, async (tab) => {
    await load(tab, url, 390);
    // Inject real data and build the nav the same way the drawer does.
    const r = await tab.send('Runtime.evaluate', { returnByValue: true, awaitPromise: true,
      expression: `(() => {
        DATA = ${JSON.stringify(data)}; window.DATA = DATA;
        renderNav();
        const tiles = [...document.querySelectorAll('#launcher-grid .tile')];
        const live  = tiles.filter(t => t.classList.contains('is-live'));
        return JSON.stringify({
          tiles: tiles.length,
          live: live.length,
          liveLabels: live.map(t => t.querySelector('.tile-nm').textContent + ':' +
            (t.querySelector('.tile-count')?.textContent || '')),
          groups: document.querySelectorAll('#launcher-grid .launcher-group').length,
          sidebarRest: document.querySelectorAll('#nav-section-everything-body .nav-item').length,
          inlineStyled: document.querySelectorAll('#launcher-grid [style]').length,
        });
      })()` });
    if (r.exceptionDetails) { console.log('THREW:', JSON.stringify(r.exceptionDetails).slice(0,400)); process.exit(1); }
    const out = JSON.parse(r.result.value);
    console.log(JSON.stringify(out, null, 2));
    if (out.tiles !== 34) { console.log('FAIL: expected 34 tiles'); process.exit(1); }
    if (out.inlineStyled !== 0) { console.log('FAIL: launcher still has inline styles'); process.exit(1); }
    console.log('launcher-ok');
  });
});
