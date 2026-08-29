# GATES — Basecoat conversion, note surfaces only

Scope locked by Ryan 2026-08-29: "Do jots, notes and today before the rest."
Three surfaces: Today (daily jot home), Notes list, Note editor. Prototype only —
nothing lands in `index.html` until Ryan compares them side by side.

Palette is not up for redecision. Graphite/blue, locked 2026-08-28:
ground `oklch(16% 0.010 255)`, accent `oklch(72% 0.135 250)`, no second accent.

Run: `node ../../skills/unlazy/scripts/gate-check.mjs --reverify GATES.md`
(paths below are relative to `k2-dashboard/spec/ui-modernization/`)

---

- [ ] G1 — Basecoat is pinned, not floating. No `@latest` in any prototype file.
    CHECK: ! grep -rn "basecoat-css@latest" prototype/
    EXPECT: exit 0

- [ ] G2 — The three prototype files exist.
    CHECK: ls prototype/bc-today.html prototype/bc-notes.html prototype/bc-note.html
    EXPECT: bc-note.html

- [ ] G3 — Each file actually loads the pinned Basecoat CSS.
    CHECK: grep -lc "basecoat-css@1.0.2/dist/basecoat.cdn.css" prototype/bc-today.html prototype/bc-notes.html prototype/bc-note.html | wc -l | tr -d ' '
    EXPECT: 3

- [ ] G4 — Basecoat components are actually used, not just linked. Each file
      carries real Basecoat classes rather than a hand-rolled lookalike.
    CHECK: for f in prototype/bc-*.html; do grep -qE 'class="[^"]*\b(btn|card|input|badge|tabs|select)\b' "$f" || { echo "BARE $f"; exit 1; }; done; echo all-styled
    EXPECT: all-styled

- [ ] G5 — Locked palette, no stray colors. Every declared color is oklch or a
      token reference. A hex literal means someone eyeballed it.
    CHECK: ! grep -rnE '#[0-9a-fA-F]{3,8}\b' prototype/bc-*.html
    EXPECT: exit 0

- [ ] G6 — The accent is the locked blue, present in every surface.
    CHECK: grep -lc "oklch(72% 0.135 250)" prototype/bc-*.html | wc -l | tr -d ' '
    EXPECT: 3

- [ ] G7 — Mobile-first: no horizontal overflow at 390px on any surface.
      Measured in a real browser, not inferred from the CSS.
    CHECK: node scripts/measure.mjs 390
    EXPECT: no-overflow

- [ ] G8 — Renders at desktop width too (regression guard on the mobile work).
    CHECK: node scripts/measure.mjs 1280
    EXPECT: no-overflow

- [ ] G9 — Screenshots captured at phone and desktop width, and non-empty.
      Ryan sees the render, not my description of it.
    CHECK: node scripts/shoot.mjs && find shots -name '*.png' -size +8k | wc -l | tr -d ' '
    EXPECT: 6

- [ ] G10 — `index.html` is untouched by this work. Prototype-only means
      prototype-only.
    CHECK: cd ../.. && git diff --name-only HEAD -- index.html | wc -l | tr -d ' '
    EXPECT: 0

---

## Deliberately NOT gated

- Visual quality. No script can tell me whether it looks like AI slop. That is
  Ryan's call off the screenshots, which is why G9 exists.
- Data wiring. These are static prototypes with representative content. Wiring
  to `DATA` is the next step and gets its own ledger.
