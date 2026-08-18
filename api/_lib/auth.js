// api/_lib/auth.js
// Session cookie sign/verify + access-code check. Node stdlib crypto only.
//
//   k2s=<exp>.<hmac_sha256(exp, SESSION_SECRET)>
//   HttpOnly; Secure; SameSite=Strict; Path=/; Max-Age=<seconds>
//
// No session store: the cookie is self-contained. Rotating SESSION_SECRET
// invalidates every session at once. See design.md "Auth".

import crypto from 'node:crypto';

const COOKIE_NAME = 'k2s';
const DEFAULT_TTL_MS = 30 * 24 * 60 * 60 * 1000; // 30 days

function sessionSecret() {
  const secret = process.env.SESSION_SECRET;
  if (!secret) throw new Error('server misconfigured: SESSION_SECRET missing');
  return secret;
}

function hmacHex(exp) {
  return crypto.createHmac('sha256', sessionSecret()).update(String(exp)).digest('hex');
}

// Constant-time string compare. Buffers of unequal length would throw in
// timingSafeEqual, so we short-circuit — but only after doing a same-length
// dummy compare, so the false branch takes the same shape of work either way.
function timingSafeEqualStr(a, b) {
  const bufA = Buffer.from(a, 'utf8');
  const bufB = Buffer.from(b, 'utf8');
  if (bufA.length !== bufB.length) {
    crypto.timingSafeEqual(bufA, bufA);
    return false;
  }
  return crypto.timingSafeEqual(bufA, bufB);
}

function parseCookies(cookieHeader) {
  const out = {};
  if (!cookieHeader || typeof cookieHeader !== 'string') return out;
  for (const part of cookieHeader.split(';')) {
    const idx = part.indexOf('=');
    if (idx === -1) continue;
    const key = part.slice(0, idx).trim();
    const value = part.slice(idx + 1).trim();
    if (key) out[key] = value;
  }
  return out;
}

/** Build the Set-Cookie header value for a fresh session. */
export function signSession(ttlMs = DEFAULT_TTL_MS) {
  const exp = Date.now() + ttlMs;
  const sig = hmacHex(exp);
  const maxAgeSec = Math.max(0, Math.floor(ttlMs / 1000));
  return `${COOKIE_NAME}=${exp}.${sig}; HttpOnly; Secure; SameSite=Strict; Path=/; Max-Age=${maxAgeSec}`;
}

/** Set-Cookie header value that clears the session. */
export function clearSessionCookie() {
  return `${COOKIE_NAME}=; HttpOnly; Secure; SameSite=Strict; Path=/; Max-Age=0`;
}

/**
 * Verify a `Cookie` request header. Returns true only for a well-formed,
 * correctly-signed, unexpired session cookie.
 */
export function verifySession(cookieHeader) {
  try {
    const cookies = parseCookies(cookieHeader);
    const raw = cookies[COOKIE_NAME];
    if (!raw) return false;

    const dotIdx = raw.indexOf('.');
    if (dotIdx === -1) return false;

    const exp = raw.slice(0, dotIdx);
    const sig = raw.slice(dotIdx + 1);
    if (!/^\d+$/.test(exp) || sig.length === 0) return false;

    const expected = hmacHex(exp);
    if (!timingSafeEqualStr(sig, expected)) return false;

    if (Number(exp) <= Date.now()) return false;

    return true;
  } catch {
    return false;
  }
}

/**
 * Guard for route handlers. Returns true if the request carries a valid
 * session; otherwise writes 401 {"error":"unauthorized"} and returns false.
 */
export function requireSession(req, res) {
  if (verifySession(req.headers && req.headers.cookie)) return true;
  res.status(401).json({ error: 'unauthorized' });
  return false;
}

/**
 * Constant-time access-code compare (REQ login). Both sides are hashed to
 * fixed-length SHA-256 digests first so string length never leaks timing.
 */
export function verifyAccessCode(candidate) {
  const expected = process.env.ACCESS_CODE;
  if (!expected) throw new Error('server misconfigured: ACCESS_CODE missing');
  const candidateHash = crypto.createHash('sha256').update(String(candidate ?? ''), 'utf8').digest();
  const expectedHash = crypto.createHash('sha256').update(expected, 'utf8').digest();
  return crypto.timingSafeEqual(candidateHash, expectedHash);
}
