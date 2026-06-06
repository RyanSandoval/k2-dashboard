---
name: action-inbox
title: Action Inbox
desc: Unified surface for action-implying items across tasks, jots, notes. LLM-scanned nightly, hybrid priority sort, pin/demote.
category: triage
version: 1.3.0
status: active
maintainer: K2

surface:
  - sidebar:Action-Inbox
  - mobile-bottom-nav:Action
  - mobile-drawer:Action-Inbox

trigger:
  - manual
  - cron:K2-Action-Inbox-Scanner (a6125141) — nightly 2 AM PT
  - cron:K2-Action-Inbox-Rerank-Poller (e30a6ae1) — every 5 min, M–Sa work hours

inputs:
  - DATA.tasks (open, not completed)
  - DATA.jots (last 30 days)
  - DATA.notes (last 30 days)

outputs:
  - DATA.actionInbox — array of items {id, source, sourceId, summary, jiraKey, priorityScore, pinned, demoted, handled, dismissed, firstSeenAt, lastSeenAt}
  - DATA.actionInboxMeta — {lastScanAt, rerankRequested}
  - ui: sidebar badge with pending count

code:
  - file: index.html
    symbol: renderActionInbox
  - file: index.html
    symbol: actionInboxHandled
  - file: index.html
    symbol: actionInboxDismiss
  - file: index.html
    symbol: actionInboxPin
  - file: index.html
    symbol: actionInboxDemote
  - file: index.html
    symbol: actionInboxRequestRerank

dependencies:
  - cron:K2-Action-Inbox-Scanner
  - cron:K2-Action-Inbox-Rerank-Poller
  - claude CLI (Haiku, for priority scoring)

invoke:
  type: data-read
  target: DATA.actionInbox
---

# Action Inbox

The pinned-in-sidebar "what needs attention" surface. Replaces the
"check 4 different lists" workflow.

## Item lifecycle

```
Scanner cron runs (nightly 2 AM)
  ↓
Walks open tasks + recent jots + recent notes for action implication
  ↓
LLM scores priority (0–100) per item
  ↓
Writes to DATA.actionInbox, merging with existing handled/dismissed state
  ↓
Dashboard renders sorted by:  pinned ↓  →  priorityScore DESC  →  demoted last
```

## Per-row actions

| Button | Effect |
|---|---|
| ☆ → ⭐ | Pin to top. Survives 14-day auto-archive. |
| ⬇ | Demote to bottom (out of sight but not gone) |
| ✓ | Mark handled. Stays in Handled tab with ↩ restore. |
| ✕ | Dismiss. Stays in Dismissed tab with ↩ restore. |
| (click row) | Jump to source: task modal, note editor, or jot at exact day |

## Filters

- **Open** (default) — unhandled, undismissed items
- **Handled** — completed items
- **Dismissed** — explicitly skipped items
- **All** — everything tracked

## Re-rank flow

User taps **🔄 Re-rank now** → writes `rerankRequested` flag to
`DATA.actionInboxMeta`. The Rerank Poller cron (every 5 min during work
hours) picks it up and re-runs the LLM scoring. Cap: tap → scores updated
= ~2–7 min.

## Auto-prune

- Done tasks auto-disappear from inbox the moment they're marked done
  in DATA.tasks (no scan needed — runtime filter).
- Items untouched for 14 days are dropped by the next scanner run.

## How to invoke as an agent

Read-only surface. Agents querying "what does Ryan have on his plate?" can
fetch:

```
GET https://raw.githubusercontent.com/RyanSandoval/k2-data/main/data.json
```

…then read `data.actionInbox` (filter `handled === false && dismissed === false`
sorted by `pinned`, then `priorityScore DESC`).

## Related skills

- [[stale-jots]] — sibling surface for old daily-doc lines
- [[daily-brief]] — today-specific subset (overdue + due today only)
- [[daily-advisor]] — opinionated picks (3 decisions for today)
