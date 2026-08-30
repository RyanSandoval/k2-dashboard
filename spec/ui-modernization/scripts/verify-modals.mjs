#!/usr/bin/env node
// Both modals, same assertions. They share one vocabulary now, so they share one
// check — a second copy of this file is how the styles ended up duplicated too.
import { readFileSync } from 'node:fs';
import { withApp, report, DATA_FILE } from './page.mjs';

const data = JSON.parse(readFileSync(DATA_FILE, 'utf8'));
const task = data.tasks.find(t => t && !t.done && (t.text || '').length > 10);
// Pick a project that actually reaches the callout branches — one that is
// plan-synced (warn callout) and has a goal (ok callout). Otherwise the modal
// renders without them and every assertion about them passes vacuously.
const project = data.projects.find(p => p && p.source === 'plan-sync' && p.planFile && p.goal)
             || data.projects.find(p => p && p.source === 'plan-sync' && p.planFile);
if (!project) { console.log('FAIL: no project exercises the callout branches'); process.exit(1); }

const out = await withApp(page => page.evaluate(({ taskId, projectId }) => {
  const check = (open, arg, root) => {
    open(arg);
    const el = document.getElementById(root);
    const o = { rendered: el.innerHTML.length > 300 };

    // Every ui-* class in the markup must match a real rule. A class that matches
    // nothing is invisible in a diff and obvious on screen.
    // Modifiers count too: is-warn is as easy to typo as ui-panel, and a modifier
    //  that matches nothing fails silently while the base class still renders.
    const used = new Set();
    el.querySelectorAll('[class]').forEach(e => {
      const own = [...e.classList];
      if (!own.some(c => c.startsWith('ui-'))) return;
      own.filter(c => c.startsWith('ui-') || c.startsWith('is-')).forEach(c => used.add(c));
    });
    const defined = new Set();
    for (const sheet of document.styleSheets) {
      let rules; try { rules = sheet.cssRules; } catch { continue; }
      for (const rule of rules || []) {
        (rule.selectorText || '').split(',').forEach(sel => {
          (sel.match(/\.((?:ui|is)-[a-z-]+)/g) || []).forEach(c => defined.add(c.slice(1)));
        });
      }
    }
    o.undefined = [...used].filter(c => !defined.has(c));
    o.everyClassDefined = o.undefined.length === 0;
    o.classesUsed = used.size;

    // The browser keeps only the first class attribute, so a tag with two renders
    // unstyled while the markup reads correctly.
    o.noDupeClass = ![...el.querySelectorAll('*')].some(e =>
      e.outerHTML.slice(0, e.outerHTML.indexOf('>')).split('class="').length > 2);
    return o;
  };

  // Every modal must actually become visible, not merely get a class. One of these
  // opened with style.display = '' and would now render hidden.
  const openable = {};
  [['task-modal', () => openTaskModal(taskId), closeTaskModal],
   ['project-modal', () => openProjectModal(projectId), closeProjectModal],
  ].forEach(([id, open, close]) => {
    const el = document.getElementById(id);
    open();
    openable[id] = getComputedStyle(el).display !== 'none';
    if (typeof close === 'function') { close(); openable[id + '-closes'] =
      getComputedStyle(el).display === 'none'; }
  });

  const t = check(openTaskModal, taskId, 'task-modal-content');
  const p = check(openProjectModal, projectId, 'modal-content');
  const panel = document.querySelector('#modal-content .ui-panel.is-callout');

  return {
    ...openable,
    taskRendered: t.rendered, taskClassesDefined: t.everyClassDefined,
    taskNoDupeClass: t.noDupeClass, taskClasses: t.classesUsed, taskUndefined: t.undefined,
    projRendered: p.rendered, projClassesDefined: p.everyClassDefined,
    projNoDupeClass: p.noDupeClass, projClasses: p.classesUsed, projUndefined: p.undefined,
    // The shared vocabulary has to actually be shared, or the rename bought nothing.
    vocabularyShared: t.classesUsed > 0 && p.classesUsed > 0,
    // is-warn must win over the base is-callout border, which is the whole point.
    calloutRendered: !!panel,
    calloutToned: !panel || (() => {
      const ctx = document.createElement('canvas').getContext('2d', { willReadFrequently: true });
      const px = (c) => { ctx.clearRect(0,0,1,1); ctx.fillStyle = c; ctx.fillRect(0,0,1,1);
        return [...ctx.getImageData(0,0,1,1).data].slice(0,3).join(); };
      const accent = getComputedStyle(document.documentElement)
        .getPropertyValue('--accent').trim();
      return px(getComputedStyle(panel).borderLeftColor) !== px(accent);
    })(),
  };
}, { taskId: task.id, projectId: project.id }));

report(out, 'modals-ok');
