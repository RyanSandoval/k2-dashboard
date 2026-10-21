"""G14 — a click on a server-owned row survives saveData()'s rebase into the PUT.

saveData() rebases onto the fresh server copy and, since ad25028 (#86), took every
SERVER_OWNED_KEYS value from the server wholesale. actionInbox is server-owned, so the
dismiss/handled/pin/archive flag the click had just set was overwritten before the payload
was built: "Inbox won't let me cancel or complete tasks — it brings back tasks I deleted."

Everything here is asserted on the captured PUT body, not on in-memory DATA — DATA was
always right for a moment, which is why the bug looked like it worked until a reload.

  1. dismiss → PUT row dismissed === true, while cron content (summary) still comes from
     the server (the #86 guarantee)
  2. restore, with the server holding dismissed=true under an older stamp → PUT row
     dismissed === false (un-setting keys on the stamp, not on a truthy flag)
  3. K2Archive.archive('action', id) → PUT row archived === true
  4. a stale local row (older stamp) cannot un-flag the server, nor push stale content
  5. staleJotState: an archived jot entry reaches the PUT

Controls: replace _mergeUserFlags with the old unconditional `DATA[k] = server[k]`
(1, 2, 3, 5 must fail), and with "local always wins" (4 must fail).
"""
import base64, json, sys
sys.path.insert(0, "/Users/ryansandoval/k2-dashboard/spec/ui-rebuild/checks")
from _boot import open_app, b64
from playwright.sync_api import sync_playwright

FAIL = []
OLD = "2026-01-01T00:00:00.000Z"
SERVER = {}   # what data.json holds; a cron "rewrote" it between every save
PUTS = []


def data_route(route):
    if route.request.method == "PUT":
        body = json.loads(route.request.post_data)
        PUTS.append(json.loads(base64.b64decode(body["content"]).decode("utf-8")))
        route.fulfill(status=200, content_type="application/json",
                      body=json.dumps({"content": {"sha": "put-%d" % len(PUTS)}}))
    else:
        route.fulfill(status=200, content_type="application/json",
                      body=json.dumps({"sha": "srv", "content": b64(SERVER)}))


def row(id_, summary, **flags):
    return dict({"id": id_, "text": "Task " + id_, "summary": summary, "score": 50,
                 "source": "jot", "firstSeenAt": OLD}, **flags)


def setup(pg, server_rows, local_rows, jots=None):
    SERVER.clear()
    SERVER.update({"actionInbox": server_rows, "staleJotState": jots or {}, "notes": []})
    PUTS.clear()
    pg.evaluate("([rows, jots]) => { DATA.actionInbox = rows; DATA.staleJotState = jots; }",
                [local_rows, jots or {}])


def put_row(id_):
    if not PUTS:
        return None
    return next((r for r in PUTS[-1].get("actionInbox", []) if r["id"] == id_), None)


def scenarios(pg):
    """Returns {name: (ok, detail)} for each assertion, so the controls can rerun them."""
    out = {}

    setup(pg, [row("a1", "cron v2")], [row("a1", "stale v1")])
    pg.evaluate("async () => { await actionInboxDismiss('a1'); }")
    r = put_row("a1")
    out["dismiss"] = (bool(r) and r.get("dismissed") is True, r)
    out["content"] = (bool(r) and r.get("summary") == "cron v2", r)

    setup(pg, [row("a1", "cron v2", dismissed=True, dismissedAt=OLD, flagsAt=OLD)],
              [row("a1", "cron v2", dismissed=True, dismissedAt=OLD, flagsAt=OLD)])
    pg.evaluate("async () => { await actionInboxRestore('a1'); }")
    r = put_row("a1")
    out["restore"] = (bool(r) and r.get("dismissed") is False and r.get("dismissedAt") is None, r)

    setup(pg, [row("a2", "cron v2")], [row("a2", "cron v2")])
    pg.evaluate("async () => { await K2Archive.archive('action', 'a2'); }")
    r = put_row("a2")
    out["archive"] = (bool(r) and r.get("archived") is True and bool(r.get("archivedAt")), r)

    # A tab left open since before the dismiss: its row carries the older stamp. Saving
    # anything from it must not un-dismiss the row or push its stale summary.
    setup(pg, [row("a3", "cron v2", dismissed=True, dismissedAt="2026-06-01T00:00:00.000Z",
                   flagsAt="2026-06-01T00:00:00.000Z")],
              [row("a3", "stale v1", dismissed=False, flagsAt=OLD)])
    pg.evaluate("async () => { await saveData(); }")
    r = put_row("a3")
    out["stale"] = (bool(r) and r.get("dismissed") is True and r.get("summary") == "cron v2", r)

    setup(pg, [], [], jots={"2026-09-01::old": {"handledAt": OLD}})
    pg.evaluate("async () => { _staleJotsSetState('2026-09-01::x', { archived: true, action: 'archive' }); await saveData(); }")
    st = PUTS[-1].get("staleJotState", {}) if PUTS else {}
    out["jot"] = (st.get("2026-09-01::x", {}).get("archived") is True and "2026-09-01::old" in st, st)
    return out


def g14(pw):
    b, pg = open_app(pw, ui2=True, width=1440)
    pg.route("https://api.github.com/repos/RyanSandoval/k2-data/contents/data.json", data_route)

    res = scenarios(pg)
    for name, (ok, detail) in res.items():
        if not ok:
            FAIL.append(f"{name}: PUT payload wrong — {detail}")

    if not pg.evaluate("() => typeof _mergeUserFlags === 'function'"):
        FAIL.append("_mergeUserFlags() is not defined — saveData still blind-assigns server-owned keys")
        b.close()
        return res

    # control A: the pre-fix body — DATA[k] = server[k] for every server-owned key
    pg.evaluate("() => { window.__realMerge = _mergeUserFlags; window._mergeUserFlags = (k, l, s) => s; }")
    ctl = scenarios(pg)
    for name in ("dismiss", "restore", "archive", "jot"):
        if ctl[name][0]:
            FAIL.append(f"CONTROL A: '{name}' passed with the old unconditional server[k] rebase — it proves nothing")

    # control B: "local always wins" — the stale tab must then clobber the server
    pg.evaluate("() => { window._mergeUserFlags = (k, l, s) => l; }")
    if scenarios(pg)["stale"][0]:
        FAIL.append("CONTROL B: 'stale' passed with local-always-wins — the #86 guarantee is untested")
    pg.evaluate("() => { window._mergeUserFlags = window.__realMerge; }")

    b.close()
    return res


with sync_playwright() as pw:
    res = g14(pw)

if FAIL:
    print("G14 FAIL:")
    for f in FAIL:
        print("  -", f)
    sys.exit(1)

print("G14 PASS: on the captured PUT body — dismiss sends dismissed=true with the server's summary "
      "('cron v2', not the stale 'stale v1'); restore against a server row holding dismissed=true "
      "under an older stamp sends dismissed=false, dismissedAt=null; K2Archive.archive('action') sends "
      "archived=true with archivedAt; a stale tab (older flagsAt) neither un-dismisses the row nor pushes "
      "its stale summary; an archived staleJotState entry reaches the PUT beside the server's existing one. "
      "Controls: the old unconditional DATA[k]=server[k] rebase fails dismiss, restore, archive and jot; "
      "local-always-wins fails the stale-tab assertion.")
