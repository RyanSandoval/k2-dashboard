# K2 Skill schema

Every SKILL.md follows this YAML frontmatter contract:

```yaml
---
# REQUIRED
name: action-inbox               # globally unique, kebab-case
title: Action Inbox              # human-readable
desc: One-sentence summary of what this skill does.
category: triage                 # capture | triage | action | observe | maintain
version: 1.0.0                   # semver; bump on behavior change
status: active                   # active | beta | deprecated | disabled
maintainer: K2                   # who owns this (K2, Ryan, agent name)

# OPTIONAL — leave out fields that don't apply

# Where the skill is invoked from
surface:
  - sidebar:Action-Inbox         # left nav entry slug
  - mobile-drawer:Action-Inbox   # mobile more-drawer entry
  - jot:agent-mention            # accessible via >agent picker
  - cron:scheduled               # fires automatically on a schedule
  - api:manifest                 # exposed for external agent consumption

# What triggers the skill to act
trigger:
  - manual                       # user clicks
  - cron:K2-Action-Inbox-Scanner
  - event:task-completed

# Inputs the skill consumes
inputs:
  - DATA.tasks                   # k2-data fields it reads
  - DATA.jots
  - DATA.notes

# Outputs the skill produces
outputs:
  - DATA.actionInbox             # k2-data fields it writes
  - ui:sidebar-badge             # UI surfaces it updates

# Code refs for humans following the trail
code:
  - file: index.html
    symbol: renderActionInbox
  - file: index.html
    symbol: actionInboxHandled

# Other skills / crons this skill depends on
dependencies:
  - cron:K2-Action-Inbox-Scanner (a6125141)

# How a remote agent invokes this skill (machine-readable)
invoke:
  type: data-mutation            # data-mutation | trigger-cron | post-message | render-ui
  target: DATA.actionInbox       # what to mutate / call
  example: |
    Add a row with {source, sourceId, summary} to DATA.actionInbox
    in k2-data/data.json then PUT via GitHub API.
---
```

## Status values

- **active** — fully wired, safe for agents to invoke
- **beta** — works but may change without notice
- **deprecated** — being phased out; do not build on
- **disabled** — code exists but is turned off; do not invoke

## Versioning

Bump `version` on:
- New required input / output → MAJOR
- New optional input / output → MINOR
- Bug fix or doc-only change → PATCH

Agents consuming the manifest should pin to MAJOR.
