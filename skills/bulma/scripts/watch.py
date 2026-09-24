#!/usr/bin/env python3
"""Find stalled ruver work in every workspace under $RUVER_HOME.

Watchdog for /bulma: reads each workspace's graph STATE.md files, drops
terminal ones, reconciles the rest against GitHub (a merged or closed PR
means the run finished outside the graph), and prints one line per
workspace with the concrete next step. Read-only on graph state. The only
file it writes is $RUVER_HOME/bulma-watch.json, which caches PRs already
seen merged or closed so later runs skip the gh call. No Jev, no key.

usage: watch.py [--stale-hours N] [--no-gh] [--summary] [--json] [--home DIR]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

GRAPHS = ("developer", "feature-delivery", "qa", "triage", "reviewer", "lstm", "goal")
# ruver-bus/JOBS.md terminal set, plus the close statuses graphs write.
DONE = {"done", "done_notes", "done_report", "complete", "published", "deferred",
        "handed_off", "classified", "walked", "qa_pass"}
NEEDS_YOU = {"waiting_user", "escalated", "blocked", "waiting_blocker"}
CACHE_NAME = "bulma-watch.json"


def ruver_home(override):
    if override:
        return Path(override)
    env = os.environ.get("RUVER_HOME")
    if env:
        return Path(env)
    home = Path.home() / ".ruver"
    grok = Path.home() / ".grok" / "ruver"
    return grok if not home.exists() and grok.is_dir() else home


def frontmatter(path):
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {}
    match = re.match(r"^---\n(.*?)\n---", text, re.S)
    # Older STATE files have no frontmatter: bare `key: value` lines under the
    # title, up to the first section heading.
    head = match.group(1) if match else text.split("\n## ", 1)[0]
    fields = {}
    for line in head.splitlines():
        if re.match(r"^[a-z_]+:", line):
            key, _, value = line.partition(":")
            fields.setdefault(key.strip(), value.strip().strip("\"'"))
    return fields


def parse_ts(value):
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError):
        return None


def age_hours(fields, path, now):
    ts = parse_ts(fields.get("updated_at", ""))
    if ts is None or ts.tzinfo is None:
        ts = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
    return (now - ts).total_seconds() / 3600


def workspace_path(slug):
    """Invert the DISK.md slug (path with / turned into -) by walking the disk."""
    parts = slug.split("-")

    def walk(base, i):
        if i == len(parts):
            return base
        for j in range(len(parts), i, -1):  # longest name first
            path = os.path.join(base, "-".join(parts[i:j]))
            if os.path.isdir(path):
                found = walk(path, j)
                if found:
                    return found
        return None

    return walk("/", 0)


def gh_pr(url):
    try:
        out = subprocess.run(
            ["gh", "pr", "view", url, "--json", "state,isDraft,mergeable,statusCheckRollup"],
            capture_output=True, text=True, timeout=30)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if out.returncode != 0:
        return None
    try:
        return json.loads(out.stdout)
    except ValueError:
        return None


def ci_from(rollup):
    states = {str(c.get("conclusion") or c.get("state") or "").upper() for c in rollup or []}
    if states & {"FAILURE", "ERROR", "TIMED_OUT", "CANCELLED", "ACTION_REQUIRED", "STARTUP_FAILURE"}:
        return "red"
    if not states or states & {"PENDING", "IN_PROGRESS", "QUEUED", "WAITING", "EXPECTED", "REQUESTED", ""}:
        return "pending"
    return "green"


def scan(home, stale_hours, now):
    """One entry per workspace with at least one live graph STATE."""
    workspaces = []
    for ws in sorted(p for p in home.iterdir() if p.is_dir()):
        jobs, any_pr = [], ""
        states = {}
        for graph in GRAPHS:
            path = ws / (".ruver-" + graph) / "STATE.md"
            if path.is_file():
                states[graph] = (path, frontmatter(path))
        for graph, (path, fields) in states.items():
            url = fields.get("pr_url", "")
            any_pr = any_pr or (url if "/pull/" in url else "")
            status = fields.get("status", "")
            if status in DONE:
                continue
            # feature-delivery is developer's engine: once developer closed,
            # a leftover fd status is a stale mirror, not live work.
            if graph == "feature-delivery" and states.get("developer", (None, {}))[1].get("status") in DONE:
                continue
            jobs.append({
                "graph": graph,
                "status": status,
                "age_h": round(age_hours(fields, path, now), 1),
                "pr_url": fields.get("pr_url", "") if "/pull/" in fields.get("pr_url", "") else "",
                "worktree": fields.get("worktree", ""),
                "question": fields.get("waiting_user", "")[:120],
            })
        if not jobs:
            continue
        needs_you = [j for j in jobs if j["status"] in NEEDS_YOU]
        youngest = min(j["age_h"] for j in jobs)
        if not needs_you and youngest < stale_hours:
            continue  # something in this workspace moved recently: not stalled
        pr_url = next((j["pr_url"] for j in jobs if j["pr_url"]), "") or any_pr
        worktree = next((j["worktree"] for j in jobs if j["worktree"]), "") or workspace_path(ws.name) or ""
        workspaces.append({
            "workspace": ws.name,
            "jobs": jobs,
            "age_h": youngest,
            "pr_url": pr_url,
            "worktree": worktree,
            "worktree_exists": bool(worktree) and Path(worktree).is_dir(),
            "needs_you": bool(needs_you),
            "question": next((j["question"] for j in needs_you if j["question"]), ""),
        })
    return workspaces


def classify(ws, pr, closed_cache):
    """bucket + next step. Buckets: closed, needs_you, orphaned, stalled."""
    if ws["pr_url"] in closed_cache:
        return "closed", "PR %s; nothing to resume" % closed_cache[ws["pr_url"]].lower()
    if pr and pr.get("state") in ("MERGED", "CLOSED"):
        closed_cache[ws["pr_url"]] = pr["state"]
        return "closed", "PR %s; nothing to resume" % pr["state"].lower()
    if not ws["worktree_exists"]:
        return "orphaned", "workspace gone; restart from the PR or drop it"
    where = "cd %s && " % ws["worktree"]
    if ws["needs_you"]:
        return "needs_you", "answer, then %s/bulma resume" % where
    if pr:
        ci = ci_from(pr.get("statusCheckRollup"))
        if ci == "red":
            return "stalled", "CI red: %s/bulma %s" % (where, ws["pr_url"])
        if pr.get("mergeable") == "CONFLICTING":
            return "stalled", "conflicts: %s/bulma %s" % (where, ws["pr_url"])
    return "stalled", "%s/bulma resume" % where


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--home", default=None)
    ap.add_argument("--stale-hours", type=float, default=24)
    ap.add_argument("--no-gh", action="store_true", help="skip GitHub reconcile")
    ap.add_argument("--summary", action="store_true", help="one line, no gh calls")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    home = ruver_home(args.home)
    if not home.is_dir():
        print("watch: no ruver home at %s" % home)
        return 0
    now = datetime.now(timezone.utc)
    cache_path = home / CACHE_NAME
    try:
        cache = json.loads(cache_path.read_text())
    except (OSError, ValueError):
        cache = {}
    closed = cache.setdefault("closed", {})

    workspaces = scan(home, args.stale_hours, now)
    use_gh = not (args.no_gh or args.summary)
    urls = sorted({w["pr_url"] for w in workspaces if use_gh and w["pr_url"] and w["pr_url"] not in closed})
    with ThreadPoolExecutor(max_workers=8) as pool:
        prs = dict(zip(urls, pool.map(gh_pr, urls)))
    for ws in workspaces:
        ws["bucket"], ws["next"] = classify(ws, prs.get(ws["pr_url"]), closed)

    if use_gh:
        cache_path.write_text(json.dumps(cache, indent=2, sort_keys=True))

    counts = {b: sum(1 for w in workspaces if w["bucket"] == b)
              for b in ("needs_you", "stalled", "orphaned", "closed")}
    if args.summary:
        live = counts["needs_you"] + counts["stalled"] + counts["orphaned"]
        if live:
            print("watch: %d need you, %d stalled, %d orphaned elsewhere (/bulma watch)" % (
                counts["needs_you"], counts["stalled"], counts["orphaned"]))
        return 0
    if args.json:
        print(json.dumps({"generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
                          "stale_hours": args.stale_hours, "counts": counts,
                          "workspaces": workspaces}, indent=2))
        return 0

    print("watch: %d need you · %d stalled · %d orphaned · %d closed upstream (stale >= %gh%s)" % (
        counts["needs_you"], counts["stalled"], counts["orphaned"], counts["closed"],
        args.stale_hours, "" if use_gh else ", no gh"))
    for bucket in ("needs_you", "stalled", "orphaned"):
        rows = sorted((w for w in workspaces if w["bucket"] == bucket), key=lambda w: -w["age_h"])
        if not rows:
            continue
        print("\n## %s" % bucket)
        for w in rows:
            graphs = ",".join("%s:%s" % (j["graph"], j["status"]) for j in w["jobs"])
            print("- %s  %s  %.0fh  %s" % (w["pr_url"] or w["workspace"], graphs, w["age_h"], w["next"]))
            if w["question"]:
                print("    Q: %s" % w["question"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
