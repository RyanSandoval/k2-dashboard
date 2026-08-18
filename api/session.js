// api/session.js — GET -> {ok:true} or 401. Used on page load to decide
// login-screen vs app.

import { requireSession } from './_lib/auth.js';

export default async function handler(req, res) {
  if (req.method !== 'GET') {
    res.status(405).json({ error: 'method not allowed' });
    return;
  }
  if (!requireSession(req, res)) return;
  res.status(200).json({ ok: true });
}
