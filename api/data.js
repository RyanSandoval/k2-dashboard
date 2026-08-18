// api/data.js — GET {sha,data} · PUT {data,sha,message?} -> {sha} · 409 on
// stale sha (REQ-013, REQ-016). The rebase-and-retry loop stays in the
// client (design.md "Save concurrency") — this route just passes sha
// straight to GitHub and surfaces 409/422 verbatim so the client's retry
// still fires.

import { requireSession } from './_lib/auth.js';
import { getDataFile, putDataFile } from './_lib/gh.js';

export default async function handler(req, res) {
  if (!requireSession(req, res)) return;

  if (req.method === 'GET') {
    try {
      const { sha, data } = await getDataFile();
      res.status(200).json({ sha, data });
    } catch (err) {
      const status = err && err.status === 404 ? 404 : 502;
      res.status(status).json({ error: status === 404 ? 'not found' : 'upstream error' });
    }
    return;
  }

  if (req.method === 'PUT') {
    const body = req.body || {};
    if (body.data === undefined || typeof body.sha !== 'string') {
      res.status(400).json({ error: 'data and sha required' });
      return;
    }
    try {
      const result = await putDataFile({ data: body.data, sha: body.sha, message: body.message });
      res.status(200).json(result);
    } catch (err) {
      if (err && (err.status === 409 || err.status === 422)) {
        res.status(err.status).json({ error: err.status === 409 ? 'conflict' : 'validation failed' });
        return;
      }
      res.status(502).json({ error: 'upstream error' });
    }
    return;
  }

  res.status(405).json({ error: 'method not allowed' });
}
