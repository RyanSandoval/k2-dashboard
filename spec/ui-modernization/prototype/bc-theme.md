# The theme block

Every `bc-*.html` carries the same `:root.dark` override inline rather than sharing a
stylesheet. That is deliberate, not laziness: the destination is `index.html`, a single
self-contained file with no build step, so a prototype that needs a second file to look
right is not testing the thing we are going to ship. Each file opens standalone from
`file://` and looks exactly as it will in the app.

Basecoat themes entirely through oklch custom properties, so the locked graphite/blue
palette drops in by overwriting twelve values. Nothing is restyled by hand.

Locked 2026-08-28, from `../PLAN.md`:

| token | value | role |
|---|---|---|
| `--background` | `oklch(16% 0.010 255)` | cool ground |
| `--primary` | `oklch(72% 0.135 250)` | the single accent |

Basecoat's own defaults write lightness as `0.145`; the plan writes `16%`. Same colour
space, same number — the percent form is kept so the values are greppable against the
plan that locked them.
