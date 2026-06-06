---
name: workers
title: Workers Tab
desc: Unified live view of K2 agent queues + recent results. Click any card to expand full action details + cancel buttons.
category: observe
version: 1.1.0
status: active
maintainer: K2

surface:
  - sidebar:Workers
  - mobile-drawer:Workers

trigger:
  - manual

inputs:
  - DATA.k2Inline — pending + recent inline mention requests
  - DATA.jiraRequests — pending + recent Jira fire button requests
  - DATA.recurrenceQueue — pending + recent recurrence judgments
  - DATA.jiraLedger — filed Jira tickets (last 24h)

outputs:
  - ui:#workers-content
  - ui:#workers-badge (pending count)

code:
  - file: index.html
    symbol: renderWorkers
  - file: index.html
    symbol: _workersCollect
  - file: index.html
    symbol: _workersCardDetailHtml
  - file: index.html
    symbol: workersCancelJiraRequest
  - file: index.html
    symbol: workersCancelInline
  - file: index.html
    symbol: workersOpenSourceJot

dependencies:
  - skill:route-to-discord-agent (produces DATA.k2Inline + DATA.jiraRequests)
  - skill:file-viking-jira (produces DATA.jiraLedger)
  - skill:smart-recurrence (produces DATA.recurrenceQueue)

invoke:
  type: render-ui
  target: "#workers-content"
---

# Workers Tab

The "what is K2 doing right now" surface. Answers the question "did my
action actually fire?" without having to dig through k2-data manually.

## Sections

1. **Overview pills** — pending count · done-in-24h count · per-lane breakdown
2. **⏳ In flight** — every pending queue item across all lanes
3. **✓ Recently done (24h)** — resolved items grouped by lane, with MW-XXX
   keys auto-linked to the Jira Ledger
4. **Lane legend** — explains the pipelines

## Lanes tracked

| Icon | Lane | Pipeline |
|---|---|---|
| 🤖 | `inline:*` | DATA.k2Inline → router cron (every 3 min) |
| 🎫 | `jira:#viking-jira` | DATA.jiraRequests → Fire Button Poller → Copilot → MW-XXX |
| 🔁 | `recurrence:judge` | DATA.recurrenceQueue → Haiku judge → clone task with next dueDate |

## Card expansion

Clicking any card reveals:

- Full text actually queued (NOT just the truncated title)
- Per-kind detail rows: source date, intent, viking context, summary,
  judgment, project, labels, Jira key, timestamps
- Action buttons depending on state:
  - **❌ Cancel** (pending only) — removes from queue, prevents fire
  - **📂 Open source jot** — jumps to the jot/note that triggered the work
  - **🎫 Open MW-XXX ↗** — opens the resulting Jira ticket once filed

## How to invoke as an agent

Workers is render-only. Agents that want to see K2's live state can:

```
GET https://raw.githubusercontent.com/RyanSandoval/k2-data/main/data.json
```

…then read `data.k2Inline`, `data.jiraRequests`, `data.recurrenceQueue`,
and `data.jiraLedger` directly. The Workers tab is just a UI rendering of
exactly that data.

## Related skills

- [[pipeline-trace]] — planned upgrade that links upstream inline items to
  their downstream Jira key
- [[jira-ledger]] — the ledger view referenced by 🎫 ↗ links
