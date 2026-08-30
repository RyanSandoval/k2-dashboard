// Opens index.html with real k2-data and hands back a Playwright page.
//
// This replaces a 96-line hand-rolled CDP client I wrote before checking whether a
// browser driver was already on this machine. One is: review-runner has Playwright,
// and `channel: 'chrome'` drives the installed Chrome so nothing has to be downloaded.
//
// ponytail: resolved through review-runner's node_modules via NODE_PATH, because
// k2-dashboard is deliberately dependency-free and one verification harness does not
// justify giving it a package.json. If that repo moves, add playwright here instead.

import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { createServer } from 'node:http';
import { extname, join, normalize } from 'node:path';

const require = createRequire(import.meta.url);
const NODE_MODULES = '/Users/ryansandoval/mkt-ai-lab/review-runner/node_modules';

let chromium;
try {
  ({ chromium } = require(`${NODE_MODULES}/playwright`));
} catch {
  console.error(`playwright not found at ${NODE_MODULES}\n` +
    'Install it there, or `npm i -D playwright` in k2-dashboard and import it directly.');
  process.exit(2);
}

const ROOT = '/Users/ryansandoval/k2-dashboard';

// Served over HTTP, not file://. Chrome refuses to run <script type="module"> from
// a file:// origin, so the Tiptap block never executed and window._todayEditor was
// never defined — the editor, the single most important thing in this app, was
// absent from every check written before this one.
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript',
                '.css': 'text/css', '.json': 'application/json', '.svg': 'image/svg+xml',
                '.png': 'image/png' };
async function serve() {
  const server = createServer((req, res) => {
    const rel = normalize(decodeURIComponent(req.url.split('?')[0])).replace(/^(\.\.[/\\])+/, '');
    const file = join(ROOT, rel === '/' ? 'index.html' : rel);
    try {
      res.writeHead(200, { 'Content-Type': TYPES[extname(file)] || 'application/octet-stream' });
      res.end(readFileSync(file));
    } catch { res.writeHead(404); res.end('not found'); }
  });
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  return { server, url: `http://127.0.0.1:${server.address().port}/index.html` };
}

export const APP = 'served at runtime';
export const DATA_FILE = '/Users/ryansandoval/k2-data/data.json';

// DATA is a `let` binding, not a window property. The app mirrors it onto window.DATA
// and keeps that in sync, but assigning window.DATA from outside only moves the mirror
// while every function keeps reading the binding — which silently empties the app and
// makes a working page look broken. Assign both.
const seed = (data) => `
  DATA = ${JSON.stringify(data)};
  window.DATA = DATA;
  document.getElementById('login-screen').style.display = 'none';
  document.getElementById('app-main').style.display = 'flex';
`;

export async function withApp(fn, { width = 390, height = 900, seedData = true } = {}) {
  const { server, url } = await serve();
  const browser = await chromium.launch({ headless: true, channel: 'chrome' });
  try {
    const page = await browser.newPage({ viewport: { width, height }, deviceScaleFactor: 2 });
    await page.goto(url, { waitUntil: 'load' });
    if (seedData) await page.evaluate(seed(JSON.parse(readFileSync(DATA_FILE, 'utf8'))));
    return await fn(page);
  } finally {
    await browser.close();
    await new Promise(r => server.close(r));
  }
}

// Every suite ends the same way: print the object, fail on any false.
export function report(out, okLabel) {
  console.log(JSON.stringify(out, null, 2));
  const bad = Object.entries(out).filter(([, v]) => typeof v === 'boolean' && v !== true);
  if (bad.length) { console.log('FAIL:', bad.map(([k]) => k).join(', ')); process.exit(1); }
  console.log(okLabel);
}
