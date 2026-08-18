# Constitution — k2-dashboard Vercel Data Layer
Version: 1.0 · 2026-08-17

1. **`main` is untouchable.** GitHub Pages must keep serving a working dashboard for the
   entire build. All work lands on `feat/vercel-data-layer` (REQ-017).
2. **The token never reaches the browser.** No endpoint, error message, log line, or debug
   path may echo `GH_TOKEN`. If a feature seems to need it client-side, the design is wrong.
3. **`api/_lib/gh.js` is the only module that knows GitHub exists.** Route handlers call it;
   they never construct a GitHub URL. This is what makes Phase 3 possible.
4. **Deny by default on paths.** A path not explicitly allowlisted is rejected. New paths are
   added to the allowlist in a reviewed change, never by loosening the matcher.
5. **Never weaken save concurrency.** The rebase + `SERVER_OWNED_KEYS` merge exists because
   ~15 crons write the same file. A save that can clobber cron data is a data-loss bug.
6. **Reads must survive >1MB.** Any new read path handles the blobs fallback. This already
   broke production once (2026-08-17).
7. **No data migration in this project.** Provisioning a DB or moving data out of git is
   Phase 3 and requires the cron writers to move first.
