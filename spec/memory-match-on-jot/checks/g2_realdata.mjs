// G2 — against Ryan's live data, the nudge stops firing on boilerplate and still
// surfaces real recall. Includes a control: the pre-fix code must FAIL this check,
// otherwise the gate is not measuring anything.
import fs from 'node:fs';
import { loadMemoryMatch, loadData, BOILERPLATE } from './_load.mjs';

const PREFIX = new URL('./fixtures/prefix-block.js', import.meta.url).pathname;

const data = loadData();
const dates = Object.keys(data.dailyDocs || {}).sort().reverse().slice(0, 30);

function replay(rawCode) {
  const fires = [];
  for (const day of dates) {
    const mm = loadMemoryMatch({ data, today: day, rawCode });
    // the pre-fix fixture has no _memPlainText — fall back to its own tag strip
    const plainOf = mm.ctx._memPlainText || ((h) => String(h || '').replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim());
    const html = data.dailyDocs[day]?.content || '';
    if (plainOf(html).length < 25) continue;
    mm.setJot(html);
    const match = mm.run();
    if (!match) continue;
    const jotTerms = mm.ctx._memTokenize(plainOf(html));
    const candTerms = mm.ctx._memTokenize(match.text);
    const shared = [...jotTerms].filter((t) => candTerms.has(t));
    fires.push({ day, id: match.id, kind: match.kind, title: match.title, shared });
  }
  return fires;
}

const now = replay(null);
const junk = now.filter((f) => f.shared.every((t) => BOILERPLATE.has(t)));
const thin = now.filter((f) => f.shared.length < 3);

// control: the same check against the pre-fix implementation
let controlJunk = null;
try {
  const before = replay(fs.readFileSync(PREFIX, 'utf8'));
  controlJunk = before.filter((f) => f.shared.every((t) => BOILERPLATE.has(t))).length;
} catch (e) { console.error('control error:', e.message); }

const fails = [];
if (junk.length) fails.push(`${junk.length} boilerplate-only nudge(s): ` + junk.map((f) => `${f.day}->${f.id}[${f.shared}]`).join(', '));
if (thin.length) fails.push(`${thin.length} nudge(s) under 3 shared terms: ` + thin.map((f) => `${f.day}[${f.shared}]`).join(', '));
if (now.length < 5) fails.push(`only ${now.length} of ${dates.length} days fire — the nudge has gone inert`);
if (controlJunk === null) fails.push('control did not run, so this check is unproven');
else if (controlJunk === 0) fails.push('control did not fail: the pre-fix code produced no boilerplate matches, so this gate proves nothing');

if (fails.length) { console.error('G2 FAIL:\n  ' + fails.join('\n  ')); process.exit(1); }
console.log(`G2 PASS: ${now.length} of ${dates.length} replayed days fire, 0 on boilerplate, all with >=3 shared terms; control (pre-fix code, same data) fired ${controlJunk} boilerplate-only matches`);
for (const f of now) console.log(`   ${f.day} -> ${f.kind}:${String(f.title).slice(0, 34)}  shared=${f.shared.slice(0, 7).join(',')}`);
