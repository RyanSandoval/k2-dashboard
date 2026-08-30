// G3 — the gate that matters. The daily note is the one artifact in this app that is
// purely Ryan's writing. Carry-forward must never overwrite it and must never mutate the
// day it reads from.
import { loadCarry, realDocs } from './_load.mjs';

const fail = (m) => { console.log('G3 FAIL: ' + m); process.exit(1); };
const YESTERDAY = '<ul data-type="taskList"><li data-checked="false" data-type="taskItem">'
  + '<div><p>unfinished</p></div></li></ul>';

// 1. a day Ryan has already typed into is left completely alone
for (const [label, written] of [
  ['prose', '<p>I wrote this before the app rendered</p>'],
  ['a task', '<ul data-type="taskList"><li data-checked="false" data-type="taskItem"><div><p>mine</p></div></li></ul>'],
  ['an image', '<p></p><img src="x.png">'],
  ['an agent result', '<div data-type="agentResult" data-label="MW-1"></div>'],
]) {
  const docs = { '2026-08-29': { content: YESTERDAY }, '2026-08-30': { content: written } };
  const ctx = loadCarry({ dailyDocs: docs });
  const r = ctx.carryForwardUnfinished('2026-08-30');
  if (r.carried !== 0) fail(`carried into a day already holding ${label}`);
  if (docs['2026-08-30'].content !== written) fail(`mutated a day already holding ${label}`);
}

// 2. blank scaffolding still counts as blank
for (const blank of ['<p></p>', '', '<p><br></p>', '<p>&nbsp;</p>', '<p></p><p></p>']) {
  const docs = { '2026-08-29': { content: YESTERDAY }, '2026-08-30': { content: blank } };
  const ctx = loadCarry({ dailyDocs: docs });
  if (ctx.carryForwardUnfinished('2026-08-30').carried !== 1) fail(`treated ${JSON.stringify(blank)} as written-in`);
}

// 3. the source day is never mutated — checked against the real 138-day corpus
const real = realDocs();
const before = JSON.stringify(real);
const dates = Object.keys(real).sort();
let carriedTotal = 0;
for (const d of dates) {
  const docs = JSON.parse(before);
  docs[d] = { content: '<p></p>' };                       // pretend this day is brand new
  const ctx = loadCarry({ dailyDocs: docs });
  const r = ctx.carryForwardUnfinished(d);
  carriedTotal += r.carried;
  if (r.from) {
    const src = JSON.stringify(docs[r.from]), orig = JSON.stringify(real[r.from]);
    if (src !== orig) fail(`${d}: mutated its source day ${r.from}`);
  }
  for (const other of dates) {
    if (other === d) continue;
    if (JSON.stringify(docs[other]) !== JSON.stringify(real[other])) fail(`${d}: collaterally changed ${other}`);
  }
}
if (JSON.stringify(real) !== before) fail('the corpus itself was mutated in place');

// 4. no source day at all (the very first note ever) is a no-op, not a crash
const ctx4 = loadCarry({ dailyDocs: { '2026-01-01': { content: '<p></p>' } } });
if (ctx4.carryForwardUnfinished('2026-01-01').carried !== 0) fail('carried from nowhere');

console.log(`G3 PASS: 4 kinds of already-written day left byte-identical, 5 blank shapes still carry, and replaying all ${dates.length} real days (${carriedTotal} lines carried) mutated no source day and no other day`);
