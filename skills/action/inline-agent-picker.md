---
name: inline-agent-picker
title: Inline >agent Picker
desc: Type `>jira`, `>k2`, `>task`, `>note`, `>dashboard` in a jot to open a popover picker. Picking inserts an AgentMention chip that fires on save.
category: action
version: 1.2.0
status: active
maintainer: K2

surface:
  - jot:trigger-> mid-paragraph
  - task:trigger->-suffix
  - mobile:tiptap-trigger

trigger:
  - manual

inputs:
  - text: TipTap editor text containing pattern /(^|\s)>([a-zA-Z][a-zA-Z-]+)/
  - K2_AGENTS: window.K2_AGENTS catalog (id, label, route, icon)

outputs:
  - AgentMention node: inserted into TipTap doc with unique reqId
  - DATA.k2Inline: pending request appended on save (via detectAgentMentions)

code:
  - file: index.html
    symbol: AgentMention
  - file: index.html
    symbol: detectAgentMentions
  - file: index.html
    symbol: handleEditorUpdate (agentMatch branch)
  - file: index.html
    symbol: selectSuggestion (agent type branch)

dependencies:
  - skill:route-to-discord-agent
  - K2_AGENTS catalog

invoke:
  type: render-ui
  target: "#suggestion-dropdown"
  example: |
    User types ">jir" in a jot. The popover lists agents matching "jir"
    (just viking-jira). User hits Enter or clicks → AgentMention chip
    inserted with a unique reqId. On next save, detectAgentMentions
    appends to DATA.k2Inline:
      {
        id, source: "jot", sourceDate, paragraph,
        explicitAgent: "viking-jira",
        explicitRoute: "jira",
        chipReqId, status: "pending"
      }
---

# Inline >agent Picker

The primary "tell K2 what to do" interface inside jots. Lets you compose your
intent in plain English, then end the line with a `>` plus an agent slug to
route it.

## Agents available

| Slug | Lane | Behavior |
|---|---|---|
| `>viking-jira` | `jira` | File a Viking Jira ticket via Fire Button Poller. Viking-only. |
| `>k2` | `classify` | Let K2 (Haiku) classify the intent and pick the right lane. |
| `>task` | `task` | Save as a regular personal task. |
| `>note` | `note` | Save as a reference note. |
| `>dashboard` | `dashboard-feedback` | Queue as a K2 dashboard improvement idea. |

## How the chip fires

1. Picker inserts an `AgentMention` Tiptap node with a unique `reqId` attr
   (data-req-id="a-xxxxxx").
2. On editor save, `detectAgentMentions` walks the JSON tree, finds each
   AgentMention node, and uses `reqId` as its dedupe key — meaning a single
   chip can only fire once for its lifetime, regardless of how much text
   the user types around it.
3. The container `<p>` / `<li>` / `<heading>` of the chip is the only text
   queued (NOT the parent block) — so a chip in one bullet of a list does
   not sweep in the other bullets.
4. The request lands in `DATA.k2Inline` with `source: "jot"`,
   `explicitRoute: <route>`, and a status of `pending`.

## Re-firing

Once a chip has fired, deleting the chip and picking again creates a new
chip with a new `reqId`. The old one stays in the queuedAgentMentionIds list
on the daily doc to prevent zombie re-fires.

## Why `>` not `@`

`@` is already burned for project mentions in jots. `>` only triggers the
picker when followed by a letter (`>jira`, not `> ` with a space) so it does
NOT collide with TipTap's blockquote shortcut.

## Related skills

- [[route-to-discord-agent]] — what processes the chip after save
- [[task-mention-k2]] — same pattern but for tasks (chip in task text)
- [[file-viking-jira]] — what `>jira` ultimately calls
