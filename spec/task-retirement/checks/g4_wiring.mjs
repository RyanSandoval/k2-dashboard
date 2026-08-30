// G4 — the page is reachable and index.html still parses. A surface nothing routes to
// is not a surface.
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { REPO } from './_load.mjs';

const src = fs.readFileSync(path.join(REPO, 'index.html'), 'utf8');
const fails = [];
const need = (l, re) => { if (!re.test(src)) fails.push(l); };

need('page container exists', /<div class="page" id="page-task-retirement"/);
need('nav entry registered', /\{ page:'task-retirement',.*label:'Task Retirement'/);
need('routed from the primary dispatch', /else if \(page === 'task-retirement'\) renderTaskRetirement\(\);/);
need('routed from the lazy-render dispatch', /\n  if \(page === 'task-retirement'\) renderTaskRetirement\(\);/);
need('expands its nav section', /reference: \['stale-jots','stale-notes','task-retirement'/);
need('search is debounced', /debouncedRenderTaskRetirement/);
need('bulk toolbar markup', /id="task-retire-bulk-toolbar"/);
need('render function exported', /window\.renderTaskRetirement = renderTaskRetirement;/);
need('bulk action exported', /window\.taskRetireBulk = taskRetireBulk;/);
need('select-by-source exported', /window\.taskRetireSelectSource = taskRetireSelectSource;/);
need('dashboard alert points here, not at the 766-item task list', /navigateTo\('task-retirement'\)[^`]*Retire them/);
if (/onclick="navigateTo\('tasks'\)"[^`]*Review Tasks/.test(src)) fails.push('the old "Review Tasks" alert link is still present');
if (/\.find\(t => String\(t\.id\) === id\)/.test(src.slice(src.indexOf('// ═══ Task Retirement ═══'), src.indexOf('// ═══ Stale Notes Reclaim Panel ═══')))) {
  fails.push('retirement still resolves tasks by id alone — duplicate ids will retire the wrong row');
}

let n = 0;
for (const m of src.matchAll(/<script(?![^>]*\bsrc=)[^>]*>([\s\S]*?)<\/script>/g)) {
  if (!m[1].trim() || /type=["']module["']/.test(m[0])) continue;
  n++;
  try { new vm.Script(m[1]); } catch (e) { fails.push(`script block ${n} does not parse: ${e.message}`); }
}
if (!n) fails.push('no script blocks found — extractor broken');

if (fails.length) { console.error('G4 FAIL:\n  ' + fails.join('\n  ')); process.exit(1); }
console.log(`G4 PASS: page, nav entry, both dispatch sites, section expansion and the dashboard alert all point at task-retirement; no id-only lookups left; ${n} script blocks parse`);
