"""G12 — Keyboard Triage Mode on Stale Jots.

The feature is a keyboard binding layered onto a surface that already had four working
buttons, so "it renders" proves nothing. What can actually break here is the routing:

  1. `t` and `j` were already bound globally (n / t / d / j / p) behind a typing guard in
     initKeyboardShortcuts(). If triage adds a second document listener, both fire and one
     keypress does two things. This check presses real keys and requires exactly one effect.
  2. The four verbs must mutate the underlying data, not just hide a row. Each is asserted
     against DATA (tasks array, note body, staleJotState, dailyDocs content).
  3. The undo stack must be multi-level and must restore the data AND the cursor.
  4. Triage must not be reachable on a phone, and the global shortcuts must still work
     when triage is off.

Three control tests are built in: neutralise the enter path, the cursor marking, and the
undo stack, and require the matching assertion to fail. A gate that passes against the
absent feature is not a gate.
"""
import sys
sys.path.insert(0, "/Users/ryansandoval/k2-dashboard/spec/ui-rebuild/checks")
from _boot import open_app
from playwright.sync_api import sync_playwright

FAIL = []
N = 30  # seeded stale lines; under STALE_JOTS_PAGE_SIZE (40) so all render on one page

SEED = """() => {
  const d = new Date(Date.now() - 60 * 86400000).toISOString().slice(0, 10);
  const lines = [];
  for (let i = 0; i < %d; i++) lines.push('<p>stale line ' + i + '</p>');
  DATA.dailyDocs = {};
  DATA.dailyDocs[d] = { content: lines.join('') };
  DATA.staleJotState = {};
  DATA.tasks = [];
  DATA.notes = [{ id: 'n1', title: 'Target note', text: '<p>existing body</p>',
                  updatedAt: '2026-01-01T00:00:00.000Z' }];
  navigateTo('stale-jots');
  return d;
}""" % N


def rows(pg):
    return pg.eval_on_selector_all("#stale-jots-list .card", "e => e.length")


def cursor_at(pg):
    """Index of the row carrying the triage cursor, or None."""
    return pg.evaluate("""() => {
      const all = [...document.querySelectorAll('#stale-jots-list .card')];
      const i = all.findIndex(e => e.dataset.triageCursor === '1');
      return i === -1 ? null : i;
    }""")


def remaining(pg):
    return pg.evaluate(
        "() => document.getElementById('stale-jots-triage-remaining')?.textContent || null")


def bar_shown(pg):
    # Absent element reads as not shown, so a build without the feature control-fails
    # with named assertions instead of a traceback.
    return pg.evaluate("""() => {
      const e = document.getElementById('stale-jots-triage-bar');
      return !!e && getComputedStyle(e).display !== 'none';
    }""")


def active_page(pg):
    return pg.evaluate("""() => {
      const p = [...document.querySelectorAll('.page')].find(e => e.classList.contains('active'));
      return p ? p.id.replace('page-', '') : null;
    }""")


def settle(pg, want):
    """Verb handlers are async (await saveData). Wait for the counter to land."""
    try:
        pg.wait_for_function(
            "n => document.getElementById('stale-jots-triage-remaining')?.textContent === n",
            arg=f"{want} remaining", timeout=5000)
    except Exception:
        pass
    pg.wait_for_timeout(150)


def g12(pw):
    b, pg = open_app(pw, ui2=True, width=1440)
    date = pg.evaluate(SEED)
    pg.wait_for_timeout(400)

    if rows(pg) != N:
        FAIL.append(f"seed did not produce {N} stale rows (got {rows(pg)}) — check the >7d cutoff")
        b.close()
        return

    # ── triage is off until asked for
    if bar_shown(pg):
        FAIL.append("triage bar visible before `t` was pressed")
    if cursor_at(pg) is not None:
        FAIL.append("a row was cursor-marked before triage started")

    # ── enter: `t` on this page starts triage instead of navigating to Tasks
    pg.keyboard.press("t")
    pg.wait_for_timeout(300)
    if active_page(pg) != "stale-jots":
        FAIL.append(f"`t` navigated to {active_page(pg)} — the global shortcut also fired")
    if not pg.evaluate("() => !!(window.K2Triage && K2Triage.active)"):
        FAIL.append("`t` did not activate triage")
    if not bar_shown(pg):
        FAIL.append("triage bar not shown after entering")
    if remaining(pg) != f"{N} remaining":
        FAIL.append(f"counter read {remaining(pg)!r} at entry, expected '{N} remaining'")
    if cursor_at(pg) != 0:
        FAIL.append(f"cursor at {cursor_at(pg)} on entry, expected row 0")

    # ── j/k move the cursor, and the focused row is scrolled into view
    for _ in range(25):
        pg.keyboard.press("j")
    pg.wait_for_timeout(1500)   # each j starts a smooth scroll; let the last one land
    if cursor_at(pg) != 25:
        FAIL.append(f"25x j left the cursor at {cursor_at(pg)}, expected 25")
    in_view = pg.evaluate("""() => {
      const el = document.querySelector('[data-triage-cursor]');
      if (!el) return false;
      const r = el.getBoundingClientRect();
      return r.top >= 0 && r.bottom <= window.innerHeight;
    }""")
    if not in_view:
        FAIL.append("cursor row 25 was not scrolled into view")
    pg.keyboard.press("k")
    pg.wait_for_timeout(200)
    if cursor_at(pg) != 24:
        FAIL.append(f"k left the cursor at {cursor_at(pg)}, expected 24")
    # j must not have also reached the global 'j' = navigate to Jots
    if active_page(pg) != "stale-jots":
        FAIL.append(f"j/k navigated to {active_page(pg)} — the global shortcut also fired")

    # back to the top so the four verbs act on known text
    for _ in range(30):
        pg.keyboard.press("k")
    pg.wait_for_timeout(300)
    if cursor_at(pg) != 0:
        FAIL.append("k did not clamp at row 0")

    # The seeded lines render in document order, so the row at index i is "stale line i".
    # Assert that rather than assume it — the verbs below act on the cursor, not on text.
    texts = [f"stale line {i}" for i in range(N)]
    first = pg.evaluate("() => document.querySelector('#stale-jots-list .card')?.textContent || ''")
    if texts[0] not in first:
        FAIL.append(f"row 0 is not {texts[0]!r} — seeded order is not what the verbs assume")

    # ── verb: t → task
    pg.keyboard.press("t")
    settle(pg, N - 1)
    tasks = pg.evaluate("() => (DATA.tasks || []).map(t => t.text)")
    if texts[0] not in tasks:
        FAIL.append(f"t did not create a task for {texts[0]!r} (DATA.tasks={tasks})")
    if pg.evaluate("() => Object.values(DATA.staleJotState).filter(s => s.action === 'task').length") != 1:
        FAIL.append("t did not record action:'task' in staleJotState")
    if remaining(pg) != f"{N-1} remaining":
        FAIL.append(f"counter read {remaining(pg)!r} after t, expected '{N-1} remaining'")

    # ── verb: n → note, with no modal
    pg.keyboard.press("n")
    settle(pg, N - 2)
    if pg.evaluate("() => !!document.getElementById('stale-jot-note-picker')"):
        FAIL.append("n opened the note picker modal — the feature is specified as modal-free")
    note_body = pg.evaluate("() => DATA.notes[0].text")
    if texts[1] not in note_body:
        FAIL.append(f"n did not append {texts[1]!r} to the note (body={note_body[:120]!r})")
    if remaining(pg) != f"{N-2} remaining":
        FAIL.append(f"counter read {remaining(pg)!r} after n")

    # ── verb: s → someday (archive)
    pg.keyboard.press("s")
    settle(pg, N - 3)
    if pg.evaluate("() => Object.values(DATA.staleJotState).filter(s => s.action === 'archive').length") != 1:
        FAIL.append("s did not record action:'archive' in staleJotState")

    # ── verb: x → trash (line removed from the daily doc)
    pg.keyboard.press("x")
    settle(pg, N - 4)
    doc = pg.evaluate(f"() => DATA.dailyDocs['{date}'].content")
    if texts[3] in doc:
        FAIL.append(f"x did not remove {texts[3]!r} from the daily doc")
    if pg.evaluate("() => Object.values(DATA.staleJotState).filter(s => s.discarded).length") != 1:
        FAIL.append("x did not record discarded in staleJotState")
    if remaining(pg) != f"{N-4} remaining":
        FAIL.append(f"counter read {remaining(pg)!r} after four verbs, expected '{N-4} remaining'")
    if rows(pg) != N - 4:
        FAIL.append(f"{rows(pg)} rows rendered after four verbs, expected {N-4}")

    if pg.evaluate("() => window.K2Triage ? K2Triage.undo.length : -1") != 4:
        FAIL.append(f"undo stack depth {pg.evaluate('() => window.K2Triage ? K2Triage.undo.length : -1')} after four verbs, expected 4")

    # ── undo: four levels, restoring data and cursor
    for want in (N - 3, N - 2, N - 1, N):
        pg.keyboard.press("u")
        settle(pg, want)
    if remaining(pg) != f"{N} remaining":
        FAIL.append(f"counter read {remaining(pg)!r} after 4x undo, expected '{N} remaining'")
    if rows(pg) != N:
        FAIL.append(f"{rows(pg)} rows after 4x undo, expected {N}")
    if pg.evaluate("() => (DATA.tasks || []).length") != 0:
        FAIL.append("undo left the created task behind")
    if pg.evaluate("() => DATA.notes[0].text") != "<p>existing body</p>":
        FAIL.append("undo did not restore the note body")
    if texts[3] not in pg.evaluate(f"() => DATA.dailyDocs['{date}'].content"):
        FAIL.append("undo did not restore the discarded line to the daily doc")
    if cursor_at(pg) != 0:
        FAIL.append(f"undo left the cursor at {cursor_at(pg)}, expected the recorded row 0")
    if pg.evaluate("() => window.K2Triage ? K2Triage.undo.length : -1") != 0:
        FAIL.append("undo stack not drained")

    # ── control 1: the undo stack is what restores. Empty it, and undo must stop working.
    pg.keyboard.press("s")
    settle(pg, N - 1)
    pg.evaluate("() => { if (window.K2Triage) K2Triage.undo = []; }")
    pg.keyboard.press("u")
    pg.wait_for_timeout(400)
    if rows(pg) != N - 1:
        FAIL.append("CONTROL: the row came back with an empty undo stack — the gate proves nothing")
    pg.evaluate("() => { DATA.staleJotState = {}; }")
    pg.evaluate("() => renderStaleJots()")
    pg.wait_for_timeout(200)

    # ── control 2: strip the cursor marking and require the j/k assertion to fail
    pg.evaluate("""() => {
      window.__realRender = renderStaleJots;
      window.renderStaleJots = function () {
        const r = window.__realRender.apply(this, arguments);
        document.querySelectorAll('[data-triage-cursor]')
          .forEach(e => e.removeAttribute('data-triage-cursor'));
        return r;
      };
    }""")
    pg.keyboard.press("j")
    pg.wait_for_timeout(300)
    if cursor_at(pg) is not None:
        FAIL.append("CONTROL: a cursor survived stripping data-triage-cursor — the gate proves nothing")
    pg.evaluate("() => { window.renderStaleJots = window.__realRender; }")

    # ── exit on Escape, and the global shortcuts work again
    pg.keyboard.press("Escape")
    pg.wait_for_timeout(300)
    if pg.evaluate("() => !!(window.K2Triage && K2Triage.active)"):
        FAIL.append("Escape did not exit triage")
    if bar_shown(pg):
        FAIL.append("triage bar still visible after Escape")
    if cursor_at(pg) is not None:
        FAIL.append("cursor still marked after Escape")

    pg.keyboard.press("d")          # global: Dashboard
    pg.wait_for_timeout(300)
    if active_page(pg) != "dashboard":
        FAIL.append(f"global `d` did not reach the dashboard with triage off (got {active_page(pg)})")
    pg.keyboard.press("j")          # global: Jots
    pg.wait_for_timeout(400)
    if active_page(pg) != "jots":
        FAIL.append(f"global `j` did not reach jots with triage off (got {active_page(pg)})")
    pg.evaluate("() => document.activeElement.blur()")
    pg.evaluate("() => navigateTo('dashboard')")
    pg.wait_for_timeout(200)
    pg.keyboard.press("t")          # global: New task, off the stale-jots page
    pg.wait_for_timeout(300)
    if active_page(pg) != "tasks":
        FAIL.append(f"global `t` did not reach tasks from another page (got {active_page(pg)})")

    # ── control 3: neutralise the enter path; `t` on Stale Jots must fall back to Tasks
    pg.evaluate("() => navigateTo('stale-jots')")
    pg.wait_for_timeout(300)
    pg.evaluate("() => { window.__realStart = window.staleJotsTriageStart; window.staleJotsTriageStart = () => false; }")
    pg.keyboard.press("t")
    pg.wait_for_timeout(400)
    if active_page(pg) == "stale-jots" and pg.evaluate("() => !!(window.K2Triage && K2Triage.active)"):
        FAIL.append("CONTROL: triage started with staleJotsTriageStart() stubbed to false — "
                    "something other than the documented enter path is binding `t`")
    if active_page(pg) != "tasks":
        FAIL.append(f"CONTROL: with the enter path stubbed, `t` should fall through to Tasks "
                    f"(got {active_page(pg)}) — the collision is not resolved where it is documented")
    pg.evaluate("() => { if (window.__realStart) window.staleJotsTriageStart = window.__realStart; }")
    b.close()

    # ── a phone must not be able to enter it, deliberately or by accident
    b, pg = open_app(pw, ui2=True, width=390)
    pg.evaluate(SEED)
    pg.wait_for_timeout(400)
    pg.keyboard.press("t")
    pg.wait_for_timeout(400)
    phone_active = pg.evaluate("() => !!(window.K2Triage && K2Triage.active)")
    if phone_active:
        FAIL.append("triage entered at 390px — a phone has no j/k")
    if pg.evaluate("() => !!(window.staleJotsTriageStart && staleJotsTriageStart())"):
        FAIL.append("staleJotsTriageStart() returned true at 390px even when called directly")
    b.close()
    return N


with sync_playwright() as pw:
    seeded = g12(pw)

if FAIL:
    print("G12 FAIL:")
    for f in FAIL:
        print("  -", f)
    sys.exit(1)

print(f"G12 PASS: `t` on Stale Jots enters triage without the global `t` also firing; j/k move a "
      f"marked cursor over {seeded} rows and scroll it into view without reaching global `j`; "
      f"t/n/s/x each mutate DATA (task created, note body appended with no modal, archive and "
      f"discard recorded, discarded line removed from the daily doc) and the counter falls "
      f"{seeded}->{seeded-4}; four undos restore every one of those plus the cursor; stubbing the "
      f"undo stack, the cursor attribute and staleJotsTriageStart() each control-fail; Escape "
      f"exits and global d/j/t work again; 390px cannot enter")
