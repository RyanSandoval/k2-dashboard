## 2025-02-18 - Keyboard Access for Custom Search Trigger
**Learning:** Found over 100 `div` and `span` tags acting as buttons via `onclick` handlers but lacking basic keyboard accessibility requirements (`role="button"`, `tabindex="0"`, `onkeydown`).
**Action:** Consistently check `div` and `span` tags with `onclick` handlers for accessibility requirements. Make sure to map 'Enter' and 'Space' keys to the click action to prevent keyboard traps. Add `:focus-visible` styles alongside `:hover` to show focus indicators.
