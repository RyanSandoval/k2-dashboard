// Loads the REAL memory-match code out of index.html and evaluates it.
// Deliberately not a reimplementation: a gate that scores with its own copy of the
// algorithm passes while index.html is broken.
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';

export const REPO = path.resolve(new URL('.', import.meta.url).pathname, '../../..');

export function loadMemoryMatch({ data = {}, today = '', file = null, rawCode = null } = {}) {
  const src = rawCode ?? fs.readFileSync(file || path.join(REPO, 'index.html'), 'utf8');
  const start = src.indexOf('// TASK-001: Tokenizer + stoplist');
  const end = src.indexOf('// TASK-005: Render nudge UI');
  const code = rawCode ? src : (() => {
    if (start < 0 || end < 0 || end <= start) throw new Error('could not locate the memory-match block in index.html');
    return src.slice(start, end);
  })();
  const shown = [];
  const ctx = {
    console,
    Math,
    Set,
    Object,
    escapeHtml: (s) => String(s),
    renderJotMatchNudge: (m) => shown.push(m),
    document: { getElementById: () => null },
  };
  ctx.window = ctx;
  ctx.DATA = data;
  ctx.window.DATA = data;
  ctx.window._todayEditorDate = today;
  vm.createContext(ctx);
  // top-level `const` lands in the script's lexical scope, not on the context object,
  // so re-export the tuning constants explicitly rather than reading undefined.
  const hasConsts = /_MEM_MIN_OVERLAP/.test(code);
  vm.runInContext(code + (hasConsts ? '\n;globalThis._MEM_MIN_OVERLAP=_MEM_MIN_OVERLAP;globalThis._MEM_MIN_SCORE=_MEM_MIN_SCORE;' : ''),
    ctx, { filename: 'index.html#memory-match' });
  return {
    ctx,
    shown,
    setJot(html) {
      ctx.window._todayEditor = { getHTML: () => html };
    },
    run() {
      shown.length = 0;
      ctx.window._memMatchDismissed = false;
      ctx.window._memMatchLastId = undefined;
      ctx._runMemoryMatch();
      return shown[shown.length - 1] ?? null;
    },
  };
}

export function loadData() {
  const cache = '/tmp/k2data.json';
  if (!fs.existsSync(cache)) {
    throw new Error('missing /tmp/k2data.json — fetch it with: gh api repos/RyanSandoval/k2-data/git/blobs/$(gh api repos/RyanSandoval/k2-data/contents/data.json --jq .sha) --jq .content | tr -d "\\n" | base64 -d > /tmp/k2data.json');
  }
  return JSON.parse(fs.readFileSync(cache, 'utf8'));
}

// The words the app itself injects into every daily doc. A nudge whose shared terms
// are a subset of these is a boilerplate collision, not recall.
export const BOILERPLATE = new Set(['end', 'day', 'what', 'got', 'done', 'carrying', 'over', 'overdue', 'due', 'today', 'calendar', 'morning', 'brief']);
