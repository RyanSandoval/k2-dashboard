#!/usr/bin/env node
// Dashboard sections reveal themselves with style.display = '', so their hidden
// state has to stay inline — a class rule would swallow the reveal. This proves
// both halves: the chrome is classed, and every section can still be shown.
import { withApp, report } from './page.mjs';

const out = await withApp(page => page.evaluate(() => {
  navigateTo('dashboard');
  const page_ = document.getElementById('page-dashboard');
  const o = {};

  o.headsClassed = page_.querySelectorAll('.ui-cardhead').length === 7;
  o.titlesClassed = page_.querySelectorAll('.ui-title').length >= 7;
  o.linksClassed = page_.querySelectorAll('.ui-link').length >= 7;
  o.tabsClassed = page_.querySelectorAll('.ui-tab').length === 5;

  // The class must actually resolve, not just be present.
  const head = page_.querySelector('.ui-cardhead');
  o.headIsFlex = getComputedStyle(head).display === 'flex' &&
                 getComputedStyle(head).justifyContent === 'space-between';

  // No element may carry two class attributes — the browser keeps the first and
  // the element renders unstyled while the markup reads correctly.
  o.noDupeClass = ![...page_.querySelectorAll('*')].some(e =>
    e.outerHTML.slice(0, e.outerHTML.indexOf('>')).split('class="').length > 2);

  // Every hidden section must still be revealable by clearing the inline style.
  const hidden = [...page_.querySelectorAll('*')].filter(el => el.style.display === 'none');
  // Not a fixed count: renderDashboard() legitimately reveals whichever sections
  // have data, so the number varies with the fixture. What must hold is that the
  // set is non-empty, otherwise everySectionCanReveal passes vacuously.
  o.hiddenSectionsFound = hidden.length > 0;
  o.hiddenCount = hidden.length;
  o.everySectionCanReveal = hidden.every(el => {
    const prev = el.style.display;
    el.style.display = '';
    const shown = getComputedStyle(el).display !== 'none';
    el.style.display = prev;
    return shown;
  });
  return o;
}));

report(out, 'dashboard-ok');
