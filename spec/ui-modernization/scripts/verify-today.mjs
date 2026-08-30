#!/usr/bin/env node
// The four Today-page panels converted from inline display= to classes. Written
// because that conversion silently broke two show-paths: `style.display=''` used to
// fall back to display:block and now falls back to the stylesheet's none.
import { withApp, report } from './page.mjs';

const out = await withApp(page => page.evaluate(() => {
  const vis = id => getComputedStyle(document.getElementById(id)).display !== 'none';
  const cycle = (id) => {
    const el = document.getElementById(id);
    el.classList.add('is-open');    const shown = vis(id);
    el.classList.remove('is-open'); return { shown, hidden: !vis(id) };
  };
  const o = {};
  o.shortcutsStartClosed = !vis('shortcuts-panel');
  toggleShortcutsPanel(); o.shortcutsOpenOnFirstPress = vis('shortcuts-panel');
  toggleShortcutsPanel(); o.shortcutsCloseAgain = !vis('shortcuts-panel');
  const brief = cycle('daily-brief-panel');
  o.briefShows = brief.shown; o.briefHides = brief.hidden;
  const link = cycle('jot-linker');
  o.linkerShows = link.shown; o.linkerHides = link.hidden;
  const nudge = document.getElementById('jot-match-nudge');
  nudge.classList.add('is-open');
  o.nudgeShows = vis('jot-match-nudge');
  o.nudgeIsFlex = getComputedStyle(nudge).display === 'flex';
  nudge.classList.remove('is-open'); o.nudgeHides = !vis('jot-match-nudge');
  o.kbdStyled = getComputedStyle(document.querySelector('#shortcuts-panel kbd'))
    .borderTopWidth === '1px';
  return o;
}));

report(out, 'today-ok');
