# Phase 1 — Scope the GitHub token down

**Why:** the dashboard currently authenticates with a classic PAT carrying full `repo`
scope (verified 2026-08-17: `x-oauth-scopes: gist, read:org, repo`). That is write access to
*every* repo on the account. The dashboard needs exactly one thing: read/write contents of
`RyanSandoval/k2-data`.

**This step cannot be automated.** GitHub exposes no API for creating personal access
tokens — it is a deliberate restriction. Everything below is a ~60-second manual step.

## 1. Mint the token

<https://github.com/settings/personal-access-tokens/new>

- **Token name:** `k2-dashboard-vercel`
- **Expiration:** 90 days (calendar a rotation)
- **Resource owner:** RyanSandoval
- **Repository access:** *Only select repositories* → **k2-data**
- **Permissions → Repository permissions → Contents:** **Read and write**
- Leave every other permission at *No access*. Metadata: Read-only is added automatically
  and is fine.
- Generate, copy the `github_pat_...` value.

## 2. Verify the scope is actually narrow

Paste the token as `$T` and run both. The first MUST fail, the second MUST succeed.

    T=github_pat_xxx
    curl -s -o /dev/null -w "dashboard(expect 403/404): %{http_code}\n" \
      -H "Authorization: Bearer $T" https://api.github.com/repos/RyanSandoval/k2-dashboard
    curl -s -o /dev/null -w "k2-data(expect 200): %{http_code}\n" \
      -H "Authorization: Bearer $T" https://api.github.com/repos/RyanSandoval/k2-data

If the first returns 200, the token is still too broad — recheck "Only select repositories".

## 3. Install it on Vercel

    cd ~/k2-dashboard
    vercel env rm GH_TOKEN production --yes 2>/dev/null
    printf '%s' "$T" | vercel env add GH_TOKEN production
    vercel --prod

## 4. Revoke the old one

Once the deployed dashboard loads and saves cleanly on the new token, delete the old
classic PAT at <https://github.com/settings/tokens>. Until it is revoked, the blast radius
is unchanged — a token that still exists is still a live credential.

Note: `~/.openclaw/workspace/.gh_token` holds that same broad classic token and is used by
other local automation, so revoking it will break those. Check what depends on it first;
minting a *separate* narrow token for the dashboard (above) does not disturb them.
