// Loads the REAL retirement code out of index.html — the staleness rule it depends on
// included — and runs it against a DOM stub thin enough to be honest about what it is.
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';

export const REPO = path.resolve(new URL('.', import.meta.url).pathname, '../../..');

function slice(src, startMark, endMark, label) {
  const a = src.indexOf(startMark), b = src.indexOf(endMark, a + 1);
  if (a < 0 || b < 0 || b <= a) throw new Error(`could not locate ${label} in index.html`);
  return src.slice(a, b);
}

export function loadRetirement(data) {
  const src = fs.readFileSync(path.join(REPO, 'index.html'), 'utf8');
  const staleness = slice(src, '// ─── Stale Task Auto-Triage ───', 'function getStaleTaskCount', 'staleness rule');
  const retirement = slice(src, '// ═══ Task Retirement ═══', '// ═══ Stale Notes Reclaim Panel ═══', 'retirement block');

  const els = new Map();
  const el = (id) => {
    if (!els.has(id)) els.set(id, { id, value: '', textContent: '', innerHTML: '', style: {} });
    return els.get(id);
  };
  let saves = 0;
  const ctx = {
    console, Math, Date, Set, Map, Array, Object, JSON, String, Number, isNaN, parseInt,
    escapeHtml: (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'),
    getTodayStr: () => new Date().toISOString().slice(0, 10),
    saveData: async () => { saves++; },
    showToast: () => {},
    document: { getElementById: (id) => (els.has(id) ? els.get(id) : null) },
  };
  ctx.window = ctx;
  ctx.DATA = data;
  vm.createContext(ctx);
  ctx.window.DATA = data;
  // the page's own elements, so render() does not bail
  ['task-retire-list', 'task-retire-meta', 'task-retire-bulk-toolbar', 'task-retire-bulk-count', 'task-retire-search'].forEach(el);
  vm.runInContext(staleness + '\n' + retirement + '\n;globalThis._RETIRE_ROWS_SHOWN=_RETIRE_ROWS_SHOWN;',
    ctx, { filename: 'index.html#task-retirement' });

  return { ctx, el, saves: () => saves, search: (q) => { el('task-retire-search').value = q; } };
}

export function loadData() {
  const cache = '/tmp/k2data.json';
  if (!fs.existsSync(cache)) throw new Error('missing /tmp/k2data.json — refresh it (see GATES.md)');
  return JSON.parse(fs.readFileSync(cache, 'utf8'));
}
