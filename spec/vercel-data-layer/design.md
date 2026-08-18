# Design — k2-dashboard Vercel Data Layer
Version: 1.0 · 2026-08-17

## Shape

    BEFORE   browser ──[PAT, repo scope, localStorage]──> api.github.com
    AFTER    browser ──[signed session cookie]──> /api/* (Vercel) ──[PAT, env var]──> api.github.com

Same origin, so no CORS anywhere. The dashboard stays one static `index.html`; Vercel
serves it alongside `api/*.js` functions. GitHub Pages on `main` is untouched — all work
lands on `feat/vercel-data-layer`, deployed as its own Vercel project. Cutover is a
human decision, not part of this build.

## API contract (frozen — both build agents code against this)

Every response is JSON unless stated. Every `/api/*` route except `login` requires a valid
session cookie and returns `401 {"error":"unauthorized"}` without one.

| Route | Method | Request | 200 response |
|---|---|---|---|
| `/api/login` | POST | `{code}` | `{ok:true}` + `Set-Cookie: k2s=...` |
| `/api/logout` | POST | — | `{ok:true}` + cookie cleared |
| `/api/session` | GET | — | `{ok:true}` or 401 |
| `/api/data` | GET | — | `{sha, data}` |
| `/api/data` | PUT | `{data, sha, message?}` | `{sha}` · 409 on stale sha |
| `/api/file` | GET | `?path=` | `{sha, content}` (utf-8 text) · 404 if absent |
| `/api/file` | PUT | `?path=` + `{content, message?, sha?}` | `{sha, url}` · `content` is base64 |
| `/api/blob` | GET | `?path=` | raw bytes, upstream `Content-Type` |

`GET /api/data` and `GET /api/file` both fall back to `GET /git/blobs/{sha}` when the
contents API returns `content: ""` (files >1MB). This is the bug fixed in `c2d34e3`,
now enforced server-side so no client can get it wrong again.

## Path allowlist (REQ-015)

Enforced in `api/_lib/gh.js`, applied to `/api/file` and `/api/blob`:

    READ    data.json · cron-snapshot.json · MEMORY.md · memory/<name>.md
    WRITE   images/notes/<name> · attachments/notes/<name>

Rules: reject any path containing `..`, a leading `/`, a backslash, or a NUL; match against
explicit literals and single-segment prefixes only (`<name>` must not contain `/`).
`data.json` is deliberately **not** writable through `/api/file` — it has its own route
with rebase semantics.

## Auth

`POST /api/login` compares `{code}` against `env.ACCESS_CODE` in constant time
(`crypto.timingSafeEqual` on equal-length SHA-256 digests, so length never leaks). On
match it sets:

    k2s=<exp>.<hmac_sha256(exp, env.SESSION_SECRET)>
    HttpOnly; Secure; SameSite=Strict; Path=/; Max-Age=2592000   (30 days)

Verification recomputes the HMAC with `timingSafeEqual` and rejects a past `exp`. No
session store — the cookie is self-contained; rotating `SESSION_SECRET` invalidates every
session at once. Login is rate-limited to 10 attempts / 10 min per IP via an in-memory map
(best-effort: Vercel functions are per-instance, so this slows scripted guessing rather
than preventing it — the real strength is a 32-char random `ACCESS_CODE`).

## Save concurrency (REQ-016)

The existing rebase-and-retry loop stays **in the client**, unchanged in logic — it just
calls `/api/data` instead of `api.github.com`. Keeping it there is the minimum diff and
preserves the `SERVER_OWNED_KEYS` merge that stops browser saves from clobbering cron
writes. `PUT /api/data` passes the caller's `sha` straight to GitHub and surfaces 409/422
verbatim so the client's existing retry logic still fires.

## Files

    api/_lib/auth.js     sign/verify session cookie, requireSession() guard
    api/_lib/gh.js       ONLY module that knows api.github.com (REQ-020)
                         getJson(path) · putJson(path,...) · getRaw(path) · assertAllowed(path,mode)
    api/login.js  api/logout.js  api/session.js
    api/data.js   api/file.js    api/blob.js
    vercel.json          static index.html + node functions, security headers
    .env.example         names only, no values

Client (`index.html`) changes, all inside the existing helpers — no call sites move:
`ghGetJsonFile` → `/api/data` | `/api/file`; `saveData` PUT → `/api/data`;
`loadCronSnapshot` → `/api/file?path=cron-snapshot.json`; `uploadPastedImage` /
`uploadFileToRepo` → `/api/file` PUT; `_fetchPrivateImage` → `/api/blob`; memory readers →
`/api/file`. `ghHeaders()` and `GH_TOKEN` are deleted. The login screen posts to
`/api/login`; the `ACCESS_HASH` constant and the token input are removed. All `fetch`
calls to `/api/*` pass `credentials: 'same-origin'`.

## Env vars (Vercel project settings)

    GH_TOKEN         fine-grained PAT, k2-data contents:rw    (REQ-001)
    ACCESS_CODE      32-char random login code
    SESSION_SECRET   32-byte random hex, HMAC key

## Phase 3 — why this stops here

Swapping git-as-datastore for Postgres/KV is a change behind `gh.js` alone (REQ-020), but
it is **not** just that module: `k2-data` is written by ~15 cron jobs, 7 of them Python
scripts committing via git (`jot_task_promoter.py`, `commitment_sync.py`,
`summarize_notes.py`, `scan_dated_reminders.py`, `k2-data-guardian*.sh`, plus the hardened
writer `scripts/k2_data_set.py`). Until those write through the same interface, a DB and
the repo would diverge silently. Migration order: (1) this API layer, (2) point the Python
writers at it, (3) only then swap the store. Doing (3) first is how you lose data.

Sizing context for (3): 1,056,797 bytes today — tasks 331KB / vikingInsights 198KB /
projects 114KB / dailyDocs 78KB / stale `cronJobs` 47KB. Whitespace alone is 220KB (21%).
The `k2-data` repo is 127MB of git history for a 1MB payload.
