#!/usr/bin/env python3
"""
Generate one-line AI summaries for K2 dashboard notes.

Pulls k2-data/data.json, finds notes missing an aiSummary (or whose
text has changed since the last summary), summarizes each via Claude
Haiku, writes the result back as note.aiSummary and note.aiSummaryFor
(sha1 of the source text). The dashboard's renderNotes preview uses
note.aiSummary when present, so refreshing after a run shows the new
summaries on the collapsed note rows.

Run modes:
  --backfill   Process every note missing/stale summary (no cap)
  --batch N    Process at most N notes this run (default 30)
  --dry-run    Show what would be summarized, no LLM call, no commit
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path

REPO = "RyanSandoval/k2-data"
LOG_DIR = Path("/Users/ryansandoval/.openclaw/workspace/k2-dashboard/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

MODEL = "haiku"  # claude CLI alias → claude-cli/claude-haiku-4-5
MAX_CHARS = 140
BATCH_SIZE = 30  # notes per LLM call

SYSTEM_PROMPT = (
    "You are a one-shot summarizer. For each note you receive, write ONE plain sentence "
    f"(max {MAX_CHARS} characters) that captures the action, decision, or core idea. "
    "No prefixes like 'Summary:'. No quotes. No markdown. No emoji. "
    "If a note is empty or fragmentary, return '(empty)'. "
    "Return ONLY a JSON object mapping each note id to its summary string. "
    "No code fences, no prose around the JSON."
)


# ---------- helpers ----------

def log(msg: str) -> None:
    stamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{stamp}] {msg}"
    print(line, flush=True)
    with open(LOG_DIR / f"summarize-{dt.date.today().isoformat()}.log", "a") as f:
        f.write(line + "\n")


def run(cmd: list[str], check: bool = True, input_data: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=check, capture_output=True, text=True, input=input_data)


def call_claude(prompt: str) -> str:
    """Pipe prompt into `claude -p --model haiku` and return raw stdout."""
    res = run(
        [
            "claude", "-p",
            "--model", MODEL,
            "--append-system-prompt", SYSTEM_PROMPT,
        ],
        input_data=prompt,
        check=False,
    )
    if res.returncode != 0:
        raise RuntimeError(f"claude cli failed (rc={res.returncode}): {res.stderr.strip()[:300]}")
    return res.stdout.strip()


def extract_json(text: str) -> dict:
    """Strip code fences / prose and parse JSON object."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```\s*$", "", cleaned)
    # Find first { and last } in case there's stray prose
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        cleaned = cleaned[start : end + 1]
    return json.loads(cleaned)


# ---------- HTML → plain text ----------

class _Stripper(HTMLParser):
    BLOCK_TAGS = {"p", "div", "br", "li", "ul", "ol", "h1", "h2", "h3", "h4", "h5", "h6", "blockquote", "pre"}

    def __init__(self):
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data):
        self.parts.append(data)

    def handle_starttag(self, tag, attrs):
        if tag.lower() in self.BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag.lower() in self.BLOCK_TAGS:
            self.parts.append("\n")


def html_to_text(html: str) -> str:
    if not html:
        return ""
    parser = _Stripper()
    try:
        parser.feed(html)
    except Exception:
        return re.sub(r"<[^>]+>", " ", html)
    text = "".join(parser.parts)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def note_hash(title: str, body: str) -> str:
    h = hashlib.sha1()
    h.update((title or "").encode("utf-8"))
    h.update(b"\x00")
    h.update((body or "").encode("utf-8"))
    return h.hexdigest()


# ---------- k2-data IO ----------

def fetch_data() -> tuple[dict, str]:
    res = run(["gh", "api", f"repos/{REPO}/contents/data.json"])
    payload = json.loads(res.stdout)
    sha = payload["sha"]
    raw = base64.b64decode(payload["content"]).decode("utf-8")
    return json.loads(raw), sha


def commit_data(data: dict, sha: str, message: str) -> None:
    body = json.dumps(data, indent=2, ensure_ascii=False)
    encoded = base64.b64encode(body.encode("utf-8")).decode("ascii")
    payload = {"message": message, "content": encoded, "sha": sha}
    run(
        ["gh", "api", "--method", "PUT", f"repos/{REPO}/contents/data.json", "--input", "-"],
        input_data=json.dumps(payload),
    )


# ---------- summarization ----------

def needs_summary(note: dict) -> bool:
    body = html_to_text(note.get("text") or "")
    title = note.get("title") or ""
    current_hash = note_hash(title, body)
    cached = note.get("aiSummary")
    cached_for = note.get("aiSummaryFor")
    if not cached:
        return True
    if cached_for != current_hash:
        return True
    return False


def summarize_batch(notes: list[dict]) -> dict[str, str]:
    """One claude -p call summarizes the whole batch. Returns {noteId: summary}."""
    payload = []
    for n in notes:
        body = html_to_text(n.get("text") or "")[:2000]
        title = (n.get("title") or "").strip()
        payload.append({"id": n["id"], "title": title or "(none)", "body": body or "(empty)"})
    prompt = (
        f"Summarize each of these {len(payload)} notes. Return ONLY a JSON object "
        "mapping note id → summary string.\n\n"
        + json.dumps(payload, ensure_ascii=False)
    )
    raw = call_claude(prompt)
    try:
        summaries = extract_json(raw)
    except Exception as exc:
        log(f"  parse error: {exc}; raw head: {raw[:200]!r}")
        return {}
    if not isinstance(summaries, dict):
        log(f"  unexpected response type: {type(summaries).__name__}")
        return {}
    # Trim to MAX_CHARS and strip wrapping quotes
    out: dict[str, str] = {}
    for nid, summary in summaries.items():
        if not isinstance(summary, str):
            continue
        text = re.sub(r'^["“”\']+|["“”\']+$', "", summary.strip()).strip()
        if len(text) > MAX_CHARS:
            text = text[: MAX_CHARS - 1].rstrip() + "…"
        out[str(nid)] = text or "(empty)"
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backfill", action="store_true", help="process every stale/missing summary")
    ap.add_argument("--batch", type=int, default=30, help="max notes per run (ignored with --backfill)")
    ap.add_argument("--dry-run", action="store_true", help="don't call LLM, don't commit")
    args = ap.parse_args()

    data, sha = fetch_data()
    notes = data.get("notes") or []
    pending = [n for n in notes if needs_summary(n)]
    if not pending:
        log(f"no work: all {len(notes)} notes have current summaries")
        return

    if not args.backfill:
        pending = pending[: args.batch]

    log(f"starting: {len(pending)} notes to summarize (total notes: {len(notes)}, model: {MODEL}, dry={args.dry_run})")

    if args.dry_run:
        for n in pending[:10]:
            title = (n.get("title") or "").strip()
            body_head = html_to_text(n.get("text") or "")[:80].replace("\n", " ")
            log(f"  would summarize: {n.get('id')} | {title!r} | {body_head!r}")
        log(f"dry-run: {len(pending)} pending (showed first 10)")
        return

    updated = 0
    now_iso = dt.datetime.now(dt.timezone.utc).isoformat()
    for batch_start in range(0, len(pending), BATCH_SIZE):
        batch = pending[batch_start : batch_start + BATCH_SIZE]
        log(f"batch {batch_start // BATCH_SIZE + 1}: {len(batch)} notes")
        summaries = summarize_batch(batch)
        if not summaries:
            log("  batch returned no summaries; skipping")
            continue
        for n in batch:
            summary = summaries.get(n["id"])
            if not summary:
                continue
            body = html_to_text(n.get("text") or "")
            title = n.get("title") or ""
            n["aiSummary"] = summary
            n["aiSummaryFor"] = note_hash(title, body)
            n["aiSummaryAt"] = now_iso
            updated += 1
            log(f"  {n['id']}: {summary}")

    if updated == 0:
        log("no notes updated; skipping commit")
        return

    # Re-fetch sha if commit may race; but we just fetched, fine for now.
    commit_data(
        data,
        sha,
        f"k2: AI summaries for {updated} note{'s' if updated != 1 else ''}",
    )
    log(f"done: committed {updated} summary update(s)")


if __name__ == "__main__":
    main()
