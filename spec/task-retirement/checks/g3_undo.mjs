// G3 — retirement is reversible and survives the cron. The undo must put the pile back
// exactly, and an archived task must stay in DATA.tasks, because the plan-files cron
// dedupes against the live array: drop a row and it is rewritten the next morning.
import fs from 'node:fs';
import { loadRetirement, loadData } from './_load.mjs';

const data = loadData();
const h = loadRetirement(JSON.parse(JSON.stringify(data)));
const { ctx } = h;
const fails = [];
const ok = (n, c, d = '') => { if (!c) fails.push(`${n}${d ? ' — ' + d : ''}`); };

let undoFn = null;
ctx.window.K2Archive = { toast: ({ undoFn: f }) => { undoFn = f; }, renderTrash() {}, renderTrashBadge() {}, notArchived: (t) => !t.archived };

ctx.renderTaskRetirement();
const [src, items] = ctx._retireGroups('')[0];
const snapshot = ctx.DATA.tasks.map(t => ({ id: t.id, text: t.text, archived: !!t.archived, archivedAt: t.archivedAt }));

ctx.taskRetireSelectSource(src);
await ctx.taskRetireBulk();
ok('an undo was offered', typeof undoFn === 'function');
ok('the retirement actually happened', ctx.DATA.tasks.filter(t => t.archived).length > snapshot.filter(t => t.archived).length);

await undoFn();
const after = ctx.DATA.tasks.map(t => ({ id: t.id, text: t.text, archived: !!t.archived, archivedAt: t.archivedAt }));
ok('undo restores the array length', after.length === snapshot.length);
const drift = after.filter((t, i) => t.archived !== snapshot[i].archived || t.archivedAt !== snapshot[i].archivedAt || String(t.id) !== String(snapshot[i].id));
ok('undo restores every archived flag and timestamp exactly', drift.length === 0, `${drift.length} rows differ`);
ok('the pile is back', ctx._retireGroups('').some(([s, g]) => s === src && g.length === items.length));

// the cron's dedupe condition, asserted against the cron's actual prompt text
const cronOwnsDedupe = /if no tasks entry with source==='plan-sync'/.test(
  fs.readFileSync('/tmp/plan-sync-cron.txt', 'utf8'));
ok('the plan-sync cron still dedupes against the live tasks array', cronOwnsDedupe,
  'cron prompt changed — re-check whether soft archive still suppresses regeneration');

if (fails.length) { console.error('G3 FAIL:\n  ' + fails.join('\n  ')); process.exit(1); }
console.log(`G3 PASS: retiring ${items.length} "${src}" tasks is fully reversible (0 rows drift after undo), rows stay in DATA.tasks, and the plan-sync cron still dedupes against that array so retirement is not regenerated`);
