#!/usr/bin/env python3
"""G9 — adding a task to today puts it beside the others, not inside them.

Ryan: "when I add something it just nests everything under another item." It did.
homePickToNote used chain().focus('end'), and the end of the DOCUMENT is inside the last
task item's paragraph, so each insert landed one level deeper than the last. Three adds
produced three levels of hierarchy he never expressed — and carry-forward treats an
unchecked parent's children as travelling with it, so the whole stack would move as one
blob."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from _boot import SNAP, b64, CHROME
from playwright.sync_api import sync_playwright

DATA = {"projects": [], "notes": [], "jots": [], "reminderActions": [], "cronJobs": [],
        "dailyDocs": {},
        "tasks": [{"id": f"t{i}", "text": f"task number {i}", "done": False,
                   "created": "2026-07-01", "status": "open"} for i in range(1, 5)]}

SHAPE = r"""
() => {
  // li[data-checked], not li[data-checked]: TaskItem renders through a nodeView,
  // so data-type exists only in getHTML() serialisation and never in the live DOM. The
  // obvious selector silently matches nothing and every count reads 0.
  const q = s => document.querySelectorAll('#page-jots .ProseMirror ' + s);
  let max = 0;
  q('li[data-checked]').forEach(li => {
    let d = 0, n = li.parentElement;
    while (n) { if (n.matches && n.matches('li[data-checked]')) d++; n = n.parentElement; }
    max = Math.max(max, d);
  });
  const ids = [...q('li[data-checked]')].map(li => li.getAttribute('data-task-id'));
  return { items: q('li[data-checked]').length,
           lists: q('ul[data-type=taskList]').length, maxNesting: max, ids };
}
"""

def main():
    fails = []
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path=CHROME)
        pg = b.new_context(viewport={"width": 1440, "height": 900}, color_scheme="dark",
                           bypass_csp=True).new_page()
        pg.route("https://api.github.com/**", lambda r: r.fulfill(
            status=200, content_type="application/json",
            body=json.dumps({"sha": "stub",
                             "content": b64(SNAP if "cron-snapshot" in r.request.url else DATA)})))
        pg.add_init_script("localStorage.setItem('k2auth','true');localStorage.setItem('gh_token','stub');"
                           "localStorage.setItem('k2.ui2','1');")
        pg.goto("file:///Users/ryansandoval/k2-dashboard/index.html")
        pg.wait_for_function("window._dataLoaded === true", timeout=30000)
        pg.click('.nav-item[data-page="jots"]'); pg.wait_for_timeout(1200)

        for i in range(1, 5):
            pg.evaluate("(id)=>homePickToNote(id)", f"t{i}"); pg.wait_for_timeout(300)
        a = pg.evaluate(SHAPE)
        if a["items"] != 4:
            fails.append(f'4 adds produced {a["items"]} items')
        if a["maxNesting"] != 0:
            fails.append(f'items nested {a["maxNesting"]} deep — they must be siblings')
        if a["lists"] != 1:
            fails.append(f'{a["lists"]} task lists — consecutive adds should build one flat list')
        if len(set(a["ids"])) != len([i for i in a["ids"] if i]):
            fails.append(f'duplicate task ids after adding: {a["ids"]}')

        # typing Enter must give a sibling that belongs to no task
        pg.evaluate("() => window._todayEditor.commands.focus('end')")
        pg.keyboard.press("Enter"); pg.keyboard.type("typed line"); pg.wait_for_timeout(300)
        c = pg.evaluate(SHAPE)
        if c["maxNesting"] != 0:
            fails.append(f'typing Enter nested {c["maxNesting"]} deep')
        if c["items"] != 5:
            fails.append(f'Enter produced {c["items"]} items, expected 5')
        linked = [i for i in c["ids"] if i]
        if len(linked) != len(set(linked)):
            fails.append(f'a typed line inherited another task id: {c["ids"]} — ticking it would close the wrong task')
        if len(linked) != 4:
            fails.append(f'{len(linked)} items carry a task id, expected the 4 that were added')

        # dedupe still works: re-adding an existing task must not add a second copy
        pg.evaluate("(id)=>homePickToNote(id)", "t2"); pg.wait_for_timeout(300)
        d = pg.evaluate(SHAPE)
        if d["items"] != c["items"]:
            fails.append(f're-adding t2 created a duplicate ({c["items"]} -> {d["items"]})')
        b.close()

    if fails:
        print("G9 FAIL:\n  " + "\n  ".join(fails)); return 1
    print(f'G9 PASS: 4 adds give 4 sibling items in 1 flat list at nesting depth 0; '
          f'Enter adds a 5th that carries no task id (so it cannot close another task); '
          f're-adding an existing task still de-dupes')
    return 0

if __name__ == "__main__":
    sys.exit(main())
