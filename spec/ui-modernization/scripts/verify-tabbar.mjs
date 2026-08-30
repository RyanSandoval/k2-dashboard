#!/usr/bin/env node
// The tab bar is the only nav on a phone. This proves all 34 tools are reachable
// from it, and that its counts come from the same source as the launcher tiles —
// the five mobile-*-badge ids this replaced were a parallel set that went silently
// dead when the drawer they lived in was deleted.
import { withApp, report } from './page.mjs';

const out = await withApp(page => page.evaluate(() => {
  renderAll();
  const o = {};
  const bar = document.getElementById('mobile-nav');
  o.tabBarVisible = getComputedStyle(bar).display !== 'none';

  // WCAG 2.5.8 asks 24x24 and Apple's HIG asks 44x44. Both were already met at
  // 78x56 and it still missed on a real phone: the home-indicator strip overlaps
  // the bottom of the bar, so the usable part is shorter than the measurement.
  // 64 with real padding underneath is the number that actually worked.
  const items = [...bar.querySelectorAll('.mobile-nav-item')];
  const boxes = items.map(i => i.getBoundingClientRect());
  o.tapTargetsBigEnough = boxes.every(r => r.height >= 64 && r.width >= 44);
  o.smallestTapTarget = Math.round(Math.min(...boxes.map(r => r.height)));
  // Clearance below the last row of content, so the bottom row is not on the edge.
  o.barClearsHomeIndicator =
    parseFloat(getComputedStyle(bar).paddingBottom) >= 16;

  // Counts must be present on load, not only after the drawer has been opened once.
  const counts = [...bar.querySelectorAll('.tab-count')];
  o.countsRendered = counts.length === 3;
  const rem = counts.find(c => c.dataset.count === 'reminders');
  o.remindersAgrees = rem.textContent === String(k2ToolCount('reminders') || '');
  const inbox = counts.find(c => c.dataset.count === 'action-inbox');
  o.inboxAgrees = inbox.textContent === (k2ToolCount('action-inbox') > 99 ? '99+'
    : String(k2ToolCount('action-inbox') || ''));

  // Tapping More must actually reach every tool.
  const more = [...bar.querySelectorAll('.mobile-nav-item')].find(i => /More/.test(i.textContent));
  o.moreExists = !!more;
  more.click();
  const drawer = document.getElementById('mobile-more-drawer');
  o.drawerOpens = drawer.classList.contains('open') && getComputedStyle(drawer).display !== 'none';
  o.allToolsReachable = document.querySelectorAll(
    '#launcher-grid .tile:not(.is-action)').length === K2_TOOLS.length;

  // A badge showing zero is noise; empty must collapse.
  const empty = document.createElement('span');
  empty.className = 'tab-count'; bar.appendChild(empty);
  o.zeroCollapses = getComputedStyle(empty).display === 'none';
  empty.remove();

  // Reachability, not existence. Refresh and Settings survived in the sidebar,
  // which is display:none on a phone, so they were gone from mobile for a day and
  // every check still passed. This asks whether a thumb can actually get to them.
  const reachable = (fnName) => {
    const hit = [...document.querySelectorAll('[onclick]')].filter(el =>
      el.getAttribute('onclick').includes(fnName));
    return hit.some(el => {
      // visible now, or inside the drawer the More tab opens
      if (el.offsetParent !== null) return true;
      return !!el.closest('#mobile-more-drawer');
    });
  };
  o.refreshReachable = reachable('forceAppRefresh') || reachable('k2RunAction');
  o.settingsReachable = reachable('openSettings') || reachable('k2RunAction');
  o.actionsInDrawer = document.querySelectorAll('#launcher-grid .tile.is-action').length === 4;

  // Nothing may still write to a badge id that no longer exists.
  o.noOrphanBadgeWrites = !/mobile-[a-z-]+-badge/.test(document.documentElement.innerHTML);
  return o;
}));

report(out, 'tabbar-ok');
