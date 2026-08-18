# Tasks — k2-dashboard Vercel Data Layer
Version: 1.0 · 2026-08-17

Branch: `feat/vercel-data-layer`. Never commit to `main` (REQ-017).

## Phase 1 — Token scope
- [ ] TASK-001 [REQ-001] Document the exact click-path to mint a fine-grained PAT
      (k2-data only, contents rw) + the `vercel env` command to install it.
      Output: `spec/vercel-data-layer/PHASE1-TOKEN.md` · Verify: user can follow it blind.
      NOTE: GitHub has no PAT-creation API — this task ends in a manual step.

## Phase 2 — Server-side data layer (AGENT A: backend)
- [ ] TASK-010 [REQ-012] `api/_lib/auth.js` — `signSession(ttl)`, `verifySession(cookieHeader)`,
      `requireSession(req,res)` returning bool + writing 401. HMAC-SHA256 over `exp`, node
      `crypto` only, `timingSafeEqual` for both HMAC and code compare.
      Verify: tampered/expired/absent cookie all fail; valid passes.
- [ ] TASK-011 [REQ-015,REQ-020] `api/_lib/gh.js` — the ONLY module referencing
      api.github.com. Exports `assertAllowed(path,mode)`, `getJson(path)`, `getRaw(path)`,
      `putFile(path,{content,message,sha})`, `getDataFile()`, `putDataFile(...)`.
      `getJson`/`getDataFile` MUST fall back to `/git/blobs/{sha}` on empty content (REQ-014).
      Verify: `assertAllowed('../x','read')` throws; `assertAllowed('memory/a/b.md','read')` throws.
- [ ] TASK-012 [REQ-011] `api/login.js` (POST, rate-limited), `api/logout.js`, `api/session.js`.
      Verify: wrong code 401, right code sets HttpOnly cookie, `/api/session` then 200.
- [ ] TASK-013 [REQ-013,REQ-016] `api/data.js` — GET `{sha,data}`; PUT `{data,sha}` passing
      sha through and surfacing 409/422 verbatim.
      Verify: GET returns 908 tasks; PUT with a bogus sha yields 409, not 500.
- [ ] TASK-014 [REQ-013,REQ-015] `api/file.js` (GET/PUT) + `api/blob.js` (GET raw).
      Verify: allowlisted read 200; `?path=../../x` 400; write to `data.json` 400.
- [ ] TASK-015 `vercel.json` — static `index.html`, node runtime for `api/**`, and headers:
      `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`,
      `Referrer-Policy: strict-origin-when-cross-origin`. Plus `.env.example` (names only).
      Verify: `npx vercel build` succeeds locally.

## Phase 2 — Client (AGENT B: frontend, `index.html` only)
- [ ] TASK-020 [REQ-010] Delete `GH_TOKEN`, `ghHeaders()`, and every `api.github.com` /
      `raw.githubusercontent.com` fetch. Repoint per design.md "Files".
      Verify: `grep -c "api.github.com\|GH_TOKEN\|ghHeaders" index.html` → 0.
- [ ] TASK-021 [REQ-011] Replace the login screen: remove `ACCESS_HASH` + `sha256()` gate +
      token input; POST `{code}` to `/api/login`; on load call `/api/session` to decide
      login-screen vs app. Keep `clearToken()` behaviour as a logout that POSTs `/api/logout`.
      Verify: `grep -c ACCESS_HASH index.html` → 0.
- [ ] TASK-022 [REQ-013] Every `/api/*` fetch passes `credentials:'same-origin'`; a 401 from
      any endpoint shows the login screen instead of failing silently.
      Verify: all 8 script blocks pass `node --check`.

## Phase 2 — Verify (K2/Opus, not delegated)
- [ ] TASK-030 Deploy branch to a new Vercel project, set the 3 env vars.
- [ ] TASK-031 Playwright: login with the real code, assert 908 tasks / 59 projects /
      21 notes / 14 decisions, zero console errors.
- [ ] TASK-032 Assert no token leak — scan every response body + `localStorage` +
      `sessionStorage` for the PAT (REQ-010).
- [ ] TASK-033 Assert the gate holds — `/api/data` with no cookie → 401; forged cookie → 401.
- [ ] TASK-034 Round-trip a save and confirm the commit lands in k2-data.

## Phase 3 — Deferred (spec only, do NOT build)
- [ ] TASK-040 [REQ-021] Point the 7 Python writers at `/api/data`.
- [ ] TASK-041 Drop the stale `cronJobs` key from data.json (47KB, owned by the sidecar since #105).
- [ ] TASK-042 Compact JSON whitespace (220KB) — only after TASK-040, or writers thrash.
- [ ] TASK-043 Sidecar `vikingInsights` (198KB, 6 UI refs).
- [ ] TASK-044 [REQ-030] Replace corsproxy.io with an allowlisted `/api/proxy`.
