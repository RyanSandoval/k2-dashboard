// api/blob.js — GET ?path= -> raw bytes, upstream Content-Type.
//
// Used for reading back binary assets (e.g. uploaded images) as well as
// any allowlisted text file as raw bytes. The path allowlist in gh.js has
// two disjoint lists — a READ set (documents) and a WRITE set (upload
// targets like images/notes/<name>). Since uploaded images only ever land
// in the WRITE set, this route accepts a path allowed under EITHER list:
// try the READ allowlist first, then the WRITE allowlist, and only 400 if
// neither matches. This keeps assertAllowed's per-list semantics exactly
// as specified while still letting the client read back what it uploaded.

import { requireSession } from './_lib/auth.js';
import { assertAllowed, getRaw } from './_lib/gh.js';

function getPath(req) {
  const raw = req.query && req.query.path;
  return typeof raw === 'string' ? raw : '';
}

function isPathAllowedForBlobRead(path) {
  try {
    assertAllowed(path, 'read');
    return true;
  } catch {
    // fall through
  }
  try {
    assertAllowed(path, 'write');
    return true;
  } catch {
    return false;
  }
}

export default async function handler(req, res) {
  if (req.method !== 'GET') {
    res.status(405).json({ error: 'method not allowed' });
    return;
  }
  if (!requireSession(req, res)) return;

  const path = getPath(req);
  if (!isPathAllowedForBlobRead(path)) {
    res.status(400).json({ error: 'invalid path' });
    return;
  }

  try {
    const { buffer, contentType } = await getRaw(path);
    res.setHeader('Content-Type', contentType);
    res.status(200).send(buffer);
  } catch (err) {
    const status = err && err.status === 404 ? 404 : 502;
    res.status(status).json({ error: status === 404 ? 'not found' : 'upstream error' });
  }
}
