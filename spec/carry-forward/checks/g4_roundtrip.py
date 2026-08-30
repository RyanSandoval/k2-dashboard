#!/usr/bin/env python3
"""G4 — the carried block has to survive the real editor. Loads the actual dashboard with
only YESTERDAY's doc present, lets renderJots() create today and carry forward for real,
then reads what TipTap parsed and re-serialized. If the marker paragraph or the task items
do not survive the schema, the carry silently evaporates the first time Ryan types."""
import base64, json, sys, time
from playwright.sync_api import sync_playwright

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
YESTERDAY = "2026-08-29"
PRIOR = ('<ul data-type="taskList">'
         '<li data-checked="false" data-type="taskItem"><div><p>ship the parity harness</p></div></li>'
         '<li data-checked="true" data-type="taskItem"><div><p>already finished this</p></div></li>'
         '<li data-checked="false" data-type="taskItem"><div><p>call the bank about the wire</p>'
         '<ul data-type="taskList"><li data-checked="false" data-type="taskItem">'
         '<div><p>find the account number</p></div></li></ul></div></li>'
         '</ul><p>prose that is not a task and must not travel</p>')

DATA = {"projects": [], "tasks": [], "notes": [], "jots": [], "reminderActions": [], "cronJobs": [],
        "dailyDocs": {YESTERDAY: {"content": PRIOR, "updatedAt": YESTERDAY + "T22:00:00Z"}}}
SNAP = {"jobs": [], "count": 0, "snapshotAtMs": int(time.time() * 1000)}


def b64(o):
    return base64.b64encode(json.dumps(o).encode()).decode()


def main():
    fails = []
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path=CHROME)
        page = b.new_context(viewport={"width": 1280, "height": 900}, bypass_csp=True).new_page()
        page.route("https://api.github.com/**", lambda r: r.fulfill(
            status=200, content_type="application/json",
            body=json.dumps({"sha": "stub",
                             "content": b64(SNAP if "cron-snapshot" in r.request.url else DATA)})))
        page.add_init_script("localStorage.setItem('k2auth','true');localStorage.setItem('gh_token','stub');")
        page.goto("file:///Users/ryansandoval/k2-dashboard/index.html")
        page.wait_for_function("window._dataLoaded === true", timeout=25000)
        page.click('.nav-item[data-page="jots"]')
        try:
            page.wait_for_function("!!window._todayEditor", timeout=25000)
        except Exception:
            pass
        if not page.evaluate("() => !!window._todayEditor"):
            fails.append("editor never initialised — cannot prove the carried block round-trips")
        else:
            out = page.evaluate("() => window._todayEditor.getHTML()")
            stored = page.evaluate("() => DATA.dailyDocs[window._todayEditorDate] || {}")
            src = page.evaluate("() => DATA.dailyDocs['%s'].content" % YESTERDAY)
            for label, ok in [
                ("carry actually ran in the browser", stored.get("carriedFrom") == YESTERDAY),
                ("marker paragraph survived TipTap", "Carried over from" in out),
                ("marker names the source day", "Saturday" in out),
                ("unfinished line 1 survived", "ship the parity harness" in out),
                ("unfinished line 2 survived", "call the bank about the wire" in out),
                ("its nested sub-item came with it", "find the account number" in out),
                ("completed line did NOT travel", "already finished this" not in out),
                ("non-task prose did NOT travel", "prose that is not a task" not in out),
                ("carried items are real task items", out.count('data-type="taskItem"') >= 3),
                ("exactly one marker", out.count("Carried over from") == 1),
                ("marker is plain — no class TipTap would strip on first edit",
                 "carried-from" not in out and "carried-from" not in stored.get("content", "")),
                ("source day left untouched", src == PRIOR),
            ]:
                if not ok:
                    fails.append(label)
            if fails:
                print("serialized output was:\n" + out[:1200])
            page.screenshot(path="/tmp/g4_carry.png")
        b.close()
    if fails:
        print("G4 FAIL:\n  " + "\n  ".join(fails))
        return 1
    print("G4 PASS: the real editor parsed and re-serialized the carried block — marker, both "
          "unfinished lines and the nested sub-item intact, completed line and prose left behind, "
          "source day unchanged")
    return 0


if __name__ == "__main__":
    sys.exit(main())
