# K2 Skills

A discoverable, machine-readable registry of every capability K2 exposes.

Each skill is one self-contained capability:
- A unique name (kebab-case)
- A one-line description
- An invoke route (where users / agents fire it)
- Inputs / outputs / dependencies (so consumers can wire to it)
- A surface (sidebar / jot / task / cron / api)
- A maintainer + version + status

The full registry is published as `_manifest.json` for other agents to consume.

## Layout

```
skills/
  README.md              ← this file
  _schema.md             ← frontmatter contract every SKILL.md follows
  _manifest.json         ← aggregated machine-readable registry
  capture/               ← create new items into K2 (jots, tasks, notes)
  triage/                ← decide what to do with what's already in K2
  action/                ← act on K2 contents (route to agents, file Jira, etc.)
  observe/               ← see what K2 is doing (workers, ledgers, dashboards)
  maintain/              ← keep K2 healthy (auto-fixer, memory sweep, etc.)
```

## Phases

Skills land in three waves:

1. **K2 dashboard skills** (this batch) — capabilities that live in `index.html`
   (~25 skills).
2. **Cron skills** — every cron job in OpenClaw becomes a skill consumable by
   other agents (Tim 1:1 prep, K2 Inbox AM, K2 Inline Mention Router, etc.).
3. **Discord agent skills** — the Copilot agents in Viking channels and the
   K2 advisor lane become skills.

## Public manifest URL

```
https://raw.githubusercontent.com/RyanSandoval/k2-dashboard/main/skills/_manifest.json
```

Cron jobs and Discord agents fetch this URL to discover what K2 can do and
how to invoke each capability.

## Adding / updating a skill

1. Drop a new `<name>.md` file in the right category directory.
2. Make sure the frontmatter matches `_schema.md`.
3. Add the entry to `_manifest.json` (manual until we wire the build script).
4. Bump version when behavior changes.

## Catalog

The dashboard renders the catalog at the `🧩 Skills` sidebar entry. The page
fetches `_manifest.json` at load time and groups skills by category.
