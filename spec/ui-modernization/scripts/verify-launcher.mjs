#!/usr/bin/env node
// The launcher replaced two hand-maintained copies of the same 34-item menu.
// Checks it builds from the catalogue, ranks live tools, and carries no inline styles.
import { withApp, report } from './page.mjs';

const out = await withApp(page => page.evaluate(() => {
  renderNav();
  const tiles = [...document.querySelectorAll('#launcher-grid .tile')];
  const tools = tiles.filter(t => !t.classList.contains('is-action'));
  const actions = tiles.filter(t => t.classList.contains('is-action'));
  const live = tools.filter(t => t.classList.contains('is-live'));
  return {
    allToolsPresent: tools.length === K2_TOOLS.length,
    // Four verbs lived in the drawer alongside the pages. Refresh and Settings have
    // no other home on a phone, because .sidebar is display:none there — dropping
    // them made both unreachable and nothing failed.
    allActionsPresent: actions.length === K2_ACTIONS.length,
    everyActionRunnable: K2_ACTIONS.every(a => typeof a.run === 'function'),
    actionTargetsExist: K2_ACTIONS.every(a => {
      const src = a.run.toString();
      const name = (src.match(/\b(K2Palette|openCapturePopover|forceAppRefresh|openSettings)\b/) || [])[1];
      return name === 'K2Palette' ? true : typeof window[name] === 'function';
    }),
    grouped: document.querySelectorAll('#launcher-grid .launcher-group').length === 5,
    sidebarMatches: document.querySelectorAll('#nav-section-everything-body .nav-item').length === 28,
    noInlineStyles: document.querySelectorAll('#launcher-grid [style]').length === 0,
    // Live tools must sort above dead ones inside a group, or the ranking is decorative.
    liveRankFirst: [...document.querySelectorAll('#launcher-grid .launcher-group')].every(g => {
      const cls = [...g.querySelectorAll('.tile')].map(t => t.classList.contains('is-live'));
      return cls.indexOf(false) === -1 || !cls.slice(cls.indexOf(false)).includes(true);
    }),
    liveCount: live.length,
    liveLabels: live.map(t => t.querySelector('.tile-nm').textContent +
      ':' + (t.querySelector('.tile-count')?.textContent || '')),
  };
}));

report(out, 'launcher-ok');
