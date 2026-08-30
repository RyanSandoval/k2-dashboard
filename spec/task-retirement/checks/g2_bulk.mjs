// G2 — the promise of the surface: one action clears a whole group, including the rows
// past the render cap, in a single save, and it can be taken back.
import { loadRetirement, loadData } from './_load.mjs';

const data = loadData();
const h = loadRetirement(JSON.parse(JSON.stringify(data)));
const { ctx } = h;
const fails = [];
const ok = (n, c, d = '') => { if (!c) fails.push(`${n}${d ? ' — ' + d : ''}`); };

ctx.renderTaskRetirement();
const groups = ctx._retireGroups('');
const [src, items] = groups[0];
const cap = ctx._RETIRE_ROWS_SHOWN ?? globalThis._RETIRE_ROWS_SHOWN;

ok('the biggest group is bigger than the render cap, or this gate proves nothing', items.length > cap, `${items.length} vs cap ${cap}`);
ok('the list only renders the cap per group', (h.el('task-retire-list').innerHTML.match(/type="checkbox"/g) || []).length <= groups.length * cap);

ctx.taskRetireSelectSource(src);
ok('select-all covers every row in the group, not just the rendered ones',
  ctx.window._taskRetireSelection.size === new Set(items.map(ctx._taskRetireKey)).size,
  `selected ${ctx.window._taskRetireSelection.size} of ${items.length}`);
ok('the toolbar reports the real count', h.el('task-retire-bulk-count').textContent === `${ctx.window._taskRetireSelection.size} selected`);

const before = h.saves();
const openBefore = ctx._retirableTasks().length;
const lenBefore = ctx.DATA.tasks.length;
await ctx.taskRetireBulk();

ok('exactly one save for the whole batch', h.saves() - before === 1, `${h.saves() - before} saves`);
ok('every task in the group left the pile', ctx._retireGroups('').every(([s]) => s !== src));
ok('the pile shrank by the size of the group', ctx._retirableTasks().length === openBefore - items.length,
  `${ctx._retirableTasks().length} vs expected ${openBefore - items.length}`);
ok('selection cleared', ctx.window._taskRetireSelection.size === 0);

// the invariant the plan-sync cron depends on
ok('nothing was removed from DATA.tasks', ctx.DATA.tasks.length === lenBefore, `${ctx.DATA.tasks.length} vs ${lenBefore}`);
const retired = ctx.DATA.tasks.filter(t => t.archived && (t.source || 'none') === src);
ok('every retired task is soft-archived', retired.length >= items.length && retired.every(t => t.archived === true && !!t.archivedAt));
ok('none were marked for hard purge', !retired.some(t => t.archivedHard));

if (fails.length) { console.error('G2 FAIL:\n  ' + fails.join('\n  ')); process.exit(1); }
console.log(`G2 PASS: selecting "${src}" covered all ${items.length} rows though only ${cap} render, retired them in 1 save, pile ${openBefore} -> ${ctx._retirableTasks().length}, DATA.tasks length unchanged at ${lenBefore}, 0 hard-purged`);
