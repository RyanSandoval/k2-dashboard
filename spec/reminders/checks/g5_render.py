#!/usr/bin/env python3
"""G5 — load the real index.html in a headless browser with a stubbed k2-data,
navigate to Reminders, and assert the page actually renders rows and groups.

Network is stubbed at api.github.com, so this never touches the private repo.
"""
import base64
import json
import sys
from datetime import datetime, timedelta, timezone

from playwright.sync_api import sync_playwright

INDEX = "/Users/ryansandoval/k2-dashboard/index.html"
NOW = datetime.now(timezone.utc)


def iso(delta):
    return (NOW + delta).strftime("%Y-%m-%dT%H:%M:%S.000Z")


CRON_SNAPSHOT = {
    "snapshotAtMs": int(NOW.timestamp() * 1000),
    "count": 4,
    "jobs": [
        {"id": "aaaaaaaa-1111-2222-3333-444444444444", "name": "Reminder — call the dentist",
         "scheduleKind": "at", "scheduleAt": iso(timedelta(hours=3)), "isReminder": True,
         "reminderText": "call the dentist", "reminderOrigin": "asked",
         "reminderSource": "#k2-dashboard", "deliveryTo": "channel:1476441453394919587",
         "reminderNote": "ask about the crown\nand book the 6-month cleaning"},
        {"id": "bbbbbbbb-1111-2222-3333-444444444444", "name": "daily-note-reminder:x:Ai skunkworks",
         "scheduleKind": "at", "scheduleAt": iso(timedelta(days=4)), "isReminder": True,
         "reminderText": "⏰ Reminder from note (2026-06-18): Ai skunkworks",
         "reminderOrigin": "auto-scan", "reminderSource": None},
        {"id": "cccccccc-1111-2222-3333-444444444444", "name": "Reminder — standup",
         "scheduleKind": "cron", "scheduleExpr": "0 9 * * 1-5", "scheduleTz": "America/Los_Angeles",
         "isReminder": True, "reminderText": "standup", "reminderOrigin": "asked"},
        {"id": "dddddddd-1111-2222-3333-444444444444", "name": "K2 Cron Snapshot Writer",
         "scheduleKind": "cron", "scheduleExpr": "*/10 * * * *", "isReminder": False},
    ],
}

DATA_JSON = {k: [] for k in ("projects", "tasks", "notes", "discussions", "decisions",
                             "timeline", "jots", "docs", "reminderActions")}
DATA_JSON.update({"dailyDocs": {}, "reminderActionsMeta": {}, "mission": ""})


def gh_file(payload):
    raw = json.dumps(payload).encode()
    return json.dumps({"sha": "stub", "content": base64.b64encode(raw).decode(), "encoding": "base64"})


def main():
    fails = []
    with sync_playwright() as pw:
        # The bundled headless shell for this playwright build is not installed; use
        # the system Chrome that pa11y already relies on rather than downloading one.
        browser = pw.chromium.launch(
            executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
        # bypass_csp: the page ships a strict script-src with no 'unsafe-eval', which
        # blocks playwright's own evaluate(). It does not change what the page renders.
        ctx = browser.new_context(viewport={"width": 1280, "height": 1000}, bypass_csp=True)
        page = ctx.new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))

        def route(r):
            url = r.request.url
            body = gh_file(CRON_SNAPSHOT) if "cron-snapshot.json" in url else gh_file(DATA_JSON)
            r.fulfill(status=200, content_type="application/json", body=body)

        page.route("https://api.github.com/**", route)
        page.route("https://raw.githubusercontent.com/**",
                   lambda r: r.fulfill(status=200, body=json.dumps(CRON_SNAPSHOT)))
        page.add_init_script(
            "localStorage.setItem('k2auth','true');localStorage.setItem('gh_token','stub');")
        page.goto(f"file://{INDEX}")
        page.wait_for_function("window._dataLoaded === true", timeout=20000)
        page.click('.nav-item[data-page="reminders"]')
        page.wait_for_selector("#page-reminders.active", timeout=5000)
        page.wait_for_timeout(400)

        html = page.inner_html("#reminders-list")
        if "call the dentist" not in html:
            fails.append("asked one-shot reminder is missing from the list")
        if "Ai skunkworks" not in html:
            fails.append("auto-scanned reminder is missing from the list")
        if "Reminder from note" in html:
            fails.append("scanner boilerplate prefix was not stripped from the reminder text")
        if "from note" not in html:
            fails.append("auto-scan origin chip is missing")
        if "book the 6-month cleaning" not in html:
            fails.append("reminder note is not rendered on the row")
        if "weekdays at 9:00am" not in html:
            fails.append("recurring cron was not humanized ('weekdays at 9:00am')")
        if "Cron Snapshot Writer" in html:
            fails.append("a non-reminder cron leaked into the Reminders list")
        for group in ("Today", "Recurring"):
            if f">{group} <" not in html:
                fails.append(f"missing group header: {group}")

        # the create form must be usable
        for sel in ("#rem-text", "#rem-at", "#rem-channel", "#rem-repeat"):
            if page.locator(sel).count() == 0:
                fails.append(f"create form is missing {sel}")

        # queueing a reminder must produce a validly-shaped action
        page.fill("#rem-text", "ship the reminders page")
        page.click("#rem-note-toggle")
        page.fill("#rem-note", "include the note field")
        page.evaluate(
            "() => { const d=new Date(Date.now()+7200000);"
            "document.getElementById('rem-at').value = d.getFullYear()+'-'+"
            "String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0')+'T'+"
            "String(d.getHours()).padStart(2,'0')+':'+String(d.getMinutes()).padStart(2,'0'); }")
        page.click("button:has-text('Add reminder')")
        page.wait_for_timeout(300)
        queued = page.evaluate("() => window.DATA.reminderActions || []")
        if len(queued) != 1:
            fails.append(f"expected 1 queued action, got {len(queued)}")
        else:
            a = queued[0]
            for field, want in (("op", "create"), ("kind", "at"), ("text", "ship the reminders page"),
                                ("note", "include the note field")):
                if a.get(field) != want:
                    fails.append(f"queued action {field}={a.get(field)!r}, want {want!r}")
            if not str(a.get("id", "")).startswith("ra-"):
                fails.append(f"queued action has a bad id: {a.get('id')!r}")
            if not str(a.get("target", "")).startswith("channel:"):
                fails.append(f"queued action has a bad target: {a.get('target')!r}")
        if "queued" not in page.inner_html("#reminders-list"):
            fails.append("queued create did not render as a pending row")

        # the badge must count what is imminent
        badge = page.inner_text("#reminders-badge")
        if badge.strip() not in ("1", "2"):
            fails.append(f"badge shows {badge!r}; expected the imminent one-shot count")

        page.screenshot(path="/tmp/g5_reminders.png", full_page=False)
        if errors:
            fails.append("page errors: " + "; ".join(errors[:3]))
        browser.close()

    if fails:
        print("G5 FAIL:\n  " + "\n  ".join(fails))
        return 1
    print("G5 PASS: reminders render + group + humanize, non-reminders excluded, "
          "create queues a valid action (screenshot: /tmp/g5_reminders.png)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
