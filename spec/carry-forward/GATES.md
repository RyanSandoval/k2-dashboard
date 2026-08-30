# Gates: yesterday's unfinished lines follow you into today

OWNS: spec/carry-forward/**, index.html (the carry-forward block only)

Scope: `PLAN.md` says "Yesterday's unfinished lines carry forward, visibly, as carried-over —
not silently." Today that does not happen: `renderJots()` creates a new day as
`{ content: '<p></p>' }` and nothing looks at the day before. Across 138 days of notes there
are 170 task items, 124 of them unchecked — so the lines exist, they just die with the day
that wrote them.

Two things make this riskier than it sounds. Ten of those docs nest a `taskList` **inside**
a `taskItem`, so anything that pairs `<li ...>` with the next `</li>` mis-slices them. And
the daily note is the one artifact in this app that is purely Ryan's writing — a carry
step that runs twice, or runs against a day he has already typed into, damages the only
surface he actually uses. G3 is the gate that matters.

The note-first landing is NOT in scope: `page-jots` already carries `active` in the markup,
so the app already opens in today's note.

- [x] G1: extraction finds exactly the unfinished lines, including under a checked parent, and never twice
  CHECK: node /Users/ryansandoval/k2-dashboard/spec/carry-forward/checks/g1_extract.mjs
  EXPECT: G1 PASS
  EVIDENCE: exit=0; shell=/bin/sh; cwd=/Users/ryansandoval/k2-dashboard/spec/carry-forward; path=cacef1cfa82c/13 entries; output=G1 PASS: 4 nesting cases correct incl. unchecked-child-of-checked-parent, naive slice proven wrong by control; over 138 real days (10 with nested task lists) extracted 122 unfinished items across 60 days, every one a balanced unchecked task

- [x] G2: carrying forward happens once — re-rendering the day does not duplicate the lines
  CHECK: node /Users/ryansandoval/k2-dashboard/spec/carry-forward/checks/g2_once.mjs
  EXPECT: G2 PASS
  EVIDENCE: exit=0; shell=/bin/sh; cwd=/Users/ryansandoval/k2-dashboard/spec/carry-forward; path=cacef1cfa82c/13 entries; output=G2 PASS: 2 of 3 lines carried once with a marker naming Saturday, 3 consecutive runs left the doc byte-identical (1 marker, 2 lines), and a zero-carry day is stamped without touching its content

- [x] G3: it cannot damage a note — a day with writing in it is left byte-identical, and the source day is never mutated
  CHECK: node /Users/ryansandoval/k2-dashboard/spec/carry-forward/checks/g3_safety.mjs
  EXPECT: G3 PASS
  EVIDENCE: exit=0; shell=/bin/sh; cwd=/Users/ryansandoval/k2-dashboard/spec/carry-forward; path=cacef1cfa82c/13 entries; output=G3 PASS: 4 kinds of already-written day left byte-identical, 5 blank shapes still carry, and replaying all 138 real days (122 lines carried) mutated no source day and no other day

- [x] G4: the carried block survives TipTap — the real editor parses and re-serializes it without dropping the marker or the items
  CHECK: python3 /Users/ryansandoval/k2-dashboard/spec/carry-forward/checks/g4_roundtrip.py
  EXPECT: G4 PASS
  EVIDENCE: exit=0; shell=/bin/sh; cwd=/Users/ryansandoval/k2-dashboard/spec/carry-forward; path=cacef1cfa82c/13 entries; output=G4 PASS: the real editor parsed and re-serialized the carried block — marker, both unfinished lines and the nested sub-item intact, completed line and prose left behind, source day unchanged
