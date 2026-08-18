// api/_lib/gh.js
// THE ONLY module in this repo that references api.github.com (REQ-020,
// constitution #3). Route handlers call the exports below; they never
// construct a GitHub URL themselves.
//
// Path allowlist (REQ-015, design.md "Path allowlist") is deny-by-default:
//   READ    data.json (own route, see getDataFile) · cron-snapshot.json ·
//           MEMORY.md · memory/<name>.md
//   WRITE   images/notes/<name> · attachments/notes/<name>
// `data.json` is deliberately never in the WRITE list — it is not writable
// through /api/file, only through the rebase-aware /api/data route.
//
// Reads fall back to `GET /repos/{repo}/git/blobs/{sha}` whenever the
// contents API returns an empty `content` field (files >1MB — this is the
// bug fixed in c2d34e3, now enforced here so no client can get it wrong
// again). REQ-014 / constitution #6.

const API_BASE = 'https://api.github.com';
const REPO = 'RyanSandoval/k2-data';

const READ_LITERALS = new Set(['data.json', 'cron-snapshot.json', 'MEMORY.md']);
const READ_PREFIXES = ['memory/'];
const WRITE_PREFIXES = ['images/notes/', 'attachments/notes/'];

const MIME_TYPES = {
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.gif': 'image/gif',
  '.webp': 'image/webp',
  '.svg': 'image/svg+xml',
  '.pdf': 'application/pdf',
  '.md': 'text/markdown; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.txt': 'text/plain; charset=utf-8',
};

function hasUnsafeChars(path) {
  if (typeof path !== 'string' || path.length === 0) return true;
  if (path.includes('..')) return true;
  if (path.startsWith('/')) return true;
  if (path.includes('\\')) return true;
  if (path.includes('\0')) return true;
  return false;
}

// A prefix match is only valid if what follows the prefix is a single path
// segment (no further '/'), e.g. "memory/a.md" matches "memory/" but
// "memory/a/b.md" does not (design.md: "<name> must not contain /").
function matchesSingleSegmentPrefix(path, prefix) {
  if (!path.startsWith(prefix)) return false;
  const rest = path.slice(prefix.length);
  return rest.length > 0 && !rest.includes('/');
}

/**
 * Deny-by-default path validator. Throws on any disallowed path; returns
 * true when the path + mode pair is allowed. mode is 'read' or 'write'.
 */
export function assertAllowed(path, mode) {
  if (hasUnsafeChars(path)) {
    throw new Error('path not allowed');
  }

  if (mode === 'read') {
    if (READ_LITERALS.has(path)) return true;
    for (const prefix of READ_PREFIXES) {
      if (matchesSingleSegmentPrefix(path, prefix)) return true;
    }
    throw new Error('path not allowed');
  }

  if (mode === 'write') {
    for (const prefix of WRITE_PREFIXES) {
      if (matchesSingleSegmentPrefix(path, prefix)) return true;
    }
    throw new Error('path not allowed');
  }

  throw new Error('invalid mode');
}

function githubToken() {
  const token = process.env.GH_TOKEN;
  if (!token) throw new Error('server misconfigured: GH_TOKEN missing');
  return token;
}

async function githubFetch(path, options = {}) {
  return fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      Authorization: `Bearer ${githubToken()}`,
      Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      'User-Agent': 'k2-dashboard-vercel',
      ...(options.headers || {}),
    },
  });
}

function encodeRepoPath(path) {
  return path.split('/').map(encodeURIComponent).join('/');
}

function guessContentType(path) {
  const idx = path.lastIndexOf('.');
  const ext = idx === -1 ? '' : path.slice(idx).toLowerCase();
  return MIME_TYPES[ext] || 'application/octet-stream';
}

function githubError(message, status, body) {
  const err = new Error(message);
  err.status = status;
  if (body !== undefined) err.body = body;
  return err;
}

// Fetch the contents-API entry for a repo path (sha, possibly-empty
// base64 content, size, ...). Never logs or echoes the token.
async function fetchContentsEntry(path) {
  const res = await githubFetch(`/repos/${REPO}/contents/${encodeRepoPath(path)}`);
  if (res.status === 404) throw githubError('not found', 404);
  if (!res.ok) throw githubError('github request failed', res.status);
  return res.json();
}

// Resolve an entry's bytes, transparently falling back to the blobs API
// when the contents API returned content:"" (>1MB files). REQ-014.
async function resolveContentBuffer(entry) {
  if (typeof entry.content === 'string' && entry.content.length > 0) {
    return Buffer.from(entry.content, 'base64');
  }
  const blobRes = await githubFetch(`/repos/${REPO}/git/blobs/${entry.sha}`);
  if (!blobRes.ok) throw githubError('github blob request failed', blobRes.status);
  const blob = await blobRes.json();
  return Buffer.from(blob.content, blob.encoding === 'base64' ? 'base64' : 'utf8');
}

/**
 * Fetch an allowlisted text file by path. Returns { sha, content } where
 * content is a decoded utf-8 string. Falls back to the blobs API on empty
 * inline content (REQ-014). Caller is responsible for path validation via
 * assertAllowed(path, 'read') — route handlers do this before calling in.
 */
export async function getJson(path) {
  const entry = await fetchContentsEntry(path);
  const buf = await resolveContentBuffer(entry);
  return { sha: entry.sha, content: buf.toString('utf8') };
}

/**
 * Fetch raw bytes for a path (used for binary/blob reads, e.g. uploaded
 * images). Returns { sha, buffer, contentType }. Same blobs fallback as
 * getJson. Caller validates the path before calling in.
 */
export async function getRaw(path) {
  const entry = await fetchContentsEntry(path);
  const buf = await resolveContentBuffer(entry);
  return { sha: entry.sha, buffer: buf, contentType: guessContentType(path) };
}

/**
 * Write an allowlisted file. `content` must already be base64 (matches the
 * /api/file PUT contract). Enforces the write allowlist itself as a
 * defense-in-depth backstop — data.json can never reach this function
 * successfully since it is not in WRITE_PREFIXES.
 */
export async function putFile(path, { content, message, sha } = {}) {
  assertAllowed(path, 'write');
  const res = await githubFetch(`/repos/${REPO}/contents/${encodeRepoPath(path)}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message: message || `chore: update ${path} via k2-dashboard`,
      content,
      ...(sha ? { sha } : {}),
    }),
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw githubError('github write failed', res.status, body);
  return { sha: body.content && body.content.sha, url: body.content && body.content.html_url };
}

/**
 * Fetch data.json specifically (own dedicated route/handling, not part of
 * the general path allowlist). Falls back to blobs API — data.json is
 * 1,056,797 bytes today, already past the 1MB inline limit, so this path
 * is exercised on every read. Returns { sha, data } with data JSON-parsed.
 */
export async function getDataFile() {
  const entry = await fetchContentsEntry('data.json');
  const buf = await resolveContentBuffer(entry);
  const data = JSON.parse(buf.toString('utf8'));
  return { sha: entry.sha, data };
}

/**
 * Write data.json. Passes the caller's sha straight through to GitHub so
 * 409 (stale sha) / 422 (validation) surface verbatim to the caller for the
 * client's existing rebase-and-retry loop (REQ-016).
 */
export async function putDataFile({ data, sha, message } = {}) {
  // 2-space indent deliberately matches what the ~15 cron writers emit. Compacting
  // here would make the browser and the crons rewrite each other's whitespace on
  // every alternating write — more git churn, not less. Compaction is TASK-040,
  // and it has to land in all writers at once.
  const content = Buffer.from(JSON.stringify(data, null, 2), 'utf8').toString('base64');
  const res = await githubFetch(`/repos/${REPO}/contents/data.json`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message: message || 'chore: update data.json via k2-dashboard',
      content,
      sha,
    }),
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw githubError('github write failed', res.status, body);
  return { sha: body.content && body.content.sha };
}
