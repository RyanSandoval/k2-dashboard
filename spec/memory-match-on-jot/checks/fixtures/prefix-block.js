// FIXTURE — the memory-match block exactly as it shipped in PR #12 (jaccard, no
// boilerplate stripping). Committed so G2's control test stays runnable after the
// fix lands. Do not 'fix' this file: its job is to fail.
// TASK-001: Tokenizer + stoplist
const _MEM_STOPLIST = new Set(['a','an','the','and','or','but','in','on','at','to','for','of','with','by','from','up','about','into','then','than','that','this','these','those','is','are','was','were','be','been','being','have','has','had','do','does','did','will','would','could','should','may','might','can','not','no','i','me','my','we','our','you','your','it','its','he','she','they','them']);
function _memTokenize(text) {
  const tokens = (text || '').toLowerCase().replace(/[^a-z0-9\s]/g, ' ').split(/\s+/);
  const out = new Set();
  for (const t of tokens) { if (t.length >= 3 && !_MEM_STOPLIST.has(t)) out.add(t); }
  return out;
}

// TASK-002: Jaccard similarity score
function _memMatchScore(setA, setB) {
  if (!setA.size || !setB.size) return 0;
  let intersection = 0;
  for (const t of setA) { if (setB.has(t)) intersection++; }
  return intersection / (setA.size + setB.size - intersection);
}

// TASK-003: Main match runner
function _runMemoryMatch() {
  if (!window._todayEditor) return;
  const html = window._todayEditor.getHTML();
  const plain = (html || '').replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();
  if (plain.length < 25) { renderJotMatchNudge(null); return; }
  const jotTerms = _memTokenize(plain);
  const today = window._todayEditorDate || '';
  const candidates = [];
  // Notes (exclude archived)
  for (const n of (window.DATA?.notes || [])) {
    if (n.archived) continue;
    const txt = ((n.title || '') + ' ' + (n.text || '')).replace(/<[^>]+>/g, ' ');
    const title = (n.title && n.title.trim()) || txt.trim().split('\n')[0].slice(0, 60) || 'Untitled';
    candidates.push({ kind: 'note', id: n.id, title, text: txt, date: (n.created || '').slice(0, 10) });
  }
  // Past daily docs (last 30, excluding today)
  const docDates = Object.keys(window.DATA?.dailyDocs || {}).filter(d => d !== today).sort().reverse().slice(0, 30);
  for (const date of docDates) {
    const doc = (window.DATA?.dailyDocs || {})[date];
    const txt = (doc.content || '').replace(/<[^>]+>/g, ' ');
    const month = date.slice(5, 7);
    const day = parseInt(date.slice(8, 10), 10);
    const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
    const title = (months[parseInt(month, 10) - 1] || month) + ' ' + day;
    candidates.push({ kind: 'doc', id: date, title, text: txt, date });
  }
  // Score all candidates
  let topMatch = null, topScore = 0;
  for (const cand of candidates) {
    const score = _memMatchScore(jotTerms, _memTokenize(cand.text));
    if (score > topScore) { topScore = score; topMatch = cand; }
  }
  if (topScore < 0.12) { renderJotMatchNudge(null); return; }
  // Dismiss logic: stay hidden if same match was dismissed
  if (window._memMatchDismissed && topMatch.id === window._memMatchLastId) return;
  // New top match clears dismiss
  if (topMatch.id !== window._memMatchLastId) window._memMatchDismissed = false;
  renderJotMatchNudge(topMatch);
}

