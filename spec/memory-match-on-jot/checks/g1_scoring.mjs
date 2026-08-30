// G1 — the real tokenizer/scorer: boilerplate is stripped, scoring is length-neutral,
// and a thin coincidence cannot produce a match.
import { loadMemoryMatch } from './_load.mjs';

const { ctx } = loadMemoryMatch();
const { _memTokenize, _memPlainText, _memMatchScore, _MEM_MIN_OVERLAP, _MEM_MIN_SCORE } = ctx;
const fails = [];
const ok = (name, cond, detail = '') => { if (!cond) fails.push(`${name}${detail ? ' — ' + detail : ''}`); };

// --- boilerplate stripping ---
const eod = "<h2>\u{1F305} End of Day</h2><p>What got done? What's carrying over?</p><p></p>";
ok('eod template strips to empty', _memPlainText(eod) === '', JSON.stringify(_memPlainText(eod)));
ok('curly apostrophe variant strips too',
  _memPlainText("<h2>\u{1F305} End of Day</h2><p>What got done? What’s carrying over?</p>") === '');
ok('generated <h2> sections are dropped',
  _memPlainText('<h2>\u{1F534} Overdue</h2><p>ship the itinerary map</p>') === 'ship the itinerary map',
  _memPlainText('<h2>\u{1F534} Overdue</h2><p>ship the itinerary map</p>'));
ok("Ryan's prose survives intact",
  _memPlainText('<p>video transition from vimeo to youtube for AEO benefit</p>') === 'video transition from vimeo to youtube for AEO benefit');
ok('a doc that is only boilerplate has no terms', _memTokenize(_memPlainText(eod)).size === 0);

// --- scoring is length-neutral (the Jaccard bug) ---
const jot = _memTokenize('itinerary map ab test prod ticket');
const bigNote = _memTokenize('itinerary map ab test prod ticket ' + Array.from({length: 200}, (_, i) => 'filler' + i).join(' '));
const jaccard = 6 / (jot.size + bigNote.size - 6);
ok('long candidate is not penalised for length', _memMatchScore(jot, bigNote) === 1,
  `got ${_memMatchScore(jot, bigNote)}`);
ok('...and jaccard would have failed here', jaccard < _MEM_MIN_SCORE, `jaccard=${jaccard.toFixed(3)}`);

// --- min-overlap rejects coincidence ---
const two = _memTokenize('itinerary map');
ok(`${_MEM_MIN_OVERLAP - 1} shared terms scores 0`, _memMatchScore(two, _memTokenize('itinerary map elsewhere')) === 0,
  `got ${_memMatchScore(two, _memTokenize('itinerary map elsewhere'))}`);
ok(`${_MEM_MIN_OVERLAP} shared terms scores`, _memMatchScore(_memTokenize('itinerary map prod'), _memTokenize('itinerary map prod elsewhere')) > 0);
ok('disjoint sets score 0', _memMatchScore(_memTokenize('hello there friend'), _memTokenize('world apart wholly')) === 0);
ok('empty set scores 0', _memMatchScore(new Set(), _memTokenize('anything at all here')) === 0);

// --- tokenizer contract ---
ok('stopwords and short tokens dropped', !_memTokenize('the of a an it be').size);
ok('punctuation split, case folded', _memTokenize('AEO/SGE, Viking!').has('viking') && _memTokenize('AEO/SGE, Viking!').has('aeo'));

if (fails.length) { console.error('G1 FAIL:\n  ' + fails.join('\n  ')); process.exit(1); }
console.log(`G1 PASS: boilerplate stripped to nothing, scoring is length-neutral where jaccard scored ${jaccard.toFixed(3)}, fewer than ${_MEM_MIN_OVERLAP} shared terms rejected (${13 - fails.length} assertions)`);
