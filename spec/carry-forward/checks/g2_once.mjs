// G2 — carrying forward happens once. renderJots() runs on every navigation and on every
// data refresh, so a carry that is not idempotent would grow the note every time Ryan
// opens the app.
import { loadCarry, text } from './_load.mjs';

const fail = (m) => { console.log('G2 FAIL: ' + m); process.exit(1); };
const YESTERDAY = '<ul data-type="taskList">'
  + '<li data-checked="false" data-type="taskItem"><div><p>ship the thing</p></div></li>'
  + '<li data-checked="true" data-type="taskItem"><div><p>already done</p></div></li>'
  + '<li data-checked="false" data-type="taskItem"><div><p>call the bank</p></div></li>'
  + '</ul><p>some prose that is not a task</p>';

const docs = {
  '2026-08-29': { content: YESTERDAY },
  '2026-08-30': { content: '<p></p>' },
};
const ctx = loadCarry({ dailyDocs: docs });

const first = ctx.carryForwardUnfinished('2026-08-30');
if (first.carried !== 2) fail(`expected 2 carried, got ${first.carried}`);
if (first.from !== '2026-08-29') fail(`carried from ${first.from}`);
const after1 = docs['2026-08-30'].content;
if (!text(after1).includes('ship the thing') || !text(after1).includes('call the bank')) fail('carried content missing');
if (text(after1).includes('already done')) fail('carried a completed line');
if (text(after1).includes('some prose')) fail('carried non-task prose');
if (!/↩ Carried over from Saturday/.test(after1)) fail('marker missing or not naming the source day');

// re-render, twice more, exactly as navigating back to Jots would
const second = ctx.carryForwardUnfinished('2026-08-30');
const third = ctx.carryForwardUnfinished('2026-08-30');
if (second.carried !== 0 || third.carried !== 0) fail(`re-run carried again: ${second.carried}/${third.carried}`);
if (docs['2026-08-30'].content !== after1) fail('content changed on re-run — not idempotent');

const markers = (docs['2026-08-30'].content.match(/Carried over from/g) || []).length;
const lines = (docs['2026-08-30'].content.match(/data-checked="false"/g) || []).length;
if (markers !== 1) fail(`${markers} markers after 3 runs`);
if (lines !== 2) fail(`${lines} unfinished lines after 3 runs, expected 2`);

// a day whose source has nothing unfinished still gets stamped, so it is asked once, not daily
const docs2 = { '2026-08-29': { content: '<p>nothing but prose</p>' }, '2026-08-30': { content: '<p></p>' } };
const ctx2 = loadCarry({ dailyDocs: docs2 });
const zero = ctx2.carryForwardUnfinished('2026-08-30');
if (zero.carried !== 0) fail('carried something from a doc with no tasks');
if (docs2['2026-08-30'].carriedFrom !== '2026-08-29') fail('zero-carry day was not stamped, so it would re-scan forever');
if (docs2['2026-08-30'].content !== '<p></p>') fail('zero-carry day had its content touched');

console.log(`G2 PASS: 2 of 3 lines carried once with a marker naming Saturday, 3 consecutive runs left the doc byte-identical (1 marker, 2 lines), and a zero-carry day is stamped without touching its content`);
