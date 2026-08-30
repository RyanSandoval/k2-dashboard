#!/usr/bin/env node
// Full-page screenshot of the app at a given width. Ryan judges whether it looks
// like AI slop, and he can only do that off a render.
// Usage: node scripts/shoot.mjs <width> <out.png>
import { withApp } from './page.mjs';

const width = Number(process.argv[2] || 390);
const out = process.argv[3] || `shots/app-${width}.png`;

await withApp(async (page) => {
  // A full-page capture paints position:fixed at its viewport offset, so the tab bar
  // lands mid-image and reads as a layout bug that is not there. Let it flow instead.
  await page.evaluate(() => document.querySelector('.tabbar')?.style.setProperty('position', 'static'));
  await page.screenshot({ path: out, fullPage: true });
}, { width });

console.log('wrote', out);
