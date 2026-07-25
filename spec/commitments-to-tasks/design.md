# Design — Commitments-to-Tasks

**Version:** 1.0
**Activated:** 2026-07-25
**Status:** active
**Implements:** requirements.md (REQ-001 … REQ-010)

Reference implementation to copy from: **session-log-gap-detector** (`spec/session-log-gap-detector/`) and the **Action Inbox** scanner cron (`a6125141`) + `renderActionInbox` in `index.html`. This feature is that pattern with a different source (Goldfish+Pieces recall, not transcripts) and a different sink (real tasks, not a gaps store).

---

## 1. Architecture summary

Two parts, mirroring Action Inbox / gap-detector:

1. **Scanner** (new cron + prompt, Sonnet, weekly) — pulls recall, extracts+enriches commitments, dedupes against `DATA.tasks`, writes the merged `tasks` slice via `scripts/k2_data_set.py`.
2. **Dashboard view** (`index.html`) — a "Commitments" card that reads `DATA.tasks`, filters `source === "commitment"`, groups by `initiative`, and renders with the normal checkoff. No detection in the browser.

Commitments ARE tasks — not a parallel store. The only new persisted state besides task rows is `DATA.commitmentsMeta` (`lastScanAt`, run stats).

---

## 2. Data flow

```
weekly cron (Sonnet, Sunday AM, non-blackout)
  → window = trailing 7 days
  → RECALL PULL (bounded — never dump full activity, REQ-009):
      Goldfish: search_memory on commitment cues → targeted get_snapshots (limit≤4) for email/Jira bodies
      Pieces:   ask_pieces_ltm(question="commitments this week", modalities incl. audio)
  → EXTRACT + ENRICH (Sonnet):
      per commitment → {initiative, commitment, who, specifics, when, nextAction,
                        confidence, sourceLayer, evidence(scrubbed), unanchored?}
      confidence: email/screen=high, summary=medium, voice-only=medium/low (REQ-005)
      unanchored (no who/what) → flagged, NOT written as a task (REQ-002)
  → DEDUPE against live DATA.tasks by commitmentKey (REQ-004):
      exists + done       → leave as-is (respect manual completion)
      exists + not done   → update commitment fields, keep id/created/done
      new                 → append task {id:Date.now()+i, done:false, source:"commitment", ...}
  → write merged tasks slice + commitmentsMeta via k2_data_set.py (REQ-007)
dashboard
  → renderCommitments() reads DATA.tasks.filter(t=>t.source==="commitment")
      groups by initiative, sorts by confidence; normal checkoff toggles done + saveData()
```

---

## 3. Data model

Commitment-tasks extend the existing Task schema (SCHEMA.md) with optional fields — a plain task still validates.

```json
{
  "id": 1785000000000,           // number, Date.now()-based (existing convention)
  "text": "string",              // = the commitment, human-readable (existing field, drives main list)
  "priority": "high|medium|low", // mapped from confidence/urgency
  "done": false,                 // existing — checkoff
  "created": "YYYY-MM-DD",       // existing
  "project": "string?",          // existing — optional project.id link if initiative maps to one

  "source": "commitment",        // set for taxonomy consistency (source already used: jot/plan-sync/...)
  "commitmentKey": "string",     // NEW — stable dedupe key (see §4) AND the card's discriminator
                                 //   (filter = tasks with a truthy commitmentKey; 0 collisions on live data)
  "initiative": "string",        // NEW — grouping (e.g. "Tactical Web (demo prep)")
  "who": "string",               // NEW — who's waiting
  "specifics": "string",         // NEW — ticket #s / email subject / thread
  "nextAction": "string",        // NEW — the concrete next step
  "confidence": "high|medium|low",// NEW — drives color
  "sourceLayer": "goldfish|pieces-voice|pieces-summary", // NEW — provenance
  "evidence": "string",          // NEW — short SCRUBBED quote/subject (no secrets, REQ-010)
  "firstSeen": "YYYY-MM-DD",     // NEW — when scan first captured it
  "lastSeen": "YYYY-MM-DD"       // NEW — last scan that still saw it
}
```

`DATA.commitmentsMeta`: `{ "lastScanAt": "ISO-8601", "lastRun": {"scanned":N,"new":N,"updated":N,"unanchored":N} }`

**Why on the task, not a side store:** REQ-003 wants them in the real task list and checkoffable. Extra keys are optional and ignored by existing task render; the Commitments card is a filtered view of the same rows. One source of truth, one checkoff.

---

## 4. Dedupe — `commitmentKey` (REQ-004)

Stable, content-derived, initiative-scoped. Mirrors gap-detector's `hash(sourceRoot+sessionId+normalizedTitle)`.

```
commitmentKey = sha1( normalize(initiative) + "|" + primaryAnchor )
  primaryAnchor = first of: ticket#(s)  ||  email-subject  ||  normalize(commitment text)
  normalize = lowercase, strip punctuation, collapse whitespace, drop stopwords
```

- Prefer a **ticket # or email subject** as the anchor so paraphrase drift between weeks (voice transcription varies) still maps to the same key.
- On each run: build key → look up in `DATA.tasks`. Match ⇒ update-or-skip per §2. No match ⇒ new task.
- `[TO VERIFY]` (TASK-001): confirm no existing task already uses `commitmentKey`/`source` keys so we don't collide.

---

## 5. Components

### 5.1 Scanner (new — NOT in index.html)
Location: `k2-dashboard/scripts/` alongside the Action Inbox / gap scanner. Form: a cron `agentTurn` (Sonnet) whose prompt does the recall pull + enrichment + dedupe, shelling `k2_data_set.py` for the write — matching how `a6125141` is built. `[TO VERIFY]` TASK-001 confirms the action-inbox scanner's exact form (agentTurn vs script+CLI) and copies it.

Guardrails baked into the prompt: bounded recall (REQ-009), no secrets persisted (REQ-010), unanchored→flagged-not-written (REQ-002), Sonnet only (REQ-008).

### 5.2 Writer
`scripts/k2_data_set.py --set tasks=/tmp/commit-tasks.json --set commitmentsMeta=/tmp/commit-meta.json --message "Commitments sync <ts>"`. The scanner computes the FULL new `tasks` array (existing tasks + merged commitment-tasks) into the temp file — the writer's ARRAY gate (≤50% shrink) protects against accidental truncation. `[TO VERIFY]` TASK-002: confirm passing the whole tasks array (not just commitment rows) is correct, since k2_data_set replaces the named key wholesale.

### 5.3 Dashboard card (`index.html`)
`renderCommitments()` — filtered view of `DATA.tasks`. Copy structure from `renderActionInbox`. Group by `initiative`; within group sort confidence high→low. Row: checkbox (normal task toggle) · commitment `text` · `who` · `nextAction` · confidence dot · source badge. Empty state: "No open commitments captured this week." Reuse existing `saveData()` + task toggle handler — no new persistence path.

---

## 6. Cron / scheduling
- Weekly, Sunday ~09:00 PT (post sleep-wake bounce, non-blackout). See [[feedback-cron-blackout-windows]], [[feedback-cron-sleep-wake-window]].
- Sonnet; `lightContext:false` (needs recall MCP tools + deferred-tool loading). See [[feedback-lightcontext-strips-deferred-tools]].
- Idempotent: safe to re-run same week (dedupe guarantees it).
- Create via `openclaw cron` CLI, not the MCP cron tool. See [[feedback-mcp-cron-tool-injects-toolsallow]].

## 7. Failure modes
- Recall MCP down (Goldfish/Pieces disabled/disconnected) → scan logs "no recall source", writes nothing, no partial. 
- Overflow payload → caught by bounded-limit design; if a snapshot still overflows, skip that snapshot, note it, continue.
- Writer gate trip → no write, non-zero exit, alert; never a partial data.json.
- Pieces disabled (default state per [[feedback-recall-layer-routing]]) → **DECIDED 2026-07-25: the weekly scan auto-enables Pieces for its run.** Sequence: `openclaw mcp configure pieces --enable && openclaw mcp reload` → do the recall pull (Goldfish + Pieces voice) → `openclaw mcp configure pieces --disable && openclaw mcp reload` in a finally/always step so Pieces returns to its dormant default even if the scan errors. This is the one sanctioned auto-enable of Pieces (overrides the "only on explicit ask" rule for this cron only). If the enable step fails, degrade to Goldfish-only and note voice coverage was off.
