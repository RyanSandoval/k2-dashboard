// G9 — the service worker's push handler must render a notification, and a tap must
// reuse an already-open dashboard rather than stacking windows. Runs the real sw.js
// against a stubbed ServiceWorkerGlobalScope.
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

const src = readFileSync('/Users/ryansandoval/k2-dashboard/sw.js', 'utf8');
const fails = [];
const handlers = {};
const shown = [];
const opened = [];
const focused = [];
const navigated = [];

const existing = { url: 'https://ryansandoval.github.io/k2-dashboard/', focus: () => { focused.push(1); return 'focused'; }, navigate: (u) => navigated.push(u) };
const self_ = {
  addEventListener: (t, fn) => { handlers[t] = fn; },
  registration: { showNotification: (title, opts) => { shown.push({ title, opts }); return Promise.resolve(); } },
  clients: { matchAll: async () => [existing], openWindow: (u) => { opened.push(u); return Promise.resolve(); } },
  skipWaiting: () => {}, caches: undefined,
};
const ctx = { self: self_, caches: { open: async () => ({ add: async () => {} }), keys: async () => [], delete: async () => {} }, console, fetch: async () => ({}), Promise, URL };
ctx.self.caches = ctx.caches;
vm.createContext(ctx);
try { new vm.Script(src).runInContext(ctx); } catch (e) { fails.push('sw.js threw on load: ' + e.message); }

if (!handlers.push) fails.push('no push handler registered');
if (!handlers.notificationclick) fails.push('no notificationclick handler registered');

const waits = [];
const evt = (data) => ({ waitUntil: (p) => waits.push(p), data, notification: null });

if (handlers.push) {
  handlers.push(evt({ json: () => ({ title: '⏰ Reminder', body: 'call the dentist\nask about the crown', url: './#reminders' }) }));
  await Promise.all(waits);
  if (shown.length !== 1) fails.push(`expected 1 notification, got ${shown.length}`);
  else {
    const n = shown[0];
    if (n.title !== '⏰ Reminder') fails.push(`wrong title: ${n.title}`);
    if (!n.opts.body.includes('ask about the crown')) fails.push('notification body lost the note');
    if (n.opts.data.url !== './#reminders') fails.push('notification did not carry its url');
    if (!n.opts.icon) fails.push('notification has no icon');
  }
  // A non-JSON payload must still surface something — iOS drops silent pushes.
  shown.length = 0; waits.length = 0;
  handlers.push(evt({ json: () => { throw new Error('not json'); }, text: () => 'plain text reminder' }));
  await Promise.all(waits);
  if (shown.length !== 1 || !shown[0].opts.body.includes('plain text')) fails.push('non-JSON payload did not render');
  // No payload at all must still show a notification rather than nothing.
  shown.length = 0; waits.length = 0;
  handlers.push(evt(null));
  await Promise.all(waits);
  if (shown.length !== 1) fails.push('payload-less push showed no notification (iOS requires one)');
}

if (handlers.notificationclick) {
  waits.length = 0;
  let closed = false;
  handlers.notificationclick({ waitUntil: (p) => waits.push(p), notification: { close: () => { closed = true; }, data: { url: './#reminders' } } });
  await Promise.all(waits);
  if (!closed) fails.push('notificationclick did not dismiss the notification');
  if (opened.length) fails.push('opened a new window despite an existing dashboard tab');
  if (!focused.length) fails.push('did not focus the existing dashboard');
  if (!navigated.length) fails.push('did not navigate the existing tab to the reminder');
}

if (fails.length) { console.log('G9 FAIL:\n  ' + fails.join('\n  ')); process.exit(1); }
console.log('G9 PASS: push renders (JSON, text and empty payloads); tap dismisses, focuses and navigates the open dashboard');
