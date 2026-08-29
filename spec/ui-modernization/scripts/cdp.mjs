// Minimal Chrome DevTools Protocol client. No dependencies — Node 22 ships WebSocket.
// Exists because the alternative was inferring layout from CSS, and CSS review does not
// catch overflow. The gates need a number from a real engine.

import { spawn } from 'node:child_process';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';

export async function withChrome(port, fn) {
  const profile = mkdtempSync(join(tmpdir(), 'k2-cdp-'));
  const proc = spawn(CHROME, [
    '--headless=new', '--disable-gpu', '--no-sandbox', '--hide-scrollbars',
    '--no-first-run', '--no-default-browser-check',
    `--user-data-dir=${profile}`,
    `--remote-debugging-port=${port}`,
    'about:blank',
  ], { stdio: 'ignore' });

  try {
    await waitForPort(port);
    return await fn();
  } finally {
    // Chrome keeps writing to the profile for a moment after SIGTERM, so removing it
    // immediately loses a race and throws ENOTEMPTY over an otherwise-passing run.
    // Wait for the exit, and never let temp-file cleanup fail the measurement.
    const exited = new Promise(r => proc.once('exit', r));
    proc.kill();
    await Promise.race([exited, new Promise(r => setTimeout(r, 3000))]);
    try { rmSync(profile, { recursive: true, force: true, maxRetries: 5, retryDelay: 200 }); }
    catch { /* leftover temp dir is not a test result */ }
  }
}

async function waitForPort(port, timeoutMs = 20000) {
  const deadline = Date.now() + timeoutMs;
  for (;;) {
    try {
      const r = await fetch(`http://127.0.0.1:${port}/json/version`);
      if (r.ok) return;
    } catch { /* not up yet */ }
    if (Date.now() > deadline) throw new Error('chrome did not open a debugging port');
    await new Promise(r => setTimeout(r, 150));
  }
}

// Opens a tab, runs the callback with a send() bound to it, then closes the tab.
export async function withTab(port, url, fn) {
  const res = await fetch(`http://127.0.0.1:${port}/json/new?${encodeURIComponent(url)}`,
    { method: 'PUT' });
  const target = await res.json();
  const ws = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((ok, bad) => { ws.onopen = ok; ws.onerror = () => bad(new Error('ws failed')); });

  let id = 0;
  const pending = new Map();
  const events = new Map();
  ws.onmessage = (m) => {
    const msg = JSON.parse(m.data);
    if (msg.id && pending.has(msg.id)) {
      const { ok, bad } = pending.get(msg.id);
      pending.delete(msg.id);
      msg.error ? bad(new Error(msg.error.message)) : ok(msg.result);
    } else if (msg.method && events.has(msg.method)) {
      events.get(msg.method)();
      events.delete(msg.method);
    }
  };
  const send = (method, params = {}) => new Promise((ok, bad) => {
    const n = ++id;
    pending.set(n, { ok, bad });
    ws.send(JSON.stringify({ id: n, method, params }));
  });
  const once = (method) => new Promise(ok => events.set(method, ok));

  try {
    return await fn({ send, once });
  } finally {
    ws.close();
    await fetch(`http://127.0.0.1:${port}/json/close/${target.id}`).catch(() => {});
  }
}

// Navigate at a fixed viewport width and settle. Returns when the page has painted.
export async function load({ send, once }, url, width, height = 900) {
  await send('Page.enable');
  await send('Emulation.setDeviceMetricsOverride',
    { width, height, deviceScaleFactor: 2, mobile: width < 700 });
  const loaded = once('Page.loadEventFired');
  await send('Page.navigate', { url });
  await loaded;
  // Webfonts and the Basecoat stylesheet arrive over the network on first run.
  await new Promise(r => setTimeout(r, 1200));
}
