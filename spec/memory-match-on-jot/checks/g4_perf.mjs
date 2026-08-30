// G4 — REQ-012: the whole check stays under 100ms on the real corpus, since it runs
// synchronously on the main thread 1.5s after Ryan stops typing.
import { loadMemoryMatch, loadData } from './_load.mjs';

const data = loadData();
const dates = Object.keys(data.dailyDocs || {}).sort().reverse();
const today = dates[0];
const mm = loadMemoryMatch({ data, today });
mm.setJot(data.dailyDocs[dates[1]]?.content || '<p>itinerary map ab test to prod, ticket for cms</p>');

mm.run(); // warm
const runs = [];
for (let i = 0; i < 20; i++) { const t = process.hrtime.bigint(); mm.run(); runs.push(Number(process.hrtime.bigint() - t) / 1e6); }
runs.sort((a, b) => a - b);
const p50 = runs[10], worst = runs[runs.length - 1];
const notes = (data.notes || []).filter((n) => !n.archived).length;

if (worst >= 100) { console.error(`G4 FAIL: worst run ${worst.toFixed(1)}ms over 100ms budget`); process.exit(1); }
console.log(`G4 PASS: ${notes} notes + 30 daily docs scored in ${p50.toFixed(1)}ms median, ${worst.toFixed(1)}ms worst of 20 runs (budget 100ms)`);
