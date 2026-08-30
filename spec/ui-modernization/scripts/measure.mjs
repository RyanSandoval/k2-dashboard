#!/usr/bin/env node
// Horizontal-overflow check at a given viewport width, measured in a real engine.
// Usage: node scripts/measure.mjs <width> [file...]
import { withApp, report } from './page.mjs';

const width = Number(process.argv[2] || 390);
const out = await withApp(page => page.evaluate(() => {
  const de = document.documentElement;
  const overflow = de.scrollWidth - de.clientWidth;
  const culprits = [...document.querySelectorAll('body *')]
    .filter(el => el.offsetParent !== null &&
      Math.round(el.getBoundingClientRect().right) > de.clientWidth + 1)
    .slice(0, 4)
    .map(el => el.tagName.toLowerCase() +
      (typeof el.className === 'string' && el.className.trim()
        ? '.' + el.className.trim().split(/\s+/)[0] : ''));
  return { overflow, culprits };
}), { width });

report({ fitsViewport: out.overflow <= 0, culprits: out.culprits, overflowPx: out.overflow },
  `no-overflow @ ${width}px`);
