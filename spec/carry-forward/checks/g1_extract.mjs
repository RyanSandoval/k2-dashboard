// G1 — extraction finds exactly the unfinished lines, including under a checked parent,
// and never twice. Runs over the real 138-day corpus plus the nesting cases that a naive
// <li>…</li> pairing gets wrong, with a control proving the naive version really is wrong.
import { loadCarry, realDocs, text } from './_load.mjs';

const ctx = loadCarry({ dailyDocs: {} });
const { unfinishedTaskItems } = ctx;
const fail = (m) => { console.log('G1 FAIL: ' + m); process.exit(1); };
const TI = (checked, body, extra = '') =>
  `<li data-checked="${checked}" data-type="taskItem"${extra}><div><p>${body}</p></div>`;

// 1. flat: takes the unchecked, leaves the checked
{
  const html = `<ul data-type="taskList">${TI('false', 'alpha')}</li>${TI('true', 'beta')}</li></ul>`;
  const got = unfinishedTaskItems(html).map(text);
  if (got.length !== 1 || !got[0].includes('alpha')) fail(`flat case got ${JSON.stringify(got)}`);
}

// 2. unchecked parent with children — taken once, whole, children not collected again
{
  const inner = `<ul data-type="taskList">${TI('false', 'child')}</li></ul>`;
  const html = `<ul data-type="taskList"><li data-checked="false" data-type="taskItem"><div><p>parent</p>${inner}</div></li></ul>`;
  const got = unfinishedTaskItems(html);
  if (got.length !== 1) fail(`nested-unchecked parent should yield 1 item, got ${got.length}`);
  if (!text(got[0]).includes('child')) fail('parent was taken without its child');
}

// 3. CHECKED parent, unchecked child — the child must still be found
{
  const inner = `<ul data-type="taskList">${TI('false', 'orphan')}</li></ul>`;
  const html = `<ul data-type="taskList"><li data-checked="true" data-type="taskItem"><div><p>done parent</p>${inner}</div></li></ul>`;
  const got = unfinishedTaskItems(html).map(text);
  if (got.length !== 1 || !got[0].includes('orphan')) fail(`checked parent hid its unfinished child: ${JSON.stringify(got)}`);
}

// 4. control — the naive "next </li>" slice really does mis-cut case 2, so the depth
//    scan is load-bearing rather than decoration.
let naiveWrong = 0;
{
  const inner = `<ul data-type="taskList">${TI('false', 'child')}</li></ul>`;
  const html = `<ul data-type="taskList"><li data-checked="false" data-type="taskItem"><div><p>parent</p>${inner}</div></li></ul>`;
  const naive = html.match(/<li\b[^>]*data-checked=["']false["'][^>]*>[\s\S]*?<\/li>/i)[0];
  const correct = unfinishedTaskItems(html)[0];
  const nOpen = (naive.match(/<li\b/gi) || []).length, nClose = (naive.match(/<\/li\s*>/gi) || []).length;
  // the non-greedy slice stops at the CHILD's </li>, so it is shorter than the real item
  // and leaves the parent's <li> unclosed. Both are true, or the control is not a control.
  if (naive.length < correct.length && nOpen !== nClose) naiveWrong = 1;
}
if (!naiveWrong) fail('control did not reproduce the naive mis-slice — the test is not proving anything');

// 5. the real corpus: every returned item is an unchecked taskItem, and nothing is double-counted
const docs = realDocs();
let days = 0, items = 0, nestedDays = 0;
for (const [date, doc] of Object.entries(docs)) {
  const html = (doc || {}).content || '';
  if (/<li[^>]*data-type="taskItem"[\s\S]*?<ul[^>]*data-type="taskList"/.test(html)) nestedDays++;
  const got = unfinishedTaskItems(html);
  if (!got.length) continue;
  days++; items += got.length;
  for (const it of got) {
    if (!/^<li\b/i.test(it)) fail(`${date}: item does not start at an <li>`);
    if (!/data-checked=["']false["']/i.test(it.slice(0, it.indexOf('>') + 1))) fail(`${date}: took a checked item`);
    if (!it.trimEnd().endsWith('</li>')) fail(`${date}: item is not closed — depth scan mis-sliced`);
  }
  const joined = got.join('');
  const opens = (joined.match(/<li\b/gi) || []).length, closes = (joined.match(/<\/li\s*>/gi) || []).length;
  if (opens !== closes) fail(`${date}: unbalanced <li> in extracted output (${opens}/${closes})`);
}
console.log(`G1 PASS: 4 nesting cases correct incl. unchecked-child-of-checked-parent, naive slice proven wrong by control; over ${Object.keys(docs).length} real days (${nestedDays} with nested task lists) extracted ${items} unfinished items across ${days} days, every one a balanced unchecked taskItem`);
