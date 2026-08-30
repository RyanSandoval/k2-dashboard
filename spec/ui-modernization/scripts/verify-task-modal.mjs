// Renders the real task modal for a real task and checks the converted classes
// actually resolve to the styles they replaced. A class name that matches no rule
// is invisible in a diff and obvious on screen — this catches it before you see it.
import { readFileSync } from 'node:fs';
import { withChrome, withTab, load } from './cdp.mjs';

const PORT = 9345;
const url = 'file:///Users/ryansandoval/k2-dashboard/index.html';
const data = JSON.parse(readFileSync('/Users/ryansandoval/k2-data/data.json', 'utf8'));
const task = data.tasks.find(t => t && !t.done && (t.text || '').length > 10);

const R = await withChrome(PORT, () => withTab(PORT, url, async (tab) => {
  await load(tab, url, 390);
  const r = await tab.send('Runtime.evaluate', { returnByValue: true, expression: `(() => {
    DATA = ${JSON.stringify(data)}; window.DATA = DATA;
    document.getElementById('login-screen').style.display='none';
    document.getElementById('app-main').style.display='flex';
    openTaskModal(${JSON.stringify(task.id)});
    const root = document.getElementById('task-modal-content');
    const cs = sel => { const e = root.querySelector(sel); return e && getComputedStyle(e); };
    const out = { rendered: root.innerHTML.length > 500 };

    // Each assertion is the declaration the inline style used to carry.
    const panel = cs('.tm-panel');
    out.panelPadded    = !!panel && panel.paddingTop === '10px';
    out.panelSurfaced  = !!panel && panel.backgroundColor !== 'rgba(0, 0, 0, 0)';
    const label = cs('.tm-label');
    out.labelUpper     = !!label && label.textTransform === 'uppercase';
    out.labelBold      = !!label && label.fontWeight === '700';
    const head = cs('.tm-head');
    out.headIsFlex     = !!head && head.display === 'flex';
    out.headGap        = !!head && head.gap === '12px';
    const body = cs('.tm-head-body');
    out.bodyFlexes     = !!body && body.flexGrow === '1';

    // Nothing may end up with two class attributes — the browser silently drops
    // the second, so the element renders unstyled while the markup looks right.
    out.noDupeClass = ![...root.querySelectorAll('*')]
      .some(e => (e.outerHTML.match(/<[^>]*?class="/g) || []).length > 1 &&
                 e.outerHTML.slice(0, e.outerHTML.indexOf('>')).split('class="').length > 2);

    // Every tm-* class used in the markup must resolve to at least one rule.
    const used = new Set();
    root.querySelectorAll('[class]').forEach(e => e.classList.forEach(c => c.startsWith('tm-') && used.add(c)));
    const defined = new Set();
    for (const sheet of document.styleSheets) {
      let rules; try { rules = sheet.cssRules; } catch { continue; }
      for (const rule of rules || []) {
        (rule.selectorText || '').split(',').forEach(sel => {
          const m = sel.trim().match(/\\.(tm-[a-z-]+)/); if (m) defined.add(m[1]);
        });
      }
    }
    out.everyClassDefined = [...used].every(c => defined.has(c));
    out.undefinedClasses = [...used].filter(c => !defined.has(c));
    out.classesUsed = used.size;
    return JSON.stringify(out);
  })()` });
  if (r.exceptionDetails) { console.log('THREW:', JSON.stringify(r.exceptionDetails).slice(0,400)); process.exit(1); }
  return JSON.parse(r.result.value);
}));

console.log(JSON.stringify(R, null, 2));
const bad = Object.entries(R).filter(([k,v]) => typeof v === 'boolean' && v !== true);
if (bad.length) { console.log('FAIL:', bad.map(([k]) => k).join(', ')); process.exit(1); }
console.log('task-modal-ok');
