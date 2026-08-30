// Loads the REAL carry-forward block out of index.html and runs it. No DOM stub: the
// shipped code is deliberately string-based so the thing under test here is the thing
// that runs in the browser.
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';

export const REPO = path.resolve(new URL('.', import.meta.url).pathname, '../../..');

export function loadCarry(data) {
  const src = fs.readFileSync(path.join(REPO, 'index.html'), 'utf8');
  const a = src.indexOf('// ═══ Carry Forward ═══');
  const b = src.indexOf('// ═══ End Carry Forward ═══');
  if (a < 0 || b < 0 || b <= a) throw new Error('could not locate the carry-forward block in index.html');
  const block = src.slice(a, b);

  const ctx = {
    console, Date, Object, Array, String, Number, JSON, RegExp, isNaN,
    escapeHtml: (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'),
  };
  ctx.window = ctx;
  ctx.DATA = data;
  vm.createContext(ctx);
  ctx.DATA = data;
  vm.runInContext(block, ctx, { filename: 'index.html#carry-forward' });
  return ctx;
}

export function realDocs() {
  const cache = '/tmp/k2data.json';
  if (!fs.existsSync(cache)) throw new Error('missing /tmp/k2data.json — refresh it (see GATES.md)');
  return JSON.parse(fs.readFileSync(cache, 'utf8')).dailyDocs || {};
}

export const text = (html) => String(html).replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();
