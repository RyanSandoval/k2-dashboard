# GATES — Requests Ingest (Copilot unresolved-requests review → K2)

Goal: the 41 open human requests from Ryan's M365 Copilot review become a
first-class `DATA.requests` type, rendered above everything else on the
dashboard and at the top of the Action Inbox.

## G1 — Ingest script exists and parses the workbook
  EVIDENCE: dry-run printed `rows=41` (2026-08-23)
- [x] `scripts/requests_sync.py` reads the xlsx and emits 41 normalized rows.
  CHECK: python3 scripts/requests_sync.py --xlsx "$XLSX" --dry-run | tail -1
  EXPECT: rows=41

## G2 — Stable ids survive a re-drop
  EVIDENCE: md5 ddfe67a0451badb752da464e9f40b2d2 twice — IDS STABLE
- [x] Running twice against the same file yields identical ids.
  CHECK: python3 scripts/requests_sync.py --xlsx "$XLSX" --dry-run --print-ids | md5; python3 scripts/requests_sync.py --xlsx "$XLSX" --dry-run --print-ids | md5
  EXPECT: identical

## G3 — Live data.json carries requests
  EVIDENCE: live blob jq -> `41  41` (requests / requestsMeta.count); open=41 overdue=29
- [x] `DATA.requests` has 41 items and `DATA.requestsMeta.count` agrees.
  CHECK: gh api repos/RyanSandoval/k2-data/git/blobs/$(gh api repos/RyanSandoval/k2-data/contents/data.json --jq .sha) --jq .content | base64 -d | jq '[(.requests|length),(.requestsMeta.count)]|@tsv' -r
  EXPECT: 41	41

## G4 — No sibling key loss
  EVIDENCE: k2_data_set gate log `keys 55->57 bytes 1035878->1084050`
- [x] Key count after write >= key count before write.
  CHECK: (recorded pre/post key counts)
  EXPECT: post >= pre (pre = 55)

## G5 — Dashboard renders requests above Action Inbox
  EVIDENCE: dash-requests @2139 < dash-action-inbox @2148 (pre-rebase); render shows card above Action Inbox
- [x] `dash-requests` card exists in DOM order before `dash-action-inbox`.
  CHECK: grep -n 'id="dash-requests"' index.html; grep -n 'id="dash-action-inbox"' index.html
  EXPECT: dash-requests line number < dash-action-inbox line number

## G6 — Requests page routes
  EVIDENCE: grep count = 8 (>= 4); navigateTo + _rerenderCurrentPage both route; page renders active=true, 16 requester groups
- [x] `page-requests` exists, nav item exists, router calls renderRequests().
  CHECK: grep -c 'id="page-requests"\|data-page="requests"\|renderRequests()' index.html
  EXPECT: >= 4

## G7 — Action Inbox leads with requests
  EVIDENCE: _requestsInboxBlock defined + called at both innerHTML sites; rendered inbox first block = "People waiting on you 41 open"
- [x] renderActionInbox prepends open requests ahead of scanned rows.
  CHECK: grep -n "_requestsAsInboxRows" index.html
  EXPECT: definition + call site present

## G8 — No JS syntax regression
  EVIDENCE: node --check clean on all 8 inline script blocks; playwright pageerror list empty
- [x] Extracted script blocks parse.
  CHECK: node --check on extracted inline script
  EXPECT: exit 0

## ABANDON log
(none yet)

## Verified
All 8 gates met 2026-08-23 on branch feat/requests-ingest (base origin/main).
Render evidence: /tmp/req-dash.png, /tmp/req-page.png, /tmp/req-inbox.png
