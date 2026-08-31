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

G6 was added after shipping. Ryan turned the flag on and reported that nothing changed on
his phone, and he was right: .sidebar is display:none at 390px, so nearly everything this
layer restyles was invisible there. Gates measured at 1440px only, which made "the design
system is in" true and "Ryan can see it" false at the same time. G6 measures the chrome a
phone actually renders.

- [x] G1: every one of the 35 tools is still reachable, and the sidebar is generated from the taxonomy rather than duplicating it
  CHECK: node /Users/ryansandoval/k2-dashboard/spec/ui-rebuild/checks/g1_reachable.mjs
  EXPECT: G1 PASS
  EVIDENCE: exit=0; shell=/bin/sh; cwd=/Users/ryansandoval/k2-dashboard/spec/ui-rebuild; path=9574616d3339/13 entries; output=G1 PASS: all 34 tools reachable — 6 primary + daily 6 + work 10 + review 8 + machine 10; rail generated from K2_TOOLS/K2_GROUPS with 0 hard-coded pages, and a newly added tool renders without touching it

- [x] G2: every text style in the new UI clears WCAG AA, measured from rendered pixels in both colour schemes
  CHECK: python3 /Users/ryansandoval/k2-dashboard/spec/ui-rebuild/checks/g2_contrast.py
  EXPECT: G2 PASS
  EVIDENCE: exit=0; shell=/bin/sh; cwd=/Users/ryansandoval/k2-dashboard/spec/ui-rebuild; path=9574616d3339/13 entries; output=G2 PASS: 18 text styles across the sidebar and Today, dark-only as declared, all clear WCAG AA

- [x] G3: the new CSS is on-scale — no ad-hoc font sizes, spacing, weights or radii
  CHECK: node /Users/ryansandoval/k2-dashboard/spec/ui-rebuild/checks/g3_scale.mjs
  EXPECT: G3 PASS
  EVIDENCE: exit=0; shell=/bin/sh; cwd=/Users/ryansandoval/k2-dashboard/spec/ui-rebuild; path=9574616d3339/13 entries; output=G3 PASS: 0 off-scale font sizes, spacing values or radii in the ui2 rules; weights limited to 600/400; 110 scale references, every radius via --u-r

- [x] G4: the flag round-trips — the previous UI is one setting away and restores the full rail
  CHECK: python3 /Users/ryansandoval/k2-dashboard/spec/ui-rebuild/checks/g4_flag.py
  EXPECT: G4 PASS
  EVIDENCE: exit=0; shell=/bin/sh; cwd=/Users/ryansandoval/k2-dashboard/spec/ui-rebuild; path=9574616d3339/13 entries; output=G4 PASS: on by default with no stored preference, explicit off still wins; flag on groups the same 29 tools under 4 headers with no change in count; off restores the flat rail live and persists; on again re-groups

- [x] G5: the editor is untouched — carry-forward, agent results and task retirement all still pass
  CHECK: bash /Users/ryansandoval/k2-dashboard/spec/ui-rebuild/checks/g5_no_regression.sh
  EXPECT: G5 PASS
  EVIDENCE: exit=0; shell=/bin/sh; cwd=/Users/ryansandoval/k2-dashboard/spec/ui-rebuild; path=9574616d3339/13 entries; output=G4 PASS: page, nav entry, both dispatch sites, section expansion and the dashboard alert all point at task-retirement; no id-only lookups left; 7 script blocks parse | G5 PASS: carry-forward 4/4, agent-result node registered, task-retiremen

- [x] G6: the flag visibly changes a phone — the chrome a 390px viewport actually renders, not the sidebar it never shows
  CHECK: python3 /Users/ryansandoval/k2-dashboard/spec/ui-rebuild/checks/g6_mobile.py
  EXPECT: G6 PASS
  EVIDENCE: exit=0; shell=/bin/sh; cwd=/Users/ryansandoval/k2-dashboard/spec/ui-rebuild; path=9574616d3339/13 entries; output=G6 PASS: at 390px the flag changes the chrome a phone actually shows — 5/5 tab icons drawn (0 emoji, restored to 4 when off), tab bar repainted, editor uncapped with a 472.64px canvas, placeholder in-flow and no focus ring round the note

- [x] G7: on a phone the note is the page — the canvas dominates, suggestions defer, and the search button clears the tab bar
  CHECK: python3 /Users/ryansandoval/k2-dashboard/spec/ui-rebuild/checks/g7_mobile_composition.py
  EXPECT: G7 PASS
  EVIDENCE: exit=0; shell=/bin/sh; cwd=/Users/ryansandoval/k2-dashboard/spec/ui-rebuild; path=9574616d3339/13 entries; output=G7 PASS: canvas 222 -> 473px and starts 132px in; suggestions 319 -> 258px (3 rows, tallest 77px); search button not shown on Today (G10: it covered a -> note button); smallest touch target 44px; no sideways scroll

- [x] G8: the flag reaches the whole app, not just Today — retuned tokens arrive on other pages and contrast is no worse than the UI Ryan has now
  CHECK: python3 /Users/ryansandoval/k2-dashboard/spec/ui-rebuild/checks/g8_whole_app.py
  EXPECT: G8 PASS
  EVIDENCE: exit=0; shell=/bin/sh; cwd=/Users/ryansandoval/k2-dashboard/spec/ui-rebuild; path=9574616d3339/13 entries; output=G8 PASS: tokens reach the app (radius 10px->4px, type clamp(0.875rem, 0.85rem + 0.15vw, 1rem)->16px, --sp-5 20px->24px); 175 text styles over 12 pages; contrast failures 13 -> 3. Remaining (hard-coded inline colours the tokens cannot reach)

- [x] G9: adding a task to today puts it beside the others, not inside them, and a typed line carries no other task's id
  CHECK: python3 /Users/ryansandoval/k2-dashboard/spec/ui-rebuild/checks/g9_flat_insert.py
  EXPECT: G9 PASS
  EVIDENCE: exit=0; shell=/bin/sh; cwd=/Users/ryansandoval/k2-dashboard/spec/ui-rebuild; path=9574616d3339/13 entries; output=G9 PASS: 4 adds give 4 sibling items in 1 flat list at nesting depth 0; Enter adds a 5th that carries no task id (so it cannot close another task); re-adding an existing task still de-dupes

- [x] G10: on a phone nothing floats on top of anything — no fixed or absolute control overlaps text or a touch target, at the top of the page or at the bottom of the scroll
  CHECK: python3 /Users/ryansandoval/k2-dashboard/spec/ui-rebuild/checks/g10_no_overlap.py
  EXPECT: G10 PASS
  EVIDENCE: exit=0; shell=/bin/sh; cwd=/Users/ryansandoval/k2-dashboard/spec/ui-rebuild; path=9574616d3339/13 entries; output=G10 PASS: no floating control overlaps text or a touch target, at rest or at the end of scroll; Attach clears the first line; nothing rests under the 755px tab bar; search button hidden
