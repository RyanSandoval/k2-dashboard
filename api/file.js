// api/file.js — GET ?path= -> {sha,content} (utf-8 text) · 404 if absent.
// PUT ?path= + {content,message?,sha?} -> {sha,url} · content is base64.
// Path allowlist (REQ-015): GET checks the READ set, PUT checks the WRITE
// set — data.json is in READ but never in WRITE, so it can never be
// written through this route (constitution #4, design.md hard rule).

import { requireSession } from './_lib/auth.js';
import { assertAllowed, getJson, putFile } from './_lib/gh.js';

function getPath(req) {
  const raw = req.query && req.query.path;
  return typeof raw === 'string' ? raw : '';
}

export default async function handler(req, res) {
  if (!requireSession(req, res)) return;

  const path = getPath(req);

  if (req.method === 'GET') {
    try {
      assertAllowed(path, 'read');
    } catch {
      res.status(400).json({ error: 'invalid path' });
      return;
    }
    try {
      const { sha, content } = await getJson(path);
      res.status(200).json({ sha, content });
    } catch (err) {
      const status = err && err.status === 404 ? 404 : 502;
      res.status(status).json({ error: status === 404 ? 'not found' : 'upstream error' });
    }
    return;
  }

  if (req.method === 'PUT') {
    try {
      assertAllowed(path, 'write');
    } catch {
      res.status(400).json({ error: 'invalid path' });
      return;
    }
    const body = req.body || {};
    if (typeof body.content !== 'string') {
      res.status(400).json({ error: 'content required' });
      return;
    }
    try {
      const result = await putFile(path, { content: body.content, message: body.message, sha: body.sha });
      res.status(200).json(result);
    } catch (err) {
      if (err && (err.status === 409 || err.status === 422)) {
        res.status(err.status).json({ error: err.status === 409 ? 'conflict' : 'validation failed' });
        return;
      }
      const status = err && err.status === 404 ? 404 : 502;
      res.status(status).json({ error: status === 404 ? 'not found' : 'upstream error' });
    }
    return;
  }

  res.status(405).json({ error: 'method not allowed' });
}
