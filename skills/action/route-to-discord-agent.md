---
name: route-to-discord-agent
title: K2 Inline Mention Router
desc: Reads DATA.k2Inline pending requests, classifies via Haiku (or honors explicit route), dispatches to jira / task / note / dashboard-feedback.
category: action
version: 1.2.0
status: active
maintainer: K2

surface:
  - cron:K2-Inline-Mention-Router (665abd82)

trigger:
  - cron:every-3min-PT-6am-11pm
  - DATA.k2Inline: any entry with status="pending"

inputs:
  - DATA.k2Inline: pending requests {id, source, sourceDate, paragraph, explicitRoute?, explicitAgent?}
  - K2_AGENTS catalog (for explicit picks)
  - Haiku LLM (for implicit picks via >k2)

outputs:
  - DATA.jiraRequests: appended when intent = jira
  - DATA.tasks: appended when intent = task or dashboard-feedback
  - DATA.notes: appended when intent = note
  - DATA.dailyDocs[date].content: marker text replaced with result chip
  - DATA.k2Inline[i].status: flipped pending → done with resolvedAt

code:
  - file: k2-inline-router/router.py
    symbol: main
  - file: k2-inline-router/router.py
    symbol: classify
  - file: k2-inline-router/router.py
    symbol: process_recurrence_queue

dependencies:
  - claude CLI (Haiku model)
  - GitHub PAT for k2-data read/write
  - cron:K2-Jira-Fire-Button-Poller (downstream for jira lane)
  - cron:K2-Inline-Mention-Router (this cron itself)

invoke:
  type: data-mutation
  target: DATA.k2Inline (append pending item)
  example: |
    Any agent that wants to fire a K2 action posts to DATA.k2Inline:
      {
        "id": "k2-xxxx",
        "source": "agent:my-agent-name",
        "paragraph": "fix the destination map sort order",
        "explicitRoute": "jira",   # optional; omit to let Haiku classify
        "status": "pending",
        "createdAt": "<ISO>"
      }
    Within 3 minutes the router classifies/dispatches and updates status.

vikingOnly: false
---

# K2 Inline Mention Router

The dispatch layer between user/agent intent and the actual K2 action.

## Pipeline

```
DATA.k2Inline (pending)
  ↓
classify() — Haiku for implicit, attrs for explicit
  ↓
ROUTES[intent](data, item, summary)
  ├─ jira  → DATA.jiraRequests       → cron Fire Button Poller → #viking-jira → Copilot files MW-XXX
  ├─ task  → DATA.tasks
  ├─ note  → DATA.notes
  └─ dashboard-feedback → DATA.tasks (project=proj-k2-dashboard, status=idea)
  ↓
maybe_complete_source_task() — if source=task, close the source task
  ↓
update_jot_marker() — swap 「K2:reqId:routing…」 for result chip text
```

## Viking gating (CRITICAL)

The router enforces the rule "Viking work must use github-copilot agents":

- Classifier outputs `vikingContext: true|false`
- If `intent == "jira"` AND `vikingContext == false`, intent is **downgraded
  to `task`** before routing. Prevents non-Viking work from polluting
  #viking-jira (and from hitting the wrong agent backend).
- See [[feedback-viking-routing-backend]] memory rule.

## Cost

- Idle fire (no pending requests): script exits before any LLM call. $0.
- Active fire (1+ pending requests, all batched): one Haiku call
  classifying everything at once. ~$0.02 per fire when there's work.
- Daily cost ceiling: ~$0.20 worst case (10 active fires per day).

## Status handling for source = task

When a source task fires (user typed `>jira` in task text):
- After successful route, `maybe_complete_source_task()`:
  - sets `task.done = true`
  - sets `task.completedAt = <ISO>`
  - sets `task.k2Status = "done"`
  - sets `task.k2Result = { intent, marker, resolvedAt }`
- Task disappears from open list, appears in completed with green chip
  showing what K2 did with it.

## How to invoke as an agent

Append a request to `DATA.k2Inline` in k2-data/data.json via the GitHub API.
See `example` in the invoke field above. The router picks it up within 3
minutes (or 5 if outside 6 AM–11 PM PT) and processes it.

## Related skills

- [[inline-agent-picker]] — the UI that creates pending requests from jots
- [[task-mention-k2]] — task-side equivalent
- [[file-viking-jira]] — what jira-lane dispatches actually do
- [[smart-recurrence]] — same cron also handles the recurrence queue
