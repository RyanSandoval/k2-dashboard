#!/usr/bin/env node
// Renders the real task modal for a real task and checks each converted class
// resolves to the declaration its inline style used to carry.
import { readFileSync } from 'node:fs';
import { withApp, report, DATA_FILE } from './page.mjs';

const task = JSON.parse(readFileSync(DATA_FILE, 'utf8'))
  .tasks.find(t => t && !t.done && (t.text || '').length > 10);

const out = await withApp(page => page.evaluate((id) => {
  openTaskModal(id);
  const root = document.getElementById('task-modal-content');
  const cs = sel => { const e = root.querySelector(sel); return e && getComputedStyle(e); };
  const o = { rendered: root.innerHTML.length > 500 };

  const panel = cs('.tm-panel');
  o.panelPadded = !!panel && panel.paddingTop === '10px';
  o.panelSurfaced = !!panel && panel.backgroundColor !== 'rgba(0, 0, 0, 0)';
  const label = cs('.tm-label');
  o.labelUpper = !!label && label.textTransform === 'uppercase';
  const head = cs('.tm-head');
  o.headIsFlex = !!head && head.display === 'flex' && head.gap === '12px';
  o.bodyFlexes = cs('.tm-head-body')?.flexGrow === '1';

  // Two class attributes on one tag: the browser drops the second, so the element
  // renders unstyled while the markup reads correctly.
  o.noDupeClass = ![...root.querySelectorAll('*')].some(e =>
    e.outerHTML.slice(0, e.outerHTML.indexOf('>')).split('class="').length > 2);

  // Every tm-* class in the markup must match a real rule.
  const used = new Set();
  root.querySelectorAll('[class]').forEach(e =>
    e.classList.forEach(c => c.startsWith('tm-') && used.add(c)));
  const defined = new Set();
  for (const sheet of document.styleSheets) {
    let rules; try { rules = sheet.cssRules; } catch { continue; }
    for (const rule of rules || []) {
      (rule.selectorText || '').split(',').forEach(sel => {
        const m = sel.trim().match(/\.(tm-[a-z-]+)/); if (m) defined.add(m[1]);
      });
    }
  }
  o.undefinedClasses = [...used].filter(c => !defined.has(c));
  o.everyClassDefined = o.undefinedClasses.length === 0;
  o.classesUsed = used.size;
  return o;
}, task.id));

report(out, 'task-modal-ok');
