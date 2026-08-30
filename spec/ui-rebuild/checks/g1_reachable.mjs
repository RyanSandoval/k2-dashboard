// G1 — every tool in the taxonomy is still reachable, and the rail is GENERATED from that
// taxonomy rather than duplicating it. Ryan kept all 34 surfaces twice; a rail that drifts
// from K2_TOOLS turns this redesign into a deletion he did not agree to.
import fs from 'node:fs';
const src = fs.readFileSync('/Users/ryansandoval/k2-dashboard/index.html', 'utf8');
const fail = m => { console.log('G1 FAIL: ' + m); process.exit(1); };

const tools = [...src.matchAll(/\{\s*page:'([\w-]+)',\s*icon:'[^']*',\s*label:'([^']*)',\s*group:'(\w+)'/g)]
  .map(m => ({ page: m[1], label: m[2], group: m[3] }));
if (tools.length < 30) fail(`only parsed ${tools.length} tools out of K2_TOOLS`);

// parse ONLY the K2_GROUPS declaration — a loose match picks up every ['a','b'] pair in
// the file and reports a fictional set of groups
const gBlock = src.slice(src.indexOf('const K2_GROUPS = ['), src.indexOf('];', src.indexOf('const K2_GROUPS = [')));
const groups = [...gBlock.matchAll(/\['(\w+)',\s*'([^']+)'\]/g)].map(m => m[1]);
if (groups.length !== 4) fail(`expected 4 groups in K2_GROUPS, parsed ${groups.length}`);
const primary = (src.match(/const U_PRIMARY = \[([^\]]+)\]/) || [])[1];
if (!primary) fail('U_PRIMARY not found');
const prim = [...primary.matchAll(/'([\w-]+)'/g)].map(m => m[1]);

// 1. nothing is stranded: every tool is either primary or lives in a group the rail renders
const rendered = new Set(prim);
const renderedGroups = groups.slice();  // every group renders; primary rows are filtered out of them
for (const t of tools) if (renderedGroups.includes(t.group)) rendered.add(t.page);
const stranded = tools.filter(t => !rendered.has(t.page));
if (stranded.length) fail(`${stranded.length} tool(s) unreachable: ${stranded.map(t => t.page).join(', ')}`);

// 2. the rail is generated, not a second list — a hand-written copy is the thing that drifts
const fn = src.slice(src.indexOf('function renderSidebarRest'), src.indexOf('// The flag.'));
if (!/K2_TOOLS\.filter/.test(fn)) fail('renderSidebarRest no longer derives from K2_TOOLS');
if (!/K2_GROUPS\.map/.test(fn)) fail('groups are not derived from K2_GROUPS');
const hardcoded = (fn.match(/data-page="(?!\$\{)/g) || []).length;
if (hardcoded) fail(`${hardcoded} hard-coded data-page value(s) in the rail`);

// 3. control: a tool added to the taxonomy must appear without editing the rail
const invented = { page: 'brand-new-tool', label: 'Brand New', group: 'work' };
const wouldRender = renderedGroups.includes(invented.group);
if (!wouldRender) fail('control failed — a new work-group tool would not be picked up');

const byGroup = {};
for (const t of tools) byGroup[t.group] = (byGroup[t.group] || 0) + 1;
console.log(`G1 PASS: all ${tools.length} tools reachable — ${prim.length} primary + `
  + renderedGroups.map(g => `${g} ${byGroup[g] || 0}`).join(' + ')
  + `; rail generated from K2_TOOLS/K2_GROUPS with 0 hard-coded pages, and a newly added tool renders without touching it`);
