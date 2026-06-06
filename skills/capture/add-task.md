---
name: add-task
title: Add Task (NL-parsed)
desc: Create a task with priority / due date / project parsed from natural language. Supports `>agent` suffix to route to an agent.
category: capture
version: 1.1.0
status: active
maintainer: K2

surface:
  - page:tasks (top input)
  - sidebar:new-task

trigger:
  - manual

inputs:
  - rawText: free-form task text. Supports:
      "do thing #project @context !high tomorrow >jira"
  - urgency / importance UI dropdowns

outputs:
  - DATA.tasks: new entry {id, text, urgency, importance, project, owner, done, dueDate, created, messages}
  - DATA.k2Inline (only if >agent suffix detected): pending request to fire the agent

code:
  - file: index.html
    symbol: addTask
  - file: index.html
    symbol: _extractAgentFromText
  - file: index.html
    symbol: parseNaturalLanguageTask

dependencies:
  - skill:route-to-discord-agent (when >agent is present)

invoke:
  type: data-mutation
  target: DATA.tasks
  example: |
    User types "Fix destination map sort bug >jira" + Enter.

    addTask() detects >jira via _extractAgentFromText:
      - strips ">jira" from saved task text
      - stamps task with k2Intent + k2Status="pending"
      - queues to DATA.k2Inline {source: "task", sourceTaskId, explicitRoute: "jira"}

    The router (every 3 min) picks it up, files the Jira ticket via the
    Fire Button Poller, then maybe_complete_source_task() flips the task
    to done with k2Result attached.

    Task row shows yellow ⏳ chip while pending, green ✓ chip once filed.
---

# Add Task (NL-parsed)

The primary way to enter tasks. Plain text in, structured task out.

## Natural language parsing

| Token | Effect |
|---|---|
| `#projectName` | sets task.project |
| `@context` | sets task.context |
| `!high` / `!med` / `!low` | sets urgency tier |
| `tomorrow` / `monday` / `2026-12-15` | sets dueDate |
| `>agent` | routes to K2 inline mention router on save |

All tokens are stripped from the saved task text.

## `>agent` lifecycle (the new pattern)

When task text contains `>agent`:

1. `_extractAgentFromText(rawText)` finds the match, validates against
   `K2_AGENTS`, and strips the token.
2. Task is created with:
   - `k2Intent: { agent, label, route, icon }`
   - `k2Status: "pending"`
   - `k2QueuedAt: <ISO>`
3. `DATA.k2Inline` gets a pending request:
   - `source: "task"`
   - `sourceTaskId: <task.id>`
   - `paragraph: <task text>`
   - `explicitRoute: <route>`
4. Router cron fires (≤3 min), executes the action.
5. `maybe_complete_source_task` (in router.py) closes the task:
   - `done: true`
   - `completedAt: <ISO>`
   - `k2Status: "done"`
   - `k2Result: { intent, marker, resolvedAt }`

UI: task row shows yellow `⏳ K2 working` chip while pending; green
`✓ done` once resolved.

## How to invoke as an agent

Push a new task directly to DATA.tasks (skip the NL parsing path):

```
POST k2-data/data.json
  - append to data.tasks: {
      id: <ms timestamp>,
      text: "<plain instruction>",
      urgency: 2, importance: 2,
      project: "<project-id or ''>",
      owner: "ryan",
      done: false,
      created: "<YYYY-MM-DD>",
      messages: []
    }
```

To also fire an agent action on it, queue a parallel DATA.k2Inline entry:

```
data.k2Inline.push({
  id, source: "task", sourceTaskId: <task.id>,
  paragraph: <task.text>,
  explicitRoute: "jira" | "task" | "note" | "dashboard-feedback" | "classify",
  status: "pending", createdAt
})
```

## Related skills

- [[inline-agent-picker]] — same `>agent` UX for jots
- [[task-mention-k2]] — explains the auto-close behavior
- [[smart-recurrence]] — triggers on task.done = true if cadence hint present
