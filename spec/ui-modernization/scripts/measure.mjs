#!/usr/bin/env node
// Horizontal-overflow check at a given viewport width, measured in a real engine.
// Usage: node scripts/measure.mjs <width>
// Prints "no-overflow" and exits 0 only if every prototype page fits.

import { resolve } from 'node:path';
import { withChrome, withTab, load } from './cdp.mjs';

const width = Number(process.argv[2] || 390);
if (!Number.isFinite(width) || width < 200) {
  console.error('usage: measure.mjs <width>');
  process.exit(2);
}

const PAGES = ['bc-today.html', 'bc-notes.html', 'bc-note.html'];
const PORT = 9334;

const PROBE = `(() => {
  const de = document.documentElement;
  const overflow = de.scrollWidth - de.clientWidth;
  const culprits = [...document.querySelectorAll('body *')]
    .filter(el => Math.round(el.getBoundingClientRect().right) > de.clientWidth + 1)
    .slice(0, 4)
    .map(el => el.tagName.toLowerCase() +
      (el.className && typeof el.className === 'string' && el.className.trim()
        ? '.' + el.className.trim().split(/\\s+/)[0] : ''));
  return JSON.stringify({ overflow, culprits, w: de.clientWidth });
})()`;

let failed = 0;

await withChrome(PORT, async () => {
  for (const page of PAGES) {
    const url = 'file://' + resolve('prototype', page);
    const out = await withTab(PORT, url, async (tab) => {
      await load(tab, url, width);
      const r = await tab.send('Runtime.evaluate', { expression: PROBE, returnByValue: true });
      return JSON.parse(r.result.value);
    });

    if (out.w !== width) {
      console.log(`FAIL ${page}: viewport is ${out.w}px, expected ${width}px`);
      failed++;
    } else if (out.overflow > 0) {
      console.log(`FAIL ${page}: overflows by ${out.overflow}px — ${out.culprits.join(', ') || 'unknown'}`);
      failed++;
    }
  }
});

if (failed) process.exit(1);
console.log('no-overflow');
