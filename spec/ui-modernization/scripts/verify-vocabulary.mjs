#!/usr/bin/env node
// One check for the whole vocabulary, rather than a suite per page. Every ui-* and
// is-* class used anywhere in index.html must resolve to a rule, and no element may
// carry two class attributes — the browser keeps the first and renders the rest
// unstyled, which reads as correct in the markup and wrong on screen.
import { readFileSync } from 'node:fs';
import { withApp, report } from './page.mjs';

const src = readFileSync('/Users/ryansandoval/k2-dashboard/index.html', 'utf8');

// Classes as written in the source, including inside template literals.
const used = new Set();
for (const attr of src.match(/class="[^"]*"/g) || []) {
  for (const c of attr.slice(7, -1).split(/\s+/)) {
    if (/^(ui|is)-[a-z0-9-]+$/.test(c)) used.add(c);
  }
}

// Tags carrying two class attributes, counted in the source so template literals
// are covered too — the DOM only ever shows the surviving one.
const dupeTags = (src.match(/<[a-zA-Z][^>]*>/g) || [])
  .filter(t => t.slice(0, t.indexOf('>')).split('class="').length > 2);

const out = await withApp(page => page.evaluate((usedList) => {
  const defined = new Set();
  for (const sheet of document.styleSheets) {
    let rules; try { rules = sheet.cssRules; } catch { continue; }
    for (const rule of rules || []) {
      (rule.selectorText || '').split(',').forEach(sel => {
        (sel.match(/\.((?:ui|is)-[a-z0-9-]+)/g) || []).forEach(c => defined.add(c.slice(1)));
      });
    }
  }
  return { undefinedClasses: usedList.filter(c => !defined.has(c)), definedCount: defined.size };
}, [...used]), { seedData: false });

report({
  everyClassResolves: out.undefinedClasses.length === 0,
  undefinedClasses: out.undefinedClasses,
  classesUsed: used.size,
  classesDefined: out.definedCount,
  noDuplicateClassAttrs: dupeTags.length === 0,
  duplicateSample: dupeTags.slice(0, 2).map(t => t.slice(0, 100)),
}, 'vocabulary-ok');
