"""Boots the real dashboard with stubbed GitHub responses. Shared by the ui-rebuild gates."""
import base64, json, time
DATA = {"projects": [], "tasks": [], "notes": [], "jots": [], "reminderActions": [],
        "cronJobs": [], "dailyDocs": {"2026-08-29": {"content":
            '<ul data-type="taskList"><li data-checked="false" data-type="taskItem">'
            '<div><p>carried line</p></div></li></ul>'}}}
SNAP = {"jobs": [], "count": 0, "snapshotAtMs": int(time.time() * 1000)}
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

def b64(o): return base64.b64encode(json.dumps(o).encode()).decode()

def open_app(pw, ui2=True, scheme="dark", width=1440):
    b = pw.chromium.launch(executable_path=CHROME)
    ctx = b.new_context(viewport={"width": width, "height": 900}, color_scheme=scheme, bypass_csp=True)
    pg = ctx.new_page()
    pg.route("https://api.github.com/**", lambda r: r.fulfill(
        status=200, content_type="application/json",
        body=json.dumps({"sha": "stub",
                         "content": b64(SNAP if "cron-snapshot" in r.request.url else DATA)})))
    # ui2=None leaves the key unset, which is the only way to test what a device that has
    # never touched the setting actually loads — the state every new browser starts in.
    pref = "" if ui2 is None else f"localStorage.setItem('k2.ui2','{'1' if ui2 else '0'}');"
    pg.add_init_script("localStorage.setItem('k2auth','true');localStorage.setItem('gh_token','stub');" + pref)
    pg.goto("file:///Users/ryansandoval/k2-dashboard/index.html")
    pg.wait_for_function("window._dataLoaded === true", timeout=30000)
    pg.wait_for_timeout(900)
    return b, pg
