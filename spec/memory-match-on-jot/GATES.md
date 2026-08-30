# Gates: memory match on jot actually recalls something

OWNS: spec/memory-match-on-jot/**, index.html (the memory-match block only)

Scope: the feature shipped in PR #12 and was firing — but on the wrong thing. Replayed
against Ryan's live data it produced 12 nudges over the last 21 written days, 10 of them
junk: 8 were the End-of-Day template colliding with itself (three at a perfect 1.000
between days containing nothing but the template) and 2 were single-word hits on
near-empty notes. Two causes stacked. The app injects boilerplate into every daily doc,
so the strongest shared signal in the corpus is text neither party wrote. And Jaccard
divides by the union, so a 7-term jot against a 200-term note caps around 0.03 and can
never outrank a template match. These gates cover the fix and, more importantly, prove
the check can still fail.

- [x] G1: boilerplate strips to nothing, scoring is length-neutral, and coincidence is rejected
  CHECK: node /Users/ryansandoval/k2-dashboard/spec/memory-match-on-jot/checks/g1_scoring.mjs
  EXPECT: G1 PASS
  EVIDENCE: exit=0; shell=/bin/sh; cwd=/Users/ryansandoval/k2-dashboard/spec/memory-match-on-jot; path=3310fa59fcbb/13 entries; output=G1 PASS: boilerplate stripped to nothing, scoring is length-neutral where jaccard scored 0.029, fewer than 3 shared terms rejected (13 assertions)

- [x] G2: on Ryan's live data no nudge fires on boilerplate, real recall survives, and the pre-fix code fails this same check
  CHECK: node /Users/ryansandoval/k2-dashboard/spec/memory-match-on-jot/checks/g2_realdata.mjs
  EXPECT: G2 PASS
  EVIDENCE: exit=0; shell=/bin/sh; cwd=/Users/ryansandoval/k2-dashboard/spec/memory-match-on-jot; path=3310fa59fcbb/13 entries; output=2026-07-22 -> note:Create new jira ticket  shared=create,ticket,all,cruise,destination,pages | 2026-07-16 -> note:1:1 with Tim  shared=mdf,send,link,khalid

- [x] G3: index.html parses and the nudge is wired to the today editor, with no stale threshold left behind
  CHECK: node /Users/ryansandoval/k2-dashboard/spec/memory-match-on-jot/checks/g3_wiring.mjs
  EXPECT: G3 PASS
  EVIDENCE: exit=0; shell=/bin/sh; cwd=/Users/ryansandoval/k2-dashboard/spec/memory-match-on-jot; path=3310fa59fcbb/13 entries; output=G3 PASS: nudge markup present under today's editor, debounce hooked into onUpdate, boilerplate stripping applied to jot + both candidate kinds, no stale 0.12 literal, all 8 inline script blocks parse

- [x] G4: the full check stays inside its 100ms main-thread budget on the real corpus
  CHECK: node /Users/ryansandoval/k2-dashboard/spec/memory-match-on-jot/checks/g4_perf.mjs
  EXPECT: G4 PASS
  EVIDENCE: exit=0; shell=/bin/sh; cwd=/Users/ryansandoval/k2-dashboard/spec/memory-match-on-jot; path=3310fa59fcbb/13 entries; output=G4 PASS: 22 notes + 30 daily docs scored in 0.6ms median, 1.0ms worst of 20 runs (budget 100ms)

Notes:
- G2 loads the real block out of index.html rather than reimplementing it, and its
  control runs `checks/fixtures/prefix-block.js` — the algorithm exactly as PR #12
  shipped it. If that control ever stops producing boilerplate matches, G2 fails on
  purpose: it means the gate is no longer measuring anything.
- G2 needs a live data snapshot at /tmp/k2data.json. Refresh with:
  gh api repos/RyanSandoval/k2-data/git/blobs/$(gh api repos/RyanSandoval/k2-data/contents/data.json --jq .sha) --jq .content | tr -d '\n' | base64 -d > /tmp/k2data.json
