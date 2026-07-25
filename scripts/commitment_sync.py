#!/usr/bin/env python3
"""commitment_sync.py — deterministic merge of enriched commitments into DATA.tasks.

The LLM half of the weekly scan does recall + enrichment and emits a JSON list of
commitments. This script does the FRAGILE part deterministically (no LLM): compute a
stable commitmentKey, dedupe against the live task list, merge new/updated commitment-
tasks, and write via k2_data_set.py. Keeping this out of the model is what makes
re-runs idempotent (REQ-004) and manual check-offs sticky.

Input commitment shape (list of objects):
  {initiative, commitment, who, specifics, when, nextAction,
   confidence: high|medium|low, sourceLayer: goldfish|pieces-voice|pieces-summary,
   evidence, unanchored?: bool, tickets?: [str], emailSubject?: str}

Merge rules (per commitmentKey):
  unanchored          -> skipped (never written as a task; REQ-002)
  key not in tasks    -> append new task {done:false, source:"commitment", ...}
  key in tasks, done  -> left as-is (respect manual completion; REQ-004)
  key in tasks, open  -> fields refreshed, id/created/done/firstSeen preserved

Discriminator for commitment-tasks is presence of `commitmentKey` (0 collisions on
live data; `source` is already used for jot/plan-sync/etc).

Usage:
  python3 commitment_sync.py --commitments /tmp/enriched.json [--base data.json] \
      [--out-tasks /tmp/commit-tasks.json] [--out-meta /tmp/commit-meta.json] \
      [--write] [--message "..."] [--now-ms N]
  python3 commitment_sync.py --selftest
"""
import argparse
import base64
import hashlib
import json
import re
import subprocess
import sys
import time

REPO = "RyanSandoval/k2-data"
PATH = "data.json"
_STOP = {"the", "a", "an", "to", "for", "of", "and", "on", "in", "with", "at",
         "by", "is", "are", "be", "this", "that", "your", "you", "i", "we"}


def normalize(s):
    s = (s or "").lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    toks = [t for t in s.split() if t and t not in _STOP]
    return " ".join(toks)


def primary_anchor(c):
    """Prefer a stable anchor (ticket# or email subject) over paraphrase-prone text."""
    tickets = c.get("tickets") or []
    if tickets:
        return "t:" + "|".join(sorted(normalize(t) for t in tickets))
    subj = c.get("emailSubject")
    if subj:
        return "s:" + normalize(subj)
    return "c:" + normalize(c.get("commitment", ""))


def commitment_key(c):
    raw = normalize(c.get("initiative", "")) + "||" + primary_anchor(c)
    return hashlib.sha1(raw.encode()).hexdigest()[:16]


def _priority(conf):
    return {"high": "high", "medium": "medium", "low": "low"}.get(conf, "medium")


def merge(base_tasks, commitments, now_ms, today):
    """Return (merged_tasks, stats). base_tasks is the FULL live task array."""
    by_key = {t["commitmentKey"]: t for t in base_tasks if t.get("commitmentKey")}
    stats = {"scanned": len(commitments), "new": 0, "updated": 0,
             "skipped_done": 0, "unanchored": 0}
    seq = 0
    for c in commitments:
        if c.get("unanchored"):
            stats["unanchored"] += 1
            continue
        key = commitment_key(c)
        fields = {
            "initiative": c.get("initiative", ""),
            "who": c.get("who", ""),
            "specifics": c.get("specifics", ""),
            "nextAction": c.get("nextAction", ""),
            "confidence": c.get("confidence", "medium"),
            "sourceLayer": c.get("sourceLayer", ""),
            "evidence": c.get("evidence", ""),
            "lastSeen": today,
        }
        if key in by_key:
            t = by_key[key]
            if t.get("done"):
                stats["skipped_done"] += 1
                continue
            t.update(fields)
            t["text"] = c.get("commitment", t.get("text", ""))
            t["priority"] = _priority(fields["confidence"])
            stats["updated"] += 1
        else:
            seq += 1
            t = {
                "id": now_ms + seq,
                "text": c.get("commitment", ""),
                "priority": _priority(fields["confidence"]),
                "done": False,
                "created": today,
                "source": "commitment",
                "commitmentKey": key,
                "firstSeen": today,
                **fields,
            }
            base_tasks.append(t)
            by_key[key] = t
            stats["new"] += 1
    return base_tasks, stats


def fetch_base():
    r = subprocess.run(["gh", "api", f"repos/{REPO}/contents/{PATH}", "--jq", ".content"],
                       capture_output=True)
    if r.returncode != 0:
        sys.exit(f"commitment_sync ERROR: fetch failed: {r.stderr.decode()[:300]}")
    return json.loads(base64.b64decode(r.stdout.decode()))


def run(args):
    commitments = json.load(open(args.commitments))
    if not isinstance(commitments, list):
        sys.exit("commitment_sync ERROR: --commitments must be a JSON list")
    base = json.load(open(args.base)) if args.base else fetch_base()
    tasks = base.get("tasks", [])
    now_ms = args.now_ms or int(time.time() * 1000)
    today = args.today or time.strftime("%Y-%m-%d")
    merged, stats = merge(tasks, commitments, now_ms, today)
    meta = {"lastScanAt": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "lastRun": stats}
    json.dump(merged, open(args.out_tasks, "w"), ensure_ascii=False, indent=0)
    json.dump(meta, open(args.out_meta, "w"), ensure_ascii=False, indent=0)
    print(json.dumps(stats))
    if args.write:
        cmd = ["python3", args.writer,
               "--set", f"tasks={args.out_tasks}",
               "--set", f"commitmentsMeta={args.out_meta}",
               "--message", args.message or f"Commitments sync {today}"]
        w = subprocess.run(cmd)
        if w.returncode != 0:
            sys.exit(f"commitment_sync ERROR: writer failed rc={w.returncode}")
    else:
        print(f"(dry) wrote slices {args.out_tasks} / {args.out_meta}; pass --write to persist",
              file=sys.stderr)


def selftest():
    today = "2026-07-25"
    base_tasks = [
        {"id": 1, "text": "unrelated normal task", "done": False, "source": "jot"},
    ]
    commits = [
        {"initiative": "Tactical Web", "commitment": "Clear the Globant pre-demo tickets",
         "who": "Sam Armani", "tickets": ["MW-12332"], "confidence": "high",
         "sourceLayer": "goldfish", "nextAction": "confirm assigned", "specifics": "MW-12332",
         "evidence": "prior to our stakeholder demo"},
        {"initiative": "Sweepstakes", "commitment": "Reply to Tim on 0.5 threshold",
         "emailSubject": "Spike in SEM Sweepstakes Form Completions", "confidence": "medium",
         "sourceLayer": "goldfish", "who": "Tim R", "nextAction": "answer", "specifics": "MW-12252",
         "evidence": "how confident are we"},
        {"initiative": "Vague", "commitment": "something I mumbled", "unanchored": True},
    ]
    import copy
    t1, s1 = merge(copy.deepcopy(base_tasks), copy.deepcopy(commits), 1785000000000, today)
    assert s1 == {"scanned": 3, "new": 2, "updated": 0, "skipped_done": 0, "unanchored": 1}, s1
    assert len(t1) == 3, "1 normal + 2 commitment tasks"
    ct = [t for t in t1 if t.get("commitmentKey")]
    assert all(t["done"] is False and t["source"] == "commitment" for t in ct)

    # Idempotency: re-run against the merged output -> 0 new, 2 updated, no dupes.
    t2, s2 = merge(copy.deepcopy(t1), copy.deepcopy(commits), 1785000009999, today)
    assert s2["new"] == 0 and s2["updated"] == 2 and s2["unanchored"] == 1, s2
    assert len([t for t in t2 if t.get("commitmentKey")]) == 2, "no duplicate commitment-tasks"

    # Respect manual done: mark one done, re-run -> it stays done, not reopened/updated.
    for t in t2:
        if t.get("commitmentKey"):
            done_key = t["commitmentKey"]; t["done"] = True; break
    t3, s3 = merge(copy.deepcopy(t2), copy.deepcopy(commits), 1785000019999, today)
    assert s3["skipped_done"] == 1 and s3["updated"] == 1, s3
    done_task = next(t for t in t3 if t.get("commitmentKey") == done_key)
    assert done_task["done"] is True, "manually-completed commitment must stay done"

    # Key stability: paraphrased commitment text, same ticket -> same key.
    c_para = dict(commits[0]); c_para["commitment"] = "Get Globant to finish the demo tickets"
    assert commitment_key(c_para) == commitment_key(commits[0]), "ticket anchor must survive paraphrase"
    print("selftest OK")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--commitments")
    ap.add_argument("--base", help="data.json path; omit to fetch live via gh")
    ap.add_argument("--out-tasks", dest="out_tasks", default="/tmp/commit-tasks.json")
    ap.add_argument("--out-meta", dest="out_meta", default="/tmp/commit-meta.json")
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
    if not args.commitments:
        ap.error("--commitments required (or use --selftest)")
    run(args)


if __name__ == "__main__":
    main()
