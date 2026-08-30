// Exercises the four Today-page panels I converted from inline display= to classes.
// Written because converting them silently broke two show-paths: `style.display=''`
// used to fall back to display:block, and now falls back to the stylesheet's none.
import { readFileSync } from 'node:fs';
import { withChrome, withTab, load } from './cdp.mjs';

const PORT = 9344;
const url = 'file:///Users/ryansandoval/k2-dashboard/index.html';
const data = JSON.parse(readFileSync('/Users/ryansandoval/k2-data/data.json', 'utf8'));

const R = await withChrome(PORT, () => withTab(PORT, url, async (tab) => {
  await load(tab, url, 390);
  const r = await tab.send('Runtime.evaluate', { returnByValue: true, expression: `(() => {
    window.DATA = ${JSON.stringify(data)};
    document.getElementById('login-screen').style.display='none';
    document.getElementById('app-main').style.display='flex';
    const vis = id => getComputedStyle(document.getElementById(id)).display !== 'none';
    const out = {};

    // Shortcuts: starts closed, one toggle opens it. The old code read its own
    // inline style, so with the inline gone the first press did nothing.
    out.shortcutsClosed = !vis('shortcuts-panel');
    toggleShortcutsPanel();
    out.shortcutsOpensOnFirstPress = vis('shortcuts-panel');
    toggleShortcutsPanel();
    out.shortcutsClosesAgain = !vis('shortcuts-panel');

    // The three show-paths must actually show.
    const brief = document.getElementById('daily-brief-panel');
    brief.classList.add('is-open');   out.briefCanShow  = vis('daily-brief-panel');
    brief.classList.remove('is-open');out.briefCanHide  = !vis('daily-brief-panel');
    const link = document.getElementById('jot-linker');
    link.classList.add('is-open');    out.linkerCanShow = vis('jot-linker');
    link.classList.remove('is-open'); out.linkerCanHide = !vis('jot-linker');
    const nudge = document.getElementById('jot-match-nudge');
    nudge.classList.add('is-open');   out.nudgeCanShow  = vis('jot-match-nudge');
    out.nudgeIsFlex = getComputedStyle(nudge).display === 'flex';
    nudge.classList.remove('is-open');out.nudgeCanHide  = !vis('jot-match-nudge');

    out.kbdStyled = getComputedStyle(document.querySelector('#shortcuts-panel kbd'))
      .borderTopWidth === '1px';
    return JSON.stringify(out);
  })()` });
  if (r.exceptionDetails) { console.log('THREW:', JSON.stringify(r.exceptionDetails).slice(0,300)); process.exit(1); }
  return JSON.parse(r.result.value);
}));

console.log(JSON.stringify(R, null, 2));
const failed = Object.entries(R).filter(([,v]) => v !== true);
if (failed.length) { console.log('FAIL:', failed.map(([k]) => k).join(', ')); process.exit(1); }
console.log('today-ok');
