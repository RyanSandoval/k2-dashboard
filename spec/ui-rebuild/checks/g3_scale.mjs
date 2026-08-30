// G3 — the new CSS is on-scale. Ad-hoc values are the named cause of amateur-looking UI,
// and the mockups this replaces failed exactly here (7/10 font sizes and 15/19 spacing
// values off-scale) while still looking better than what they replaced. Looking better is
// not the same as being designed, which is why this is a gate and not a preference.
import fs from 'node:fs';
const src = fs.readFileSync('/Users/ryansandoval/k2-dashboard/index.html', 'utf8');
const fail = m => { console.log('G3 FAIL: ' + m); process.exit(1); };

const a = src.indexOf('<style id="ui2-design-system">');
const b = src.indexOf('</style>', a);
if (a < 0 || b < 0) fail('ui2 stylesheet not found');
let css = src.slice(a, b);
css = css.replace(/\/\*[\s\S]*?\*\//g, '');          // comments quote off-scale numbers on purpose

const TYPE = new Set([12,14,16,18,20,24,30,36,48,60,72]);
const SPACE = new Set([0,4,8,12,16,24,32,48,64,96,128]);
const WEIGHT = new Set([400,500,600,700]);

// the token declarations themselves define the scale; the rules must then use var()
const decls = css.slice(css.indexOf('body.ui2{'), css.indexOf('body.ui2{background'));
const rules = css.slice(css.indexOf('body.ui2{background'));

const litType = [...rules.matchAll(/font-size\s*:\s*([^;}\n]+)/g)]
  .flatMap(m => [...m[1].replace(/var\([^)]*\)/g,'').matchAll(/([\d.]+)px/g)].map(x => +x[1]))
  .filter(v => !TYPE.has(v));
if (litType.length) fail(`off-scale font-size in rules: ${[...new Set(litType)].join(', ')}`);

const litSpace = [...rules.matchAll(/(?:padding|margin|gap)[a-z-]*\s*:\s*([^;}\n]+)/g)]
  .flatMap(m => [...m[1].replace(/var\([^)]*\)|calc\([^)]*\)/g,'').matchAll(/([\d.]+)px/g)].map(x => +x[1]))
  .filter(v => !SPACE.has(v));
if (litSpace.length) fail(`off-scale spacing in rules: ${[...new Set(litSpace)].join(', ')}`);

const weights = [...css.matchAll(/font-weight\s*:\s*(\d+)/g)].map(m => +m[1]).filter(v => !WEIGHT.has(v));
if (weights.length) fail(`off-scale font-weight: ${[...new Set(weights)].join(', ')}`);

const radii = [...rules.matchAll(/border-radius\s*:\s*([^;}\n]+)/g)]
  .flatMap(m => [...m[1].replace(/var\([^)]*\)/g,'').matchAll(/([\d.]+)px/g)].map(x => +x[1]));
if (radii.length) fail(`border-radius bypassing --u-r: ${[...new Set(radii)].join(', ')}`);

// control — the audit must be capable of failing
if (!/font-size:\s*var\(--u-text/.test(rules)) fail('control: found no var() font sizes, the probe is not reading the rules');
const usesVar = (rules.match(/var\(--u-(space|text)-/g) || []).length;
if (usesVar < 20) fail(`only ${usesVar} scale references in the rules — that is not a system`);

console.log(`G3 PASS: 0 off-scale font sizes, spacing values or radii in the ui2 rules; `
  + `weights limited to ${[...new Set([...css.matchAll(/font-weight\s*:\s*(\d+)/g)].map(m=>m[1]))].join('/')}; `
  + `${usesVar} scale references, every radius via --u-r`);
