# Requirements — k2-dashboard Vercel Data Layer
Version: 1.0 · Created: 2026-08-17 · Status: active

## Problem

`k2-dashboard` is a **public** repo served from GitHub Pages. Its login screen is a
SHA-256 hash compared client-side (`index.html:1899`) — not an auth boundary; it is
bypassed by writing `localStorage` directly (demonstrated 2026-08-17). Behind it sits a
GitHub PAT with full **`repo`** scope in browser `localStorage`, inside an 18,325-line
single-file app with 194 `innerHTML` sites that also pipes URLs through the third-party
`corsproxy.io` — including the user's Google Calendar ICS feed.

Any XSS or hostile browser extension yields write access to **every repo the user owns**.

Secondary: `data.json` reached 1,056,797 bytes and crossed GitHub's 1MB inline-content
limit, breaking all reads until commit `c2d34e3` routed them to the blobs API.

## Requirements

### Phase 1 — Token scope
- **REQ-001** The GitHub credential used by the dashboard shall be a fine-grained PAT
  scoped to `RyanSandoval/k2-data` only, with `contents: read+write` and nothing else.
  *AC:* `curl -H "Authorization: Bearer $T" https://api.github.com/repos/RyanSandoval/k2-dashboard`
  returns 403/404 while the same call against `k2-data` returns 200.
- **REQ-002** No requirement in this spec shall depend on `repo`, `gist`, or `read:org` scope.
  *AC:* every endpoint passes its test with the fine-grained token.

### Phase 2 — Server-side data layer
- **REQ-010** The GitHub credential shall never be transmitted to the browser.
  *AC:* full-text search of every network response and of `localStorage`/`sessionStorage`
  after a complete login + load + save cycle contains no substring of the token.
- **REQ-011** Access shall be granted by a server-verified session, not a client-side hash.
  *AC:* setting `localStorage` by hand grants nothing; `GET /api/data` without a valid
  session cookie returns 401.
- **REQ-012** The session cookie shall be `HttpOnly`, `Secure`, `SameSite=Strict`, signed
  with an HMAC secret held server-side, and shall expire.
  *AC:* `document.cookie` from page JS cannot read it; a tampered cookie returns 401.
- **REQ-013** All GitHub reads/writes the browser performs today shall be available through
  same-origin `/api/*` endpoints with identical observable behaviour.
  *AC:* dashboard loads 908 tasks / 59 projects / 21 notes / 14 decisions and a save
  round-trips, matching the pre-migration baseline.
- **REQ-014** Server reads shall transparently handle files >1MB via the blobs API.
  *AC:* `GET /api/data` returns complete `data.json` while it exceeds 1,048,576 bytes.
- **REQ-015** File endpoints shall accept only allowlisted paths; traversal and
  arbitrary-path access shall be rejected.
  *AC:* `GET /api/file?path=../../etc/passwd` and `?path=.github/workflows/x.yml` → 400.
- **REQ-016** Concurrent-write safety shall be preserved: a save rebases onto the current
  server copy and retries on conflict, so cron writes are not clobbered.
  *AC:* a PUT with a stale sha returns 409 and the client's retry succeeds.
- **REQ-017** The GitHub Pages deployment on `main` shall keep working, unchanged, until
  the user explicitly cuts over.
  *AC:* `main` is untouched; all work lands on `feat/vercel-data-layer`.

### Phase 3 — Storage abstraction (spec only, not built)
- **REQ-020** All GitHub access shall sit behind one module so the datastore can be
  swapped without touching route handlers or the client.
  *AC:* exactly one file imports the GitHub REST base URL.
- **REQ-021** The store-swap plan shall account for the ~15 cron writers that write
  `data.json` via git, which are **out of scope** for this phase.
  *AC:* `design.md` names them and states the migration order.

## Out of scope (this build)
- Provisioning Postgres/KV or migrating data out of git.
- Rewiring cron writers.
- Compacting `data.json` whitespace (needs all 7 Python writers aligned first — would
  otherwise cause whitespace-thrash commits between browser and cron writes).
- Replacing `corsproxy.io` (tracked as REQ-030, deferred).
- Cutting DNS / retiring GitHub Pages.

## Clarifications
### Session 2026-08-17
- Q: Interview? → A: Skipped — user gave explicit "implement, report when done" authority
  after a full architecture discussion in #k2-dashboard. Scope taken from that thread.
- Q: Cut over live dashboard tonight? → A: No. Build on a branch, deploy to Vercel,
  verify, user flips. Reversibility over speed.
- Q: Create the fine-grained PAT automatically? → A: Impossible — GitHub exposes no API
  for PAT creation. Phase 1 ends in a documented 60-second manual step.
