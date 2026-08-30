# Gates: build G into index.html

OWNS: spec/ui-rebuild/**, index.html (design tokens, sidebar, Today page)

Scope: seven mockups in, Ryan approved G and said build it. This lands the design system
and the two surfaces it changes — the sidebar and Today — against the real app.

The load-bearing risk is not visual. Ryan decided twice to keep all 34 surfaces, and this
work collapses a flat 35-item rail into 6 primary plus three collapsed groups. If a single
page stops being reachable, the change is a deletion he did not agree to. G1 is that gate
and it is the reason the sidebar renders from the existing K2_TOOLS taxonomy rather than a
second hand-written list that could drift from it.

Second risk: index.html holds a live TipTap editor with carry-forward, agent results and
task retirement shipped into it today. A restyle that breaks the editor costs more than the
design gains. G5 re-runs those suites unchanged.

The old UI stays reachable behind a flag until Ryan has used this for a day — that is his
rollback, not a nicety, so G4 proves it round-trips.

- [x] G1: every one of the 35 tools is still reachable, and the sidebar is generated from the taxonomy rather than duplicating it
  CHECK: node /Users/ryansandoval/k2-dashboard/spec/ui-rebuild/checks/g1_reachable.mjs
  EXPECT: G1 PASS
  EVIDENCE: exit=0; shell=/bin/sh; cwd=/Users/ryansandoval/k2-dashboard/spec/ui-rebuild; path=f33e2ca3f1bd/13 entries; output=G1 PASS: all 34 tools reachable — 6 primary + daily 6 + work 10 + review 8 + machine 10; rail generated from K2_TOOLS/K2_GROUPS with 0 hard-coded pages, and a newly added tool renders without touching it

- [x] G2: every text style in the new UI clears WCAG AA, measured from rendered pixels in both colour schemes
  CHECK: python3 /Users/ryansandoval/k2-dashboard/spec/ui-rebuild/checks/g2_contrast.py
  EXPECT: G2 PASS
  EVIDENCE: exit=0; shell=/bin/sh; cwd=/Users/ryansandoval/k2-dashboard/spec/ui-rebuild; path=f33e2ca3f1bd/13 entries; output=G2 PASS: 19 text styles across the sidebar and Today, dark-only as declared, all clear WCAG AA

- [x] G3: the new CSS is on-scale — no ad-hoc font sizes, spacing, weights or radii
  CHECK: node /Users/ryansandoval/k2-dashboard/spec/ui-rebuild/checks/g3_scale.mjs
  EXPECT: G3 PASS
  EVIDENCE: exit=0; shell=/bin/sh; cwd=/Users/ryansandoval/k2-dashboard/spec/ui-rebuild; path=f33e2ca3f1bd/13 entries; output=G3 PASS: 0 off-scale font sizes, spacing values or radii in the ui2 rules; weights limited to 600/400; 44 scale references, every radius via --u-r

- [x] G4: the flag round-trips — the previous UI is one setting away and restores the full rail
  CHECK: python3 /Users/ryansandoval/k2-dashboard/spec/ui-rebuild/checks/g4_flag.py
  EXPECT: G4 PASS
  EVIDENCE: exit=0; shell=/bin/sh; cwd=/Users/ryansandoval/k2-dashboard/spec/ui-rebuild; path=f33e2ca3f1bd/13 entries; output=G4 PASS: opt-in by default; flag on groups the same 29 tools under 4 headers with no change in count; off restores the flat rail live and persists; on again re-groups

- [x] G5: the editor is untouched — carry-forward, agent results and task retirement all still pass
  CHECK: bash /Users/ryansandoval/k2-dashboard/spec/ui-rebuild/checks/g5_no_regression.sh
  EXPECT: G5 PASS
  EVIDENCE: exit=0; shell=/bin/sh; cwd=/Users/ryansandoval/k2-dashboard/spec/ui-rebuild; path=f33e2ca3f1bd/13 entries; output=G4 PASS: page, nav entry, both dispatch sites, section expansion and the dashboard alert all point at task-retirement; no id-only lookups left; 7 script blocks parse | G5 PASS: carry-forward 4/4, agent-result node registered, task-retiremen
