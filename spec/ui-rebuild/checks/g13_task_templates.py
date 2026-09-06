"""G13 — Reusable Task Templates: detection threshold, and spawning through the real path.

Four things can break here and none of them are visible from "the strip renders":

  1. The threshold. "Repeats 3+ times" is the whole product claim. At two repeats the
     strip must stay silent, and the same seed at three must speak. Both are asserted.
  2. The plan-sync decoy. ~610 rows in the live store carry `sourcePlanFile` and share a
     project; they look like one enormous perfectly-repeating sequence. The gate seeds
     610 of them and requires zero suggestions from them.
  3. Spawning has to make REAL tasks — same shape as addTask(), pushed into DATA.tasks,
     open, on the right project. Asserted against DATA, not against the rendered list.
  4. Ids. addTask() uses Date.now(), which is unique when a human types one task at a
     time and collides for every step of a template spawned inside one millisecond.

Four controls are built in: drop a run, mark the seed as plan-sync, restore Date.now()
ids, and empty the store. Each must fail the matching assertion.
"""
import sys
sys.path.insert(0, "/Users/ryansandoval/k2-dashboard/spec/ui-rebuild/checks")
from _boot import open_app
from playwright.sync_api import sync_playwright

FAIL = []
STEPS = ["Draft release notes", "QA the staging build", "Tag and publish", "Email the changelog"]

# Three runs of the same four steps, a month apart, plus 610 plan-sync rows that share a
# project and a completion date — the shape the live store actually contains.
SEED = """(runs) => {
  const steps = %s;
  const tasks = [];
  let id = 9000;
  ['2026-01-05', '2026-02-05', '2026-03-05'].slice(0, runs).forEach(d => {
    steps.forEach((t, si) => tasks.push({ id: id++, text: t, project: 'proj-x', owner: 'ryan',
      done: true, completedAt: d + 'T0' + si + ':00:00.000Z', urgency: 2, importance: 2 }));
  });
  for (let i = 0; i < 610; i++) tasks.push({ id: id++, text: 'Plan step ' + (i %% 4),
    project: 'proj-planned', owner: 'ryan', done: true, sourcePlanFile: 'plans/roadmap.md',
    completedAt: '2026-04-0' + (1 + (i %% 3)) + 'T00:00:00.000Z', urgency: 2, importance: 2 });
  DATA.tasks = tasks;
  DATA.taskTemplates = [];
  window.prompt = () => 'Release prep';
  window.confirm = () => true;
  navigateTo('tasks');
  renderTasks();
}""" % STEPS


def suggestion(pg):
    return pg.evaluate("""() => {
      const e = document.getElementById('task-template-suggestion');
      return e ? e.textContent.trim() : null;
    }""")


def chips(pg):
    return pg.eval_on_selector_all(
        "#task-templates-strip button[onclick^='spawnTaskTemplate']", "e => e.map(x => x.textContent.trim())")


def strip_shown(pg):
    return pg.evaluate("""() => {
      const e = document.getElementById('task-templates-strip');
      return !!e && getComputedStyle(e).display !== 'none';
    }""")


def open_tasks(pg):
    return pg.evaluate("() => DATA.tasks.filter(t => !t.done).map(t => t.text)")


def reseed(pg, runs):
    pg.evaluate(SEED, runs)
    pg.wait_for_timeout(300)


def g13(pw):
    b, pg = open_app(pw, ui2=True, width=1440)

    if not pg.evaluate("() => typeof detectTaskTemplates === 'function'"):
        FAIL.append("detectTaskTemplates() is not defined — the feature is absent")
        b.close()
        return

    # ── the live store must not be fooled by anything: with two runs, silence
    reseed(pg, 2)
    if suggestion(pg) is not None:
        FAIL.append(f"a suggestion appeared at TWO repeats: {suggestion(pg)!r} — the 3+ threshold is not enforced")
    if strip_shown(pg):
        FAIL.append("the templates strip was visible with nothing saved and nothing suggested")
    # control 1 lives here: the 610 plan-sync rows are present in this seed too
    if pg.evaluate("() => detectTaskTemplates(DATA.tasks).length") != 0:
        FAIL.append("CONTROL: 610 plan-sync rows produced a pattern — the sourcePlanFile "
                    "exclusion is not doing the work the gate credits it for")

    # ── three runs: the suggestion appears, naming the count
    reseed(pg, 3)
    sug = suggestion(pg)
    if sug is None:
        FAIL.append("no suggestion at THREE repeats — detection does not fire")
    else:
        if f"{len(STEPS)} steps" not in sug:
            FAIL.append(f"suggestion did not name {len(STEPS)} steps: {sug!r}")
        if "3 times" not in sug:
            FAIL.append(f"suggestion did not name 3 repeats: {sug!r}")
    if not strip_shown(pg):
        FAIL.append("strip hidden while a suggestion exists")
    found = pg.evaluate("() => detectTaskTemplates(DATA.tasks)")
    if len(found) != 1:
        FAIL.append(f"{len(found)} patterns detected, expected exactly 1 (plan-sync rows leaking in?)")
    elif found[0]["project"] != "proj-x" or found[0]["steps"] != STEPS:
        FAIL.append(f"pattern is {found[0]['project']}/{found[0]['steps']}, expected proj-x/{STEPS} "
                    "— steps must be in completion order")

    # ── control 2: mark the seeded rows as plan-sync and the same data must go quiet
    pg.evaluate("() => DATA.tasks.forEach(t => { if (t.project === 'proj-x') t.sourcePlanFile = 'plans/x.md'; })")
    if pg.evaluate("() => detectTaskTemplates(DATA.tasks).length") != 0:
        FAIL.append("CONTROL: the pattern survived being marked sourcePlanFile — plan-sync rows are not excluded")
    pg.evaluate("() => DATA.tasks.forEach(t => { if (t.project === 'proj-x') delete t.sourcePlanFile; })")
    pg.evaluate("() => renderTasks()")
    pg.wait_for_timeout(200)

    # ── save it
    pg.click("#task-template-suggestion button")
    pg.wait_for_timeout(600)
    tpl = pg.evaluate("() => (DATA.taskTemplates || []).filter(t => !t.dismissed)")
    if len(tpl) != 1:
        FAIL.append(f"{len(tpl)} templates in DATA.taskTemplates after saving, expected 1")
    elif tpl[0]["steps"] != STEPS or tpl[0]["project"] != "proj-x" or tpl[0]["name"] != "Release prep":
        FAIL.append(f"saved template is wrong: {tpl[0]}")
    if suggestion(pg) is not None:
        FAIL.append("the suggestion is still offered after being saved — it will nag forever")
    if chips(pg) != ["📋 Release prep 4"]:
        FAIL.append(f"chips after saving: {chips(pg)}, expected one 'Release prep 4'")

    # ── spawn: one tap makes the whole checklist as real, open tasks
    before = pg.evaluate("() => DATA.tasks.length")
    pg.click("#task-templates-strip button[onclick^='spawnTaskTemplate']")
    pg.wait_for_timeout(800)
    if pg.evaluate("() => DATA.tasks.length") != before + len(STEPS):
        FAIL.append(f"spawn added {pg.evaluate('() => DATA.tasks.length') - before} tasks, expected {len(STEPS)}")
    spawned = pg.evaluate("() => DATA.tasks.filter(t => !t.done)")
    if [t["text"] for t in spawned] != STEPS:
        FAIL.append(f"spawned tasks are {[t['text'] for t in spawned]}, expected {STEPS}")
    for t in spawned:
        if t.get("project") != "proj-x":
            FAIL.append(f"spawned task {t['text']!r} landed on project {t.get('project')!r}, expected proj-x")
        for field in ("id", "urgency", "importance", "priority", "owner", "created", "messages"):
            if field not in t:
                FAIL.append(f"spawned task {t['text']!r} is missing {field} — it did not come from makeTask()")
                break
    ids = [t["id"] for t in spawned]
    if len(set(ids)) != len(ids):
        FAIL.append(f"spawned tasks share ids {ids} — every step is the same row to anything keyed by id")
    if open_tasks(pg) != STEPS:
        FAIL.append(f"open task list is {open_tasks(pg)}, expected {STEPS}")
    # The board files new tasks under a collapsed Backlog section, so expand it before
    # asking whether they rendered — a closed section holds no task text at all.
    pg.evaluate("() => toggleFocusSection('backlog')")
    pg.wait_for_timeout(400)
    rendered = pg.eval_on_selector("#focus-board", "e => e.textContent")
    missing = [s for s in STEPS if s not in rendered]
    if missing:
        FAIL.append(f"spawned tasks are in DATA but the Tasks board did not render {missing}")

    # ── control 3: makeTask()'s bare Date.now() id must collide across a batch, or the
    # +i offset in spawnTaskTemplate() is decoration and the uniqueness assertion above
    # proves nothing. Called directly rather than stubbed — no production code to restore.
    collided = pg.evaluate(f"""() => {{
      const ids = Array.from({{length: {len(STEPS)}}}, () => makeTask('x', 'proj-x', 2, 2).id);
      return new Set(ids).size < ids.length;
    }}""")
    if not collided:
        FAIL.append(f"CONTROL: {len(STEPS)} bare makeTask() calls produced distinct ids — the "
                    "gate's id assertion proves nothing on this machine")
    reseed(pg, 3)

    # ── dismiss suppresses the same signature without saving a template
    pg.click("#task-template-suggestion button:nth-of-type(2)")
    pg.wait_for_timeout(600)
    if suggestion(pg) is not None:
        FAIL.append("dismiss did not suppress the suggestion")
    if chips(pg):
        FAIL.append(f"dismiss created a usable template chip: {chips(pg)}")
    if len(pg.evaluate("() => (DATA.taskTemplates || []).filter(t => t.dismissed)")) != 1:
        FAIL.append("dismiss did not record a dismissal row in DATA.taskTemplates")
    if strip_shown(pg):
        FAIL.append("strip still visible with nothing saved and the only suggestion dismissed")

    # ── control 4: empty the store and the dismissal must stop suppressing
    pg.evaluate("() => { DATA.taskTemplates = []; renderTaskTemplates(); }")
    pg.wait_for_timeout(300)
    if suggestion(pg) is None:
        FAIL.append("CONTROL: the suggestion stayed hidden with DATA.taskTemplates emptied — "
                    "something other than the store is suppressing it")

    b.close()


with sync_playwright() as pw:
    g13(pw)

if FAIL:
    print("G13 FAIL:")
    for f in FAIL:
        print("  -", f)
    sys.exit(1)

print(f"G13 PASS: {len(STEPS)} steps repeated twice raise nothing and a third repeat raises exactly one "
      f"suggestion naming both counts, with 610 sourcePlanFile rows in the same store contributing zero; "
      f"saving writes one DATA.taskTemplates row and retires the suggestion; one tap on the chip pushes "
      f"{len(STEPS)} open tasks onto proj-x with makeTask()'s full shape and {len(STEPS)} distinct ids, and "
      f"the board renders them; dismiss suppresses by signature without leaving a usable chip. Controls: "
      f"dropping a run, marking the seed sourcePlanFile, restoring Date.now() ids and emptying the store "
      f"each fail their assertion.")
