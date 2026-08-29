# K2 Dashboard — Design & UX Overhaul

Written 2026-08-28, rewritten after Ryan: "the only thing I really love is my jots, the
daily note that refreshes every day. Everything else is just noise, other than maybe
reminders."

## Thesis

**The daily note is the product.** Everything else is input to it, output of it, or noise.

This is not a preference to be accommodated around the edges. It is the whole design.

Two pieces of evidence, both from today:

1. **16 of the last 30 days have a note written**, 136 days total since February. Nothing
   else in the app has a habit attached to it.
2. **Today's note contains the agent mention that filed a Jira ticket.** The line
   "Create a ticket for changing promo cards…" with a 🤖 mention is what the inline router
   picked up and routed to #viking-jira. The note is already a command line.

Meanwhile: 34 nav entries, seven with anything live in them, and seven holding literally
zero items — inbox, someday, weekly review, accomplishments, docs, growth, jira ledger.
Several of those were added by a past spec (`spec/amplenote-steals/`) whose premise was
that more surfaces would turn data into action. They are all empty. That experiment has
run and the result is in.

## The actual bug is not visual

Today the flow runs one way and ends somewhere Ryan never looks:

    jot → router → task / Jira request / reminder → a page he does not open

874 tasks exist. Most were machine-written by the jot→task promoter into a surface with no
reader. A cron writing to nobody is worse than no cron: it costs tokens, it grows the file
past the 1MB API ceiling, and it produces a number that makes the app feel like debt.

**Reverse the arrow.** Results come back into the note, on the line under what he wrote:

    Create a ticket for promo cards 2×3 vs 9×16   🤖
      ↳ MW-12363 filed · Ready for Release

That single change does more for the daily experience than any repaint, because it puts
the output where the attention already is.

## The new shape

Two surfaces and a drawer.

**Today's note** — the app opens here, cursor in the editor, no dashboard in front of it.
- Yesterday's unfinished lines carry forward, visibly, as carried-over — not silently.
- `🤖` mentions still dispatch; results land inline as above.
- A line with a time in it becomes a reminder without leaving the note.
- Past days are one swipe or one keystroke away, not a separate page.

**Reminders** — stays. It is new, it is used, and it is the one thing with a claim on
attention at a specific moment rather than on demand.

**System** — one drawer, not eleven pages: workers, crons, memory, mission, trash, skills.
The machine room. Rarely opened, and that is the correct frequency.

Everything else is folded into the note or removed: Requests, Action Inbox, Inbox, Ball
Back, Saw/Didn't Act, Stale Jots and Waiting For are eight doors onto "something arrived" —
they become at most one line in today's note when there is genuinely something, and nothing
at all when there is not. Tasks and Projects become note lines with a `#project` tag rather
than a database. Trading, Growth, AI Insights, Jira Ledger, Discussions, Accomplishments,
Weekly Review, Docs, Clips, Decisions: dead, cut them.

## What this costs

The pages do not have to be deleted on day one. Build the note-first home alongside the
existing app, move for two weeks, then delete what nobody missed. Additive first, subtractive
once proven — a page nobody opens is cheap to keep for a fortnight and expensive to remove
by mistake.

## Decisions needed before any pixels

1. **The 874 tasks.** Archive them wholesale and let the note carry work from here, or keep
   a real task surface? Recommendation: archive, and turn off the jot→task promoter. If a
   line matters it is in the note; if it is not in the note it did not matter.
2. **What K2 is allowed to write into the note.** Agent results, yes. Reminders that fired,
   probably. Cron health, morning briefs, finance snapshots — those would turn the one thing
   he loves into another feed. Recommendation: only things caused by a line he wrote.
3. **Reminders inside or beside the note.** Inline creation is clearly right; the question is
   whether the Reminders page survives as a list or becomes a filter over the note.

## Sequence

1. Answer the three questions above.
2. Prototype the note-first home as throwaway static HTML at phone width — carried-forward
   lines, inline agent results, inline reminder creation. Hold it before building it.
3. Wire results back into the note. This is valuable on its own and does not need the redesign.
4. Build the new home alongside the current one. Two weeks of real use.
5. Delete what was not missed.
6. Visual layer last: a two-surface app needs far less design system than a thirty-four
   surface one, which is the other reason to do structure first.

---

## Decisions locked

**2026-08-28 — Structure approved.** Note-first home, "Start here" three-with-reasons above
the note, agent results inline under the line that caused them, reminders as a property of a
line, three tabs (Today / Search / System). Ryan: "I agree with everything else."

**2026-08-28 — Palette: Graphite / blue.** Warm amber rejected. Cool ground
`oklch(16% 0.010 255)`, single blue accent `oklch(72% 0.135 250)`, cool-tinted neutrals,
no second accent. Supersedes the warm-amber direction in `DESIGN-AUDIT.md`, which is now
historical.

Canonical mockup: `prototype/today.html`. Rejected variants deleted — the decision is the
artifact, not the options.

**Answers to the three open questions:**
1. *Tasks* — keep them, but AI picks three and says why. The other 871 are searchable, never
   browsable. No triage-the-list UI.
2. *What K2 may write into the note* — things that make Ryan better, smarter, more organized.
   Operationally: a line earns its place only if it changes what he does next. Results of
   things he asked for, carried-forward work, patterns worth knowing. Not status feeds, cron
   health, morning briefs or finance snapshots.
3. *Reminders* — no separate app. A line with a time is a reminder; what is due shows at the
   top of the note; a fired reminder writes itself back into that day's note.

## Next

Step 3 of the sequence — **wire agent results back into the note** — is the highest-value
piece and does not depend on the redesign. The anchor already exists: an inline mention
carries `data-req-id` in the note HTML, so a result can be inserted as a sibling of the line
that caused it.

Risk to weigh before building it: this writes into `dailyDocs`, the one surface Ryan
actually loves. Corrupting a daily note is the worst available outcome, so it needs the
snapshot-and-verify treatment — never a blind HTML splice.
