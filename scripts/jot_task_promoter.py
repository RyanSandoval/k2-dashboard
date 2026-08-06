#!/usr/bin/env python3
"""jot_task_promoter.py — promote important tasks/reminders written in the daily
jot into real DATA.tasks so Ryan can check them off in the Tasks view.

Ryan writes work into two places that AREN'T the task list:
  1. Daily docs (dailyDocs[date].content) as checkbox taskItems — deliberate tasks.
  2. Quick jots (jots[]) — freeform capture, sometimes a task/reminder.

Those get lost because they never become completable tasks. This script scans
both, promotes the ones that are actually actionable, and merges them into
DATA.tasks via k2_data_set.py. Fully deterministic (no LLM) so re-runs are
idempotent and manual completions stick.

Promotion rules:
  daily-doc taskItem  -> promote if UNCHECKED on first sight. If it was already
                         checked before we ever saw it, skip (no dead done-tasks).
  jot                 -> promote only with a clear task signal (leading "[]", or
                         a reminder/todo keyword). Skips "love it" style noise.

Merge (per stable jotKey = sha1(sourceType:sourceDate:normText)[:16]):
  key not in tasks         -> append {done:false, source:"jot-promoted", jotKey,...}
  key in tasks, task done   -> left as-is (manual completion is sticky)
  key in tasks, box checked -> task marked done (checking the doc box completes it)
  key in tasks, still open   -> text refreshed, stays open

done is MONOTONIC: done = existing_task.done OR source_box_checked. A task
completed in the Tasks UI is never reopened just because the doc box is still
unchecked.

Usage:
  python3 jot_task_promoter.py [--base data.json] [--look-back-days 30] \
      [--out-tasks /tmp/jot-tasks.json] [--out-meta /tmp/jot-meta.json] \
      [--write] [--message "..."] [--now-ms N] [--today YYYY-MM-DD]
  python3 jot_task_promoter.py --selftest
"""
import argparse
import base64
import datetime as dt
import hashlib
import json
import re
import subprocess
import sys
import time
from html.parser import HTMLParser

REPO = "RyanSandoval/k2-data"
PATH = "data.json"
SOURCE = "jot-promoted"

# jots whose text matches a task/reminder signal (freeform capture is noisy)
_JOT_SIGNAL = re.compile(
    r"(^\s*\[\s*\]"                       # leading "[]" checkbox convention
    r"|\bremind\b|\breminder\b|\btodo\b|\bto-do\b|\bfollow[\s-]?up\b"
    r"|\bdon'?t forget\b|\bneed to\b|\bhave to\b|\bmust\b|\bdeadline\b"
    r"|\bdue\b|\bby (?:mon|tue|wed|thu|fri|sat|sun|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec))",
    re.IGNORECASE,
)
_HIGH = re.compile(r"\b(urgent|asap|important|critical)\b|!", re.IGNORECASE)


# ---------- HTML: pull checkbox taskItems out of a daily doc ----------

class CheckboxExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self._in_item = False
        self._in_div = 0
        self._checked = False
        self._buf = []
        self.items = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "li" and a.get("data-type") == "taskItem":
            self._in_item = True
            self._checked = a.get("data-checked", "false") == "true"
            self._buf = []
            self._in_div = 0
        elif self._in_item and tag == "div":
            self._in_div += 1
        elif self._in_item and tag == "a" and a.get("href"):
            self._buf.append(a["href"])

    def handle_data(self, data):
        if self._in_item and self._in_div > 0:
            self._buf.append(data)

    def handle_endtag(self, tag):
        if tag == "li" and self._in_item:
            self.items.append({"text": "".join(self._buf).strip(),
                               "checked": self._checked})
            self._in_item = False
        elif self._in_item and tag == "div":
            self._in_div = max(0, self._in_div - 1)


def extract_checkboxes(html):
    p = CheckboxExtractor()
    try:
        p.feed(html or "")
    except Exception:
        pass
    return [i for i in p.items if i["text"]]


# ---------- keying ----------

def normalize(s):
    s = (s or "").lower()
    s = re.sub(r"^\s*\[\s*\]", "", s)          # drop leading "[]"
    s = re.sub(r"https?://\S+", "", s)          # urls are unstable -> ignore in key
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return " ".join(s.split())


def jot_key(source_type, source_date, text):
    raw = f"{source_type}:{source_date}:{normalize(text)}"
    return hashlib.sha1(raw.encode()).hexdigest()[:16]


def clean_text(text):
    return re.sub(r"^\s*\[\s*\]\s*", "", (text or "").strip())


def priority_for(text):
    return "high" if _HIGH.search(text or "") else "medium"


# ---------- candidate collection ----------

def collect_candidates(data, today, look_back_days):
    """Return list of {sourceType, sourceDate, text, checked}. Only actionable items."""
    out = []
    cutoff = today - dt.timedelta(days=look_back_days)

    daily = data.get("dailyDocs") or {}
    for date_str, doc in daily.items():
        try:
            d = dt.date.fromisoformat(date_str[:10])
        except (ValueError, TypeError):
            continue
        if d < cutoff:
            continue
        html = doc.get("content") if isinstance(doc, dict) else doc
        for item in extract_checkboxes(html):
            out.append({"sourceType": "daily-doc", "sourceDate": date_str[:10],
                        "text": item["text"], "checked": item["checked"]})

    for jot in (data.get("jots") or []):
        text = (jot.get("text") or "").strip()
        if not text or not _JOT_SIGNAL.search(text):
            continue
        date_str = (jot.get("date") or today.isoformat())[:10]
        try:
            if dt.date.fromisoformat(date_str) < cutoff:
                continue
        except ValueError:
            pass
        out.append({"sourceType": "jot", "sourceDate": date_str,
                    "text": text, "checked": bool(jot.get("done"))})
    return out


# ---------- merge ----------

def merge(base_tasks, candidates, now_ms, today):
    by_key = {t["jotKey"]: t for t in base_tasks if t.get("jotKey")}
    stats = {"scanned": len(candidates), "new": 0, "completed": 0,
             "refreshed": 0, "skipped_done": 0, "skipped_prechecked": 0}
    seq = 0
    for c in candidates:
        key = jot_key(c["sourceType"], c["sourceDate"], c["text"])
        text = clean_text(c["text"])
        if key in by_key:
            t = by_key[key]
            if t.get("done"):
                stats["skipped_done"] += 1
                continue
            if c["checked"]:                       # box got checked in the doc
                t["done"] = True
                t["completedAt"] = today
                stats["completed"] += 1
            else:
                t["text"] = text
                t["priority"] = priority_for(text)
                stats["refreshed"] += 1
            t["lastSeen"] = today
        else:
            if c["checked"]:                       # already-done, never promoted -> skip
                stats["skipped_prechecked"] += 1
                continue
            seq += 1
            base_tasks.append({
                "id": now_ms + seq,
                "text": text,
                "priority": priority_for(text),
                "done": False,
                "created": today,
                "source": SOURCE,
                "jotKey": key,
                "jotSource": c["sourceType"],
                "jotDate": c["sourceDate"],
                "firstSeen": today,
                "lastSeen": today,
            })
            by_key[key] = base_tasks[-1]
            stats["new"] += 1
    return base_tasks, stats


# ---------- io ----------

def fetch_base():
    r = subprocess.run(["gh", "api", f"repos/{REPO}/contents/{PATH}", "--jq", ".content"],
                       capture_output=True)
    if r.returncode != 0:
        sys.exit(f"jot_task_promoter ERROR: fetch failed: {r.stderr.decode()[:300]}")
    return json.loads(base64.b64decode(r.stdout.decode()))


def run(args):
    base = json.load(open(args.base)) if args.base else fetch_base()
    today = dt.date.fromisoformat(args.today) if args.today else dt.date.today()
    now_ms = args.now_ms or int(time.time() * 1000)
    cands = collect_candidates(base, today, args.look_back_days)
    tasks = base.get("tasks", [])
    merged, stats = merge(tasks, cands, now_ms, today.isoformat())
    meta = {"lastScanAt": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "lastRun": stats}
    json.dump(merged, open(args.out_tasks, "w"), ensure_ascii=False, indent=0)
    json.dump(meta, open(args.out_meta, "w"), ensure_ascii=False, indent=0)
    print(json.dumps(stats))
    if args.write:
        cmd = ["python3", args.writer,
               "--set", f"tasks={args.out_tasks}",
               "--set", f"jotPromoterMeta={args.out_meta}",
               "--message", args.message or f"Jot->task promote {today.isoformat()}"]
        if subprocess.run(cmd).returncode != 0:
            sys.exit("jot_task_promoter ERROR: writer failed")
    else:
        print(f"(dry) wrote {args.out_tasks} / {args.out_meta}; pass --write to persist",
              file=sys.stderr)


# ---------- selftest ----------

def selftest():
    today = "2026-07-26"
    doc_html = ('<ul data-type="taskList">'
                '<li data-checked="false" data-type="taskItem"><label><input type="checkbox">'
                '<span></span></label><div><p>ISO formatting for all forms</p></div></li>'
                '<li data-checked="true" data-type="taskItem"><label><input type="checkbox">'
                '<span></span></label><div><p>already finished thing</p></div></li></ul>')
    base = {
        "dailyDocs": {"2026-07-25": {"content": doc_html}},
        "jots": [
            {"text": "[] follow up with Ganges email", "date": "2026-07-24", "done": False},
            {"text": "love it", "date": "2026-07-24", "done": False},
            {"text": "remind me to renew the cert", "date": "2026-07-24", "done": False},
        ],
        "tasks": [{"id": 1, "text": "unrelated", "done": False, "source": "manual"}],
    }
    import copy
    t = dt.date.fromisoformat(today)

    c1 = collect_candidates(copy.deepcopy(base), t, 30)
    # 2 daily-doc items + 2 signal jots ("love it" excluded)
    assert len(c1) == 4, [x["text"] for x in c1]

    m1, s1 = merge(copy.deepcopy(base)["tasks"], c1, 1785000000000, today)
    # promoted: unchecked doc item + 2 jots = 3 new; prechecked doc item skipped
    assert s1["new"] == 3 and s1["skipped_prechecked"] == 1, s1
    promoted = [x for x in m1 if x.get("jotKey")]
    assert all(x["source"] == SOURCE and x["done"] is False for x in promoted)

    # idempotency
    c2 = collect_candidates(copy.deepcopy(base), t, 30)
    m2, s2 = merge(copy.deepcopy(m1), c2, 1785000009999, today)
    assert s2["new"] == 0 and s2["skipped_prechecked"] == 1, s2
    assert len([x for x in m2 if x.get("jotKey")]) == 3, "no dupes"

    # checking the box in the doc completes the task
    base_checked = copy.deepcopy(base)
    base_checked["dailyDocs"]["2026-07-25"]["content"] = doc_html.replace(
        'data-checked="false"', 'data-checked="true"', 1)
    c3 = collect_candidates(base_checked, t, 30)
    m3, s3 = merge(copy.deepcopy(m2), c3, 1785000019999, today)
    assert s3["completed"] == 1, s3
    iso = next(x for x in m3 if x["text"] == "ISO formatting for all forms")
    assert iso["done"] is True and iso.get("completedAt") == today

    # manual completion in Tasks UI is sticky even if doc box stays unchecked
    m4 = copy.deepcopy(m2)
    jt = next(x for x in m4 if x.get("jotKey"))
    jt["done"] = True
    c4 = collect_candidates(copy.deepcopy(base), t, 30)  # doc box still unchecked
    m5, s5 = merge(m4, c4, 1785000029999, today)
    assert s5["skipped_done"] >= 1
    assert next(x for x in m5 if x.get("jotKey") == jt["jotKey"])["done"] is True

    # key stability: url change / [] prefix don't change the key
    k_a = jot_key("jot", "2026-07-24", "[] follow up with Ganges email http://x/1")
    k_b = jot_key("jot", "2026-07-24", "follow up with Ganges email http://x/2")
    assert k_a == k_b, "url + [] must not affect key"
    print("selftest OK")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", help="data.json path; omit to fetch live via gh")
    ap.add_argument("--look-back-days", dest="look_back_days", type=int, default=30)
    ap.add_argument("--out-tasks", dest="out_tasks", default="/tmp/jot-tasks.json")
    ap.add_argument("--out-meta", dest="out_meta", default="/tmp/jot-meta.json")
    ap.add_argument("--writer",
                    default="/Users/ryansandoval/.openclaw/workspace/scripts/k2_data_set.py")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--message")
    ap.add_argument("--now-ms", dest="now_ms", type=int)
    ap.add_argument("--today")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        selftest(); return
    run(args)


if __name__ == "__main__":
    main()
