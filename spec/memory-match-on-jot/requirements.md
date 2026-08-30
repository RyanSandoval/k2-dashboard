🧠 memory-match-on-jot

# Requirements — K2 Memory Match on New Jot

**Version:** v0.1 (drafted 2026-06-21)
**Scope:** When Ryan types in today's daily jot editor, K2 computes keyword similarity against existing notes and past daily docs. If a strong enough match exists, a soft inline nudge appears below the editor: "You explored this on [date] — [title]." One tap jumps to the prior note. No backend, no LLM call — all client-side at match time.

**Why this exists:** Ryan re-derives conclusions he already captured in notes 2-3 months ago because searching requires intent; the nudge surfaces the link passively, at the moment of jotting.

**Out of scope (MVP):** MEMORY.md matching (file not accessible from browser — see OQ-1), multi-match list, fuzzy phonetic matching, previous-day jot editor (today only).

---

## Functional Requirements

### REQ-001 — Trigger on debounced jot edit
The match check **shall** run on `_createTodayEditor.onUpdate` for non-checkbox edits, debounced at 1500ms — the same cadence as `debouncedJotLinker`. It **shall not** run on checkbox toggles (the `isCheckboxToggle` flag gates it).

**Acceptance:** Typing in today's editor triggers a match check ~1.5s after the last keystroke. Checking a task checkbox does not trigger it.

### REQ-002 — Minimum text threshold
The match check **shall** skip (clear any visible nudge and return) when the plain-text content of today's jot is fewer than 25 characters after stripping HTML.

**Acceptance:** With "hello" in the editor, no nudge appears. With a 25+ char sentence, the check runs.

### REQ-003 — Match corpus: notes
The check **shall** compare the jot text against every entry in `DATA.notes` using the `_memMatchScore(jotTerms, candidateTerms)` function. Each candidate uses `(note.title || '') + ' ' + (note.text || '').replace(/<[^>]+>/g, '')` as its text. Archived notes (`note.archived === true`) **shall** be excluded.

**Acceptance:** A note titled "Planning flow redesign" matches a jot about "flow redesign ideas." An archived note is not returned even with identical text.

### REQ-004 — Match corpus: past daily docs
The check **shall** also compare against the plain-text content of `DATA.dailyDocs` entries for the 30 most recent dates excluding today. Each candidate's title is the date string (e.g., "Jun 15").

**Acceptance:** A jot about "SimpleFIN auth failure" matches a past daily doc that contains "SimpleFIN auth" from two weeks prior.

### REQ-005 — Scoring algorithm
**Revised 2026-08-30 on evidence — see "Deviations" below.** `_memMatchScore(setA, setB)` **shall** return the overlap coefficient of two pre-computed term sets: `|A ∩ B| / min(|A|, |B|)`, and **shall** return 0 when `|A ∩ B| < 3`. Terms are lowercase, stop-word filtered (a hardcoded ~50-word English stoplist), minimum 3 characters. Punctuation stripped before tokenizing.

**Acceptance:** `_memMatchScore({'redesign','flow','planning'}, {'planning','flow','ui'})` ≈ 0.5. `_memMatchScore({'hello'}, {'world'})` === 0.

### REQ-006 — Nudge threshold
**Revised 2026-08-30 to 0.40**, tracking the change of scale in REQ-005. A nudge **shall** appear only when the top-scoring candidate has score ≥ 0.40. If multiple candidates exceed the threshold, only the highest-scoring one is shown.

**Acceptance:** A score of 0.11 shows no nudge. A score of 0.12 shows the nudge. If two notes score 0.15 and 0.13, only the 0.15 match is shown.

### REQ-007 — Nudge UI — content
The nudge **shall** render in `#jot-match-nudge` (inserted once, immediately below `#daily-doc-today-editor`) and contain:
- An icon + label: "📎 Prior note match"
- The candidate's title or date
- A one-line text snippet (first 80 non-HTML chars of the candidate)
- A "Compare →" tap target that navigates to the match
- A dismiss "×" that hides the nudge until the next meaningful content change

**Acceptance:** The nudge shows title, snippet, and two interactive elements. On mobile and desktop.

### REQ-008 — Nudge UI — style
The nudge **shall** use a soft non-blocking style: `background: color-mix(in srgb, var(--accent) 10%, transparent)`, `border: 1px solid var(--accent-dim)`, `border-radius: var(--radius-sm)`, `font-size: 12px`. It **shall not** intercept pointer events on the editor above it.

**Acceptance:** Nudge is visible but doesn't feel like an error or blocker. Editor remains fully usable with the nudge present.

### REQ-009 — Dismiss behavior
Tapping "×" **shall** set `window._memMatchDismissed = true` and hide the nudge. The dismissed state **shall** clear when the jot content changes enough that a new check would score ≥ 0.12 (i.e., the dismissed match is no longer the top match, or a higher-scoring new match is found).

**Acceptance:** After dismissing, the nudge stays hidden while the same match is top-ranked. Adding new content that surfaces a different match re-shows the nudge.

### REQ-010 — "Compare →" navigation
Tapping "Compare →" **shall**:
- For a note match: call `openNoteEditor(note.id)` to open that note in the editor panel.
- For a daily-doc match: call `navigateTo('jots')` and expand the matched date via `toggleDocDay`.

**Acceptance:** Tapping Compare on a note match opens that note. Tapping on a daily-doc match expands that day in the jots view.

### REQ-011 — No self-match
The check **shall** never match against today's date entry in `DATA.dailyDocs`.

**Acceptance:** Even if today's doc is passed as a candidate, it is skipped.

### REQ-012 — Performance guard
The full check (tokenize + score all candidates) **shall** complete in under 100ms for a corpus of up to 200 notes + 90 daily docs. Scoring is synchronous and runs in the main thread.

**Acceptance:** `console.time` around the check shows < 100ms with a realistic data set.

---

## Open Questions

## Deviations from v0.1 (2026-08-30)

v0.1 shipped in PR #12 and was measured against the live corpus (22 notes, 137 daily
docs). Over the last 21 written days it produced 12 nudges, 10 of them worthless:

- **8 boilerplate collisions.** Every daily doc carries an app-injected End-of-Day
  template. Its words (`end, day, what, got, done, carrying, over`) were the strongest
  shared signal in the corpus. Three days scored a perfect 1.000 against each other
  because they contained the template and nothing else.
- **2 thin hits.** Single shared words against near-empty notes — Jaccard on a 2-term
  candidate is trivially high.

Two fixes, both forced by the data:

1. **Strip generated blocks before tokenizing** (`_memPlainText`): `<h2>` sections (the
   Morning Brief's Overdue / Due Today / Calendar headers) and the End-of-Day prompt.
   Document-frequency filtering was tried first and rejected — at this corpus size the
   template words sit at 15-21% DF, indistinguishable from `viking` (21%) and `ticket`
   (25%), so any cut that removed the template also removed the vocabulary that matters.
2. **Overlap coefficient instead of Jaccard.** Jaccard's union denominator punishes
   short text, and real jots are short — median 7 meaningful terms. A 7-term jot against
   a 200-term note caps near 0.03, so a template collision beat every genuine match by
   construction. `min()` removes the length bias; the new `_MEM_MIN_OVERLAP = 3` floor
   does the work of rejecting coincidence that the union term was supposedly doing.

Result on the same 30 days: 7 nudges, 0 on boilerplate, every one with 3+ shared
meaningful terms. Gates in `GATES.md`; the pre-fix algorithm is kept at
`checks/fixtures/prefix-block.js` as G2's control.

### OQ-1 — MEMORY.md matching
The idea spec'd "K2 memory" as part of the corpus. MEMORY.md is on disk, not in `DATA`. Options: (a) pre-index via cron into `DATA.memoryIndex[]`; (b) skip for MVP and revisit. **Recommend (b) — ship notes + daily docs first, add MEMORY.md index as Phase 2.**

**Decided 2026-08-30 — (b), skip for MVP.** Ryan signed off.

### OQ-2 — Previous-day editor
Should the nudge also run when editing a previous-day doc? The hook for previous-day editors (`_createDayEditor.onUpdate → debouncedSavePreviousDoc`) is a simpler debounce. **Decided 2026-08-30 — no.** Ryan signed off. Today's editor is the primary capture surface.
