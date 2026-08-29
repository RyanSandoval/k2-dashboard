#!/usr/bin/env python3
"""G3 — load the REAL dashboard with a note containing an agent result, let TipTap parse it
into its schema, then serialize back out. If the node is not registered correctly the editor
drops or mangles it here — which is the failure that would silently eat results the next
time Ryan edits a note."""
import base64, json, sys, time
from playwright.sync_api import sync_playwright

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
RESULT = ('<div class="agent-result" data-type="agentResult" data-req-id="a-req-1"'
          ' data-status="done" data-label="MW-12363"'
          ' data-href="https://vikingtravel.atlassian.net/browse/MW-12363"'
          ' data-meta="Ready for Release · Max Akbar" contenteditable="false">'
          '<span class="agent-result-arrow">↳</span>'
          '<a class="agent-result-label" href="https://vikingtravel.atlassian.net/browse/MW-12363"'
          ' target="_blank" rel="noopener">MW-12363</a>'
          '<span class="agent-result-meta">Ready for Release · Max Akbar</span></div>')
NOTE = ('<ul data-type="taskList"><li data-checked="false" data-type="taskItem">'
        '<label><input type="checkbox"><span></span></label><div><p>Create a ticket for promo cards '
        '<span class="mention-agent" data-type="agentMention" data-req-id="a-req-1">🤖 </span></p>'
        + RESULT + '</div></li></ul><p></p><h2>🌅 End of Day</h2>')

DATA = {"projects": [], "tasks": [], "notes": [], "jots": [], "reminderActions": [], "cronJobs": [],
        "dailyDocs": {"2026-08-28": {"content": NOTE, "updatedAt": "2026-08-28T22:00:00Z"}}}
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
            fails.append("editor never initialised — cannot prove the node round-trips")
        else:
            out = page.evaluate("() => window._todayEditor.getHTML()")
            for label, ok in [
                ("result node survived parse+serialize", 'data-type="agentResult"' in out),
                ("request id preserved", 'data-req-id="a-req-1"' in out),
                ("label preserved", "MW-12363" in out),
                ("href preserved", "vikingtravel.atlassian.net/browse/MW-12363" in out),
                ("meta preserved", "Ready for Release" in out),
                ("exactly one result, not duplicated", out.count('data-type="agentResult"') == 1),
                ("the mention it answers survived", 'data-type="agentMention"' in out),
                ("Ryan's own text survived", "Create a ticket for promo cards" in out),
                ("result stayed inside the task item", out.find("agent-result") < out.find("</li>")),
            ]:
                if not ok:
                    fails.append(label)
            if fails:
                print("serialized output was:\n" + out[:900])
            page.screenshot(path="/tmp/g3_note.png")
        b.close()
    if fails:
        print("G3 FAIL:\n  " + "\n  ".join(fails))
        return 1
    print("G3 PASS: TipTap parses and re-serializes the result node intact, inside its task item")
    return 0


if __name__ == "__main__":
    sys.exit(main())
