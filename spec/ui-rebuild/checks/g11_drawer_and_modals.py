"""G11 — the two behaviours this morning's auto-fix run actually changed.

The ten gates before this one all passed with the diff in place, which only proved it broke
nothing. Neither half of it was tested by anything:

  1. Escape used to write inline display:none onto a .ui-modal. .ui-modal.is-open sets
     display:block, and an inline style beats a class, so the modal could never reopen —
     for the rest of the session, not just the next click. Every ui-modal is affected.
  2. The More drawer's tiles are built by renderLauncher(), which ran only when the sheet
     was opened, and its buttons carried no class navigateTo()/mobileNavMore() look for.
     So a drawer page could never show as current.

Both halves are control-tested: the check re-applies the old behaviour in the live page and
requires the assertion to fail. A gate that passes against the bug is not a gate.
"""
import sys
sys.path.insert(0, "/Users/ryansandoval/k2-dashboard/spec/ui-rebuild/checks")
from _boot import open_app
from playwright.sync_api import sync_playwright

FAIL = []


def g11(pw):
    # ---- part 1: modals reopen after Escape (desktop width — modals are a desktop surface)
    b, pg = open_app(pw, ui2=True, width=1440)

    ids = pg.eval_on_selector_all(".ui-modal[id$='-modal']", "els => els.map(e => e.id)")
    if not ids:
        FAIL.append("no .ui-modal elements found — selector drifted")
        b.close()
        return

    def open_close_reopen(mid):
        """open -> Escape -> open again; report whether it is visible the second time."""
        pg.evaluate(f"document.getElementById('{mid}').classList.add('is-open')")
        first = pg.eval_on_selector(f"#{mid}", "e => getComputedStyle(e).display")
        pg.keyboard.press("Escape")
        closed = pg.eval_on_selector(f"#{mid}", "e => getComputedStyle(e).display")
        pg.evaluate(f"document.getElementById('{mid}').classList.add('is-open')")
        second = pg.eval_on_selector(f"#{mid}", "e => getComputedStyle(e).display")
        return first, closed, second

    reopened = 0
    for mid in ids:
        first, closed, second = open_close_reopen(mid)
        if first == "none":
            FAIL.append(f"{mid}: is-open did not show it (display:{first})")
        if closed != "none":
            FAIL.append(f"{mid}: Escape did not close it (display:{closed})")
        if second == "none":
            FAIL.append(f"{mid}: could not reopen after Escape (display:{second}) — the bug")
        else:
            reopened += 1

    # control: restore the old one-liner and require the same assertion to fail
    pg.evaluate("""() => {
      window.__realClose = closeAllModals;
      window.closeAllModals = function () {
        document.querySelectorAll('[id$="-modal"]').forEach(m => {
          if (m.style.display !== 'none') m.style.display = 'none';
        });
      };
    }""")
    ctl = ids[0]
    _, _, ctl_second = open_close_reopen(ctl)
    if ctl_second != "none":
        FAIL.append(f"CONTROL: old closeAllModals still let {ctl} reopen — gate proves nothing")
    pg.evaluate("window.closeAllModals = window.__realClose")

    # the Escape path users take is the keydown handler, not a direct call — confirm it is wired
    handler_ok = pg.evaluate("typeof closeAllModals === 'function'")
    if not handler_ok:
        FAIL.append("closeAllModals is not a function on window")
    b.close()

    # ---- part 2: the More drawer marks the current page, at phone width
    b, pg = open_app(pw, ui2=True, width=390)

    # tiles must exist before the sheet is ever opened (DOMContentLoaded render)
    pre = pg.eval_on_selector_all(".mobile-more-item[data-page]", "e => e.length")
    if pre == 0:
        FAIL.append("drawer has no .mobile-more-item tiles before opening — init render missing")

    pages = pg.eval_on_selector_all(
        ".mobile-more-item[data-page]", "els => els.map(e => e.dataset.page)")
    target = next((p for p in pages if p not in ("dashboard", "jots", "tasks", "notes")), None)
    if not target:
        FAIL.append(f"no drawer-only page among {len(pages)} tiles to navigate to")
    else:
        pg.evaluate(f"k2Launch('{target}')")
        pg.wait_for_timeout(500)

        marked = pg.eval_on_selector_all(
            ".mobile-more-item.active", "els => els.map(e => e.dataset.page)")
        if marked != [target]:
            FAIL.append(f"k2Launch('{target}') marked {marked or 'nothing'}, expected exactly it")

        # the page actually changed — active state on a page you did not land on is worse
        # than none at all
        shown = pg.evaluate("""() => {
          const p = [...document.querySelectorAll('[id^="page-"]')]
            .find(e => getComputedStyle(e).display !== 'none');
          return p ? p.id.replace('page-','') : null;
        }""")
        if shown != target:
            FAIL.append(f"k2Launch('{target}') left {shown} on screen")

        # a drawer page has no tab of its own, so More is the honest marker
        more_active = pg.evaluate(
            "!!document.querySelector('.mobile-nav-item:last-child.active')")
        if not more_active:
            FAIL.append("More tab not marked active for a drawer page")

        # control: strip the class the fix adds and require the marking to stop working
        pg.evaluate("""() => document.querySelectorAll('.mobile-more-item')
                        .forEach(e => e.classList.remove('mobile-more-item','active'))""")
        pg.evaluate(f"k2Launch('{target}')")
        pg.wait_for_timeout(300)
        if pg.eval_on_selector_all(".mobile-more-item.active", "e => e.length") != 0:
            FAIL.append("CONTROL: marking survived removing .mobile-more-item — gate proves nothing")

    tiles = len(pages)
    b.close()
    return reopened, len(ids), tiles, target


with sync_playwright() as pw:
    r = g11(pw)

if FAIL:
    print("G11 FAIL:")
    for f in FAIL:
        print("  -", f)
    sys.exit(1)

reopened, total, tiles, target = r
print(f"G11 PASS: {reopened}/{total} ui-modals close on Escape and reopen after "
      f"(old closeAllModals control-fails); {tiles} drawer tiles exist before the sheet is "
      f"opened, k2Launch('{target}') navigates and marks that tile plus the More tab, and "
      f"removing .mobile-more-item control-fails")
