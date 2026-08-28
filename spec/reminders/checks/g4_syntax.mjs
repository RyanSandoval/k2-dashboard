// G4 — every inline <script> in index.html must still parse.
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

const html = readFileSync('/Users/ryansandoval/k2-dashboard/index.html', 'utf8');
const re = /<script(?![^>]*\bsrc=)([^>]*)>([\s\S]*?)<\/script>/gi;
let m, checked = 0, failures = [];
while ((m = re.exec(html))) {
  const attrs = m[1] || '', body = m[2];
  if (/type\s*=\s*["'](?!text\/javascript|module|application\/javascript)/i.test(attrs)) continue;
  if (!body.trim()) continue;
  const line = html.slice(0, m.index).split('\n').length;
  const isModule = /type\s*=\s*["']module["']/i.test(attrs);
  try {
    // ESM blocks must be parsed as modules — vm.Script rejects a bare `import`.
    if (isModule) new vm.SourceTextModule(body, { identifier: `index.html:${line}` });
    else new vm.Script(body, { filename: `index.html:${line}` });
    checked++;
  } catch (e) { failures.push(`script at line ${line}: ${e.message}`); }
}
if (!checked) { console.log('G4 FAIL: no inline scripts found — checker is not looking at anything'); process.exit(1); }
// control: the checker must actually be able to fail
try { new vm.Script('function ( {'); failures.push('control: checker accepted invalid JS'); } catch {}
if (failures.length) { console.log('G4 FAIL:\n  ' + failures.join('\n  ')); process.exit(1); }
console.log(`G4 PASS: ${checked} inline script block(s) parse; control rejection confirmed`);
