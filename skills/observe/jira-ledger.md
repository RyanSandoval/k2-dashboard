---
name: jira-ledger
title: Jira Ledger
desc: Index of every Jira ticket K2 has filed. Source of truth for "has K2 already filed this?" dedupe.
category: observe
version: 1.0.0
status: active
maintainer: K2

surface:
  - sidebar:Jira-Ledger
  - mobile-drawer:Jira-Ledger

trigger:
  - manual
  - written-by: cron:K2-Jira-Fire-Button-Poller (appends on filed)

inputs:
  - DATA.jiraLedger — [{jiraKey, title, noteId?, sourceText, createdAt, project, requestId}]

outputs:
  - ui:#jira-ledger-list

code:
  - file: index.html
    symbol: renderJiraLedger

dependencies:
  - skill:file-viking-jira
  - cron:K2-Jira-Fire-Button-Poller (4b4ae123)

invoke:
  type: data-read
  target: DATA.jiraLedger
---

# Jira Ledger

The historical record of every MW-XXX ticket K2 has filed. Used for dedupe
and for showing "Filed as MW-XXX" links on Workers cards.

## When entries land

The Fire Button Poller cron appends after a successful Jira filing:

```js
{
  jiraKey: "MW-12345",
  title: "<request title>",
  noteId: "<source note id or null>",
  sourceText: "<truncated description>",
  createdAt: "<ISO>",
  project: "MW",
  requestId: "<request.id>"
}
```

## Pre-fire dedupe

Before queuing a new Jira request, check the ledger:

```js
const dupe = DATA.jiraLedger.find(e =>
  e.title === proposedTitle ||
  (e.sourceText && proposedDesc.includes(e.sourceText.slice(0, 60)))
);
if (dupe) showToast(`Already filed as ${dupe.jiraKey}`);
```

The K2 Inline Mention Router does NOT do this dedupe yet — it's on the
backlog. Currently each fire creates a new ticket.

## How to invoke as an agent

```
GET https://raw.githubusercontent.com/RyanSandoval/k2-data/main/data.json
# read data.jiraLedger
```

Useful for cron jobs that want to avoid double-filing.

## Related skills

- [[file-viking-jira]] — what writes to this ledger
- [[workers]] — surfaces ledger entries in the recently-done section
