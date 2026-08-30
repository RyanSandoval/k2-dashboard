// G1 — the pile the surface shows is the right pile, on Ryan's real data.
import { loadRetirement, loadData } from './_load.mjs';

const data = loadData();
const { ctx } = loadRetirement(data);
const fails = [];
const ok = (n, c, d = '') => { if (!c) fails.push(`${n}${d ? ' — ' + d : ''}`); };

const items = ctx._retirableTasks();
ok('finds a real pile', items.length > 100, `got ${items.length}`);
ok('no completed tasks', !items.some(t => t.done || t.status === 'done'));
ok('no subtasks', !items.some(t => t.parentId));
ok('no already-archived tasks', !items.some(t => t.archived));
ok('every item is stale by the app\'s own rule', items.every(t => ctx.isTaskStale(t)));
ok('oldest first', items.every((t, i) => i === 0 || ctx._taskAgeDays(items[i - 1]) >= ctx._taskAgeDays(t)));

// a task snoozed into the future must drop out — that is what Snooze is for
const victim = items[0];
const future = new Date(Date.now() + 9 * 86400000).toISOString().slice(0, 10);
const prior = victim.hideUntil;
victim.hideUntil = future;
ok('a snoozed task leaves the pile', !ctx._retirableTasks().some(t => t.id === victim.id));
victim.hideUntil = prior;
ok('and comes back when the snooze lapses', ctx._retirableTasks().some(t => t.id === victim.id));

// grouping must not lose or duplicate anything
const groups = ctx._retireGroups('');
const grouped = groups.reduce((n, [, g]) => n + g.length, 0);
ok('grouping is lossless', grouped === items.length, `${grouped} grouped vs ${items.length} found`);
// A key may legitimately repeat — the live store holds one id three times with identical
// text, and true duplicates should retire together. What must never happen is a key
// conflating two DIFFERENT tasks, which is exactly what keying on id alone did.
const byKey = new Map();
for (const [, g] of groups) for (const t of g) {
  const k = ctx._taskRetireKey(t);
  if (!byKey.has(k)) byKey.set(k, []);
  byKey.get(k).push(t);
}
const conflated = [...byKey.values()].filter((rows) => new Set(rows.map((r) => (r.text || r.title || ''))).size > 1);
ok('no key conflates two different tasks', conflated.length === 0, `${conflated.length} conflated`);
const dupKeys = [...byKey.values()].filter((r) => r.length > 1).length;
// and the bug this replaced must still be demonstrable, or the guard is untested
const idOnly = new Map();
for (const [, g] of groups) for (const t of g) {
  const k = String(t.id);
  if (!idOnly.has(k)) idOnly.set(k, []);
  idOnly.get(k).push(t);
}
const wouldConflate = [...idOnly.values()].filter((rows) => new Set(rows.map((r) => (r.text || r.title || ''))).size > 1).length;
ok('control: keying on id alone would still conflate, so this guard is doing work', wouldConflate > 0, `${wouldConflate}`);
ok('biggest group first', groups.every((g, i) => i === 0 || groups[i - 1][1].length >= g[1].length));
ok('the machine source dominates, which is the premise of the surface',
  groups[0][0] === 'plan-sync' && groups[0][1].length > items.length / 2,
  `${groups[0][0]}=${groups[0][1].length} of ${items.length}`);

if (fails.length) { console.error('G1 FAIL:\n  ' + fails.join('\n  ')); process.exit(1); }
console.log(`G1 PASS: ${items.length} stale tasks in ${groups.length} groups, oldest first, lossless, largest is ${groups[0][0]} at ${groups[0][1].length}; snoozing removes and restores; ${dupKeys} true-duplicate key(s) share a row, 0 conflated where id-only keying would have conflated ${wouldConflate}`);
