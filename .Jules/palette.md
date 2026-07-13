## 2024-05-24 - Interactive Custom Elements Require Keyboard Handlers

**Learning:** When using `div` or `span` elements as interactive buttons (with `role="button"` and `tabindex="0"`), adding standard keyboard navigation to map 'Enter' and 'Space' to the click action is crucial. The default browser behavior does not trigger `onclick` for non-button elements, causing a keyboard trap or unclickable elements for keyboard users.

**Action:** Whenever adding `role="button"` and `tabindex="0"` to a non-button element in this codebase, ensure an `onkeydown` handler is also added to intercept 'Enter' and 'Space' keys and trigger the `click()` event. Use `event.preventDefault()` to prevent default page scrolling when pressing 'Space'.
