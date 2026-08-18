// api/login.js — POST {code} -> {ok:true} + Set-Cookie, or 401.
// Rate-limited to 10 attempts / 10 min per IP via an in-memory map. This is
// best-effort (Vercel functions are per-instance, see design.md "Auth") —
// the real strength is a long random ACCESS_CODE.

import { verifyAccessCode, signSession } from './_lib/auth.js';

const WINDOW_MS = 10 * 60 * 1000;
const MAX_ATTEMPTS = 10;
const attempts = new Map(); // ip -> timestamps[]

function clientIp(req) {
  const fwd = req.headers['x-forwarded-for'];
  if (typeof fwd === 'string' && fwd.length > 0) return fwd.split(',')[0].trim();
  return (req.socket && req.socket.remoteAddress) || 'unknown';
}

function isRateLimited(ip) {
  const now = Date.now();
  const recent = (attempts.get(ip) || []).filter((t) => now - t < WINDOW_MS);
  attempts.set(ip, recent);
  return recent.length >= MAX_ATTEMPTS;
}

function recordAttempt(ip) {
  const list = attempts.get(ip) || [];
  list.push(Date.now());
  attempts.set(ip, list);
}

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    res.status(405).json({ error: 'method not allowed' });
    return;
  }

  const ip = clientIp(req);
  if (isRateLimited(ip)) {
    res.status(429).json({ error: 'too many attempts' });
    return;
  }
  recordAttempt(ip);

  const code = req.body && req.body.code;

  let ok;
  try {
    ok = verifyAccessCode(code);
  } catch {
    res.status(500).json({ error: 'server misconfigured' });
    return;
  }

  if (!ok) {
    res.status(401).json({ error: 'unauthorized' });
    return;
  }

  res.setHeader('Set-Cookie', signSession());
  res.status(200).json({ ok: true });
}
