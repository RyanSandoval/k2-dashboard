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
  o.allToolsReachable = document.querySelectorAll('#launcher-grid .tile').length === K2_TOOLS.length;

  // A badge showing zero is noise; empty must collapse.
  const empty = document.createElement('span');
  empty.className = 'tab-count'; bar.appendChild(empty);
  o.zeroCollapses = getComputedStyle(empty).display === 'none';
  empty.remove();

  // Nothing may still write to a badge id that no longer exists.
  o.noOrphanBadgeWrites = !/mobile-[a-z-]+-badge/.test(document.documentElement.innerHTML);
  return o;
}));

report(out, 'tabbar-ok');
