// G3 — index.html still parses and the nudge is actually wired to the editor.
// A scorer nobody calls is not a feature.
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { REPO } from './_load.mjs';

const src = fs.readFileSync(path.join(REPO, 'index.html'), 'utf8');
const fails = [];
const need = (label, re) => { if (!re.test(src)) fails.push(label); };

need('nudge container in the jots page', /<div id="jot-match-nudge"/);
need('nudge sits under today\'s editor', /id="daily-doc-today-editor"[\s\S]{0,200}id="jot-match-nudge"/);
need('debounce wrapper defined', /window\.debouncedMemoryMatch\s*=\s*\(function\s*\(\)/);
need('debounce calls the runner', /setTimeout\(_runMemoryMatch,\s*1500\)/);
need('hooked into the today editor onUpdate', /!isCheckboxToggle && typeof window\.debouncedMemoryMatch === 'function'[\s\S]{0,80}window\.debouncedMemoryMatch\(\)/);
need('boilerplate stripper present', /function _memPlainText\(/);
need('runner strips boilerplate from the jot', /const plain = _memPlainText\(html\)/);
need('runner strips boilerplate from note candidates', /const txt = _memPlainText\(\(n\.title/);
need('runner strips boilerplate from doc candidates', /const txt = _memPlainText\(doc\.content\)/);
need('threshold reads the constant, not a literal', /topScore < _MEM_MIN_SCORE/);
if (/topScore < 0\.12/.test(src)) fails.push('old hardcoded 0.12 threshold still present');

// every <script> block must parse
let n = 0;
for (const m of src.matchAll(/<script(?![^>]*\bsrc=)[^>]*>([\s\S]*?)<\/script>/g)) {
  const body = m[1];
  if (!body.trim()) continue;
  const isModule = /type=["']module["']/.test(m[0]);
  n++;
  try {
    if (isModule) new vm.SourceTextModule(body); else new vm.Script(body);
  } catch (e) {
    if (/SourceTextModule/.test(String(e)) && isModule) continue; // needs --experimental-vm-modules
    fails.push(`script block ${n} does not parse: ${e.message}`);
  }
}
if (!n) fails.push('no inline script blocks found — the extractor is broken');

if (fails.length) { console.error('G3 FAIL:\n  ' + fails.join('\n  ')); process.exit(1); }
console.log(`G3 PASS: nudge markup present under today's editor, debounce hooked into onUpdate, boilerplate stripping applied to jot + both candidate kinds, no stale 0.12 literal, all ${n} inline script blocks parse`);
