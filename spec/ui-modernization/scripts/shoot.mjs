#!/usr/bin/env node
// Full-page screenshots of every prototype at phone and desktop width.
// Ryan decides whether this looks like AI slop, and he can only do that off a render.

import { writeFileSync, mkdirSync } from 'node:fs';
import { resolve, join } from 'node:path';
import { withChrome, withTab, load } from './cdp.mjs';

const PAGES = ['bc-today.html', 'bc-notes.html', 'bc-note.html'];
const WIDTHS = [390, 1280];
const PORT = 9335;
const OUT = 'shots';

mkdirSync(OUT, { recursive: true });

await withChrome(PORT, async () => {
  for (const page of PAGES) {
    const url = 'file://' + resolve('prototype', page);
    for (const width of WIDTHS) {
      await withTab(PORT, url, async (tab) => {
        await load(tab, url, width);
        // A full-page capture paints position:fixed elements at their viewport offset, so
        // the tab bar lands in the middle of a tall screenshot and reads like a layout bug
        // that is not there. absolute+bottom:0 does not help — it resolves against the
        // initial containing block, which is still the viewport. Let it flow instead: the
        // bar is the last element in the body, so static puts it at the true page bottom.
        await tab.send('Runtime.evaluate', { expression: `
          document.querySelector('.tabbar')?.style.setProperty('position','static')` });
        const shot = await tab.send('Page.captureScreenshot',
          { format: 'png', captureBeyondViewport: true });
        const name = `${page.replace(/^bc-|\.html$/g, '')}-${width}.png`;
        writeFileSync(join(OUT, name), Buffer.from(shot.data, 'base64'));
        console.log('wrote', join(OUT, name));
      });
    }
  }
});
