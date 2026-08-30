#!/usr/bin/env python3
"""G4 — the flag round-trips. This is Ryan's rollback, not a nicety: he agreed to try the
new design, not to lose the old one. Off must restore the flat rail exactly."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from _boot import open_app
from playwright.sync_api import sync_playwright

def main():
    fails = []
    with sync_playwright() as pw:
        # 1. default is OFF — the previous UI is what loads until Ryan says otherwise
        b, pg = open_app(pw, ui2=False)
        if pg.evaluate("() => document.body.classList.contains('ui2')"):
            fails.append("new design is on by default; it must be opt-in")
        flat = pg.evaluate("() => document.querySelectorAll('#nav-section-everything-body .nav-item').length")
        groups_off = pg.evaluate("() => document.querySelectorAll('.u-grp').length")
        if groups_off: fails.append(f"{groups_off} group headers rendered while the flag is off")
        if flat < 25: fails.append(f"old rail shows only {flat} tools")
        b.close()

        # 2. on -> grouped, and every tool still present in the DOM
        b, pg = open_app(pw, ui2=True)
        if not pg.evaluate("() => document.body.classList.contains('ui2')"):
            fails.append("flag did not apply on a cold load")
        grouped = pg.evaluate("() => document.querySelectorAll('.u-grp').length")
        rows_on = pg.evaluate("() => document.querySelectorAll('#nav-section-everything-body .nav-item').length")
        if grouped != 4: fails.append(f"expected 4 group headers, got {grouped}")
        if rows_on != flat:
            fails.append(f"tool count changed with the flag: {flat} -> {rows_on}. Redesign became a deletion")

        # 3. toggling off at runtime restores the flat rail, no reload
        pg.evaluate("() => setUiTwo(false)"); pg.wait_for_timeout(300)
        if pg.evaluate("() => document.body.classList.contains('ui2')"):
            fails.append("setUiTwo(false) left the class on")
        back = pg.evaluate("() => document.querySelectorAll('#nav-section-everything-body .nav-item').length")
        if pg.evaluate("() => document.querySelectorAll('.u-grp').length"):
            fails.append("group headers survived turning the flag off")
        if back != flat: fails.append(f"rail did not restore: {flat} -> {back}")
        if pg.evaluate("() => localStorage.getItem('k2.ui2')") != "0":
            fails.append("preference not persisted as off")

        # 4. and back on again — a one-way door is not a rollback
        pg.evaluate("() => setUiTwo(true)"); pg.wait_for_timeout(300)
        if pg.evaluate("() => document.querySelectorAll('.u-grp').length") != 4:
            fails.append("second toggle on did not re-group")
        b.close()

    if fails:
        print("G4 FAIL:\n  " + "\n  ".join(fails)); return 1
    print(f"G4 PASS: opt-in by default; flag on groups the same {flat} tools under 4 headers "
          f"with no change in count; off restores the flat rail live and persists; on again re-groups")
    return 0

if __name__ == "__main__":
    sys.exit(main())
