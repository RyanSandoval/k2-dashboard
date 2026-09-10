## 2024-05-18 - Missing label for attributes

**Learning:** When inputs have visible labels next to them in the DOM, using \`aria-label\` on the input creates a WCAG 2.5.3 (Label in Name) violation if the text does not exactly match. The more robust accessibility pattern is to link the visible \`<label>\` directly to the input using the \`for\` attribute.
**Action:** Before adding \`aria-label\` to an unlabelled input, check if there is a visible label adjacent to it. If so, link them using the \`for\` attribute on the label. Only use \`aria-label\` when there is truly no visible text label.
