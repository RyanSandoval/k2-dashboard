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
DATA_JSON.update({"dailyDocs": {}, "mission": "", "reminderActionsMeta": {
    "appliedIds": ["ra-old"],
    # a failure from days ago must not sit on the banner forever
    "results": {"ra-old": {"status": "failed", "error": "invalid cron.remove params: id not found",
                           "at": "2026-08-01T00:00:00+00:00"}},
}})


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
        # Collapsed rows flag a note rather than dumping it; the body shows on expand.
        if "📝 note" not in html:
            fails.append("collapsed row does not flag that a note exists")
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
        # The form must be submittable with nothing but text — a default time is prefilled.
        prefilled = page.input_value("#rem-at")
        if not prefilled:
            fails.append("date field ships empty, so typing text and tapping Add does nothing")
        page.fill("#rem-text", "ship the reminders page")
        page.click("#rem-note-toggle")
        page.fill("#rem-note", "include the note field")
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

        # A collapsed row must carry NO destructive control — this is the regression that
        # made "edit" look like "delete". Actions live in the expanded panel, labelled.
        page.set_viewport_size({"width": 1280, "height": 1000})
        page.evaluate("() => { _remState.expanded = null; renderReminders(); }")
        collapsed = page.inner_html("#reminders-list")
        if "cancelReminder(" in collapsed:
            fails.append("collapsed row still exposes a delete control")
        if "Delete" in collapsed:
            fails.append("collapsed row still shows a Delete button")

        # Clicking a reminder opens the detail: full note + labelled actions.
        page.evaluate("() => toggleReminderDetail('aaaaaaaa-1111-2222-3333-444444444444')")
        page.wait_for_timeout(200)
        opened = page.inner_html("#reminders-list")
        for want, label in (("book the 6-month cleaning", "full note"),
                            ("🗑 Delete", "delete button"),
                            ("✏️ Edit", "edit button"),
                            ("Posts to #k2-dashboard", "delivery target resolved to a channel name")):
            if want not in opened:
                fails.append(f"expanded detail is missing the {label}")
        page.screenshot(path="/tmp/g5_reminders_detail.png", full_page=False)

        # Undo must actually pull a queued action back out of the queue.
        page.evaluate("() => queueReminderAction({op:'cancel', cronId:'aaaaaaaa-1111-2222-3333-444444444444'})")
        page.wait_for_timeout(200)
        acts = page.evaluate("() => window.DATA.reminderActions || []")
        cancels = [a for a in acts if a.get("op") == "cancel"]
        if len(cancels) != 1:
            fails.append(f"expected 1 queued cancel, got {len(cancels)}")
        else:
            if "undo cancel" not in page.inner_html("#rem-queue-banner"):
                fails.append("queued cancel has no undo control")
            page.evaluate(f"() => undoReminderAction('{cancels[0]['id']}')")
            page.wait_for_timeout(200)
            left = page.evaluate("() => (window.DATA.reminderActions||[]).filter(a=>a.op==='cancel').length")
            if left != 0:
                fails.append("undo did not remove the queued cancel")

        # A failure older than 2h must not still be shouting on the banner.
        banner = page.inner_html("#rem-queue-banner")
        if "id not found" in banner:
            fails.append("a stale failure is still displayed on the banner")

        # ...but a fresh one must be, and must be dismissible.
        page.evaluate("() => { DATA.reminderActionsMeta = {appliedIds:['ra-new'], results:{'ra-new':"
                      "{status:'failed', error:'boom', at:new Date().toISOString()}}}; renderReminders(); }")
        page.wait_for_timeout(150)
        if "boom" not in page.inner_html("#rem-queue-banner"):
            fails.append("a recent failure is not shown")
        page.evaluate("() => dismissReminderFailures()")
        page.wait_for_timeout(150)
        if "boom" in page.inner_html("#rem-queue-banner"):
            fails.append("dismiss did not clear the failure")

        # The push opt-in row must always say something, and must always make clear that
        # Discord keeps posting — push is additive, never a swap.
        row = page.inner_text("#rem-push-row")
        if not row.strip():
            fails.append("push status row is empty")
        if "Discord" not in row:
            fails.append("push row does not say Discord still posts")
        env = page.evaluate("() => _pushEnvironment()")
        if env not in ("ok", "needs-install", "unsupported"):
            fails.append(f"_pushEnvironment returned an unexpected value: {env!r}")

        # the badge must count what is imminent
        badge = page.inner_text("#reminders-badge")
        if badge.strip() not in ("1", "2"):
            fails.append(f"badge shows {badge!r}; expected the imminent one-shot count")

        page.screenshot(path="/tmp/g5_reminders.png", full_page=False)

        # Mobile: the More drawer is a SEPARATE hardcoded list from the desktop sidebar.
        # Adding a sidebar nav-item does not put the page on the phone — this caught that.
        page.set_viewport_size({"width": 390, "height": 844})
        page.evaluate("() => navigateTo('jots')")
        page.evaluate("() => openMobileMore()")
        page.wait_for_timeout(200)
        drawer = page.locator('.mobile-more-item[data-page="reminders"]')
        if drawer.count() == 0:
            fails.append("mobile More drawer has no Reminders entry")
        else:
            drawer.first.click()
            page.wait_for_timeout(400)
            if page.locator("#page-reminders.active").count() == 0:
                fails.append("mobile drawer entry did not navigate to the Reminders page")
            page.screenshot(path="/tmp/g5_reminders_mobile.png", full_page=False)
        if errors:
            fails.append("page errors: " + "; ".join(errors[:3]))
        browser.close()

    if fails:
        print("G5 FAIL:\n  " + "\n  ".join(fails))
        return 1
    print("G5 PASS: reminders render + group + humanize, non-reminders excluded, "
          "create queues a valid action; mobile drawer entry navigates "
          "(screenshots: /tmp/g5_reminders.png, /tmp/g5_reminders_mobile.png)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
