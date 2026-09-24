#!/usr/bin/env python3
"""Append one review observation to $RUVER_HOME/insights/observations.jsonl.

Contract: ../INSIGHTS.md. Human comments come from lstm and reviewer; fd
rows record a defect our own gates caught before the PR. Validates every
field, derives caught_by_ours from the ruver-review marker's open= list
(fd rows are "self"), skips an id already in the file, and appends under
an exclusive lock so parallel workers never interleave lines.

exit 0 written or duplicate (prints which), 4 invalid input.
"""
from __future__ import annotations

import argparse
import datetime
import fcntl
import json
import os
import re
import sys
from pathlib import Path

AXES = ("spec", "tests", "correctness", "contract", "security", "standards",
        "perf", "a11y", "deps", "other")
SEVERITIES = ("critical", "important", "nice_to_have")
CLAIMS = ("yes", "no", "unknown")
SOURCES = ("lstm", "reviewer", "fd")
# fd rows are our own gates catching a defect before the PR exists.
FD_REVIEWERS = ("ruver-fd-reviewer", "ruver-fd-quality")
SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{0,79}$")
PATTERN_CAP = 300
KEYWORDS_MAX = 6
LINE_WINDOW = 10
PR_REF = re.compile(r"^[\w.-]+/[\w.-]+#\d+$")
BOT_LOGIN = re.compile(r"\[bot\]$|^(github-actions|dependabot|renovate)$", re.I)


def ruver_home() -> Path:
    env = os.environ.get("RUVER_HOME")
    if env:
        return Path(env)
    home = Path.home() / ".ruver"
    legacy = Path.home() / ".grok" / "ruver"
    return legacy if not home.exists() and legacy.is_dir() else home


def caught_by_ours(open_list: str | None, path: str, line: int | None) -> str:
    """yes when our marker's open= list has a finding on path within LINE_WINDOW."""
    if open_list is None:
        return "unknown"
    for entry in open_list.split("|"):
        parts = entry.strip().split(":")
        if len(parts) < 2 or parts[0] != path:
            continue
        if line is None or not parts[1].isdigit():
            return "yes"
        if abs(int(parts[1]) - line) <= LINE_WINDOW:
            return "yes"
    return "no"


def build(args: argparse.Namespace) -> dict:
    errors = []
    fd = args.source == "fd"
    if fd:
        if args.reviewer not in FD_REVIEWERS:
            errors.append("--source fd needs --reviewer %s" % " or ".join(FD_REVIEWERS))
        if not args.job or not SLUG.match(args.finding_id or ""):
            errors.append("--source fd needs --job and a kebab-case --finding-id")
        if args.pr_ref and not PR_REF.match(args.pr_ref):
            errors.append("--pr-ref must be owner/repo#number")
    else:
        if BOT_LOGIN.search(args.reviewer):
            errors.append("reviewer %r is a bot; observations are human review only" % args.reviewer)
        if args.comment_id is None or not args.sha:
            errors.append("--source %s needs --comment-id and --sha" % args.source)
        if not PR_REF.match(args.pr_ref or ""):
            errors.append("--pr-ref must be owner/repo#number")
    pattern = " ".join(args.pattern.split())
    if not pattern:
        errors.append("--pattern is empty")
    elif len(pattern) > PATTERN_CAP:
        errors.append("--pattern is %d chars, cap %d" % (len(pattern), PATTERN_CAP))
    keywords = [k.strip().lower() for k in (args.keywords or "").split(",") if k.strip()]
    if len(keywords) > KEYWORDS_MAX:
        errors.append("--keywords has %d entries, max %d" % (len(keywords), KEYWORDS_MAX))
    if errors:
        for e in errors:
            print("observe: " + e, file=sys.stderr)
        raise SystemExit(4)
    caught = "self" if fd else caught_by_ours(args.ours_open, args.path, args.line)
    return {
        "id": "fd-%s-%s" % (args.job, args.finding_id) if fd else "gh-%s" % args.comment_id,
        "pr_ref": args.pr_ref or "",
        "job": args.job or "",
        "head_sha": args.sha,
        "reviewer": args.reviewer,
        "source": args.source,
        "path": args.path,
        "line": args.line,
        "axis": args.axis,
        "severity_inferred": args.severity,
        "claim_true": args.claim_true,
        "generalized_pattern": pattern,
        "context_keywords": keywords,
        "caught_by_ours": caught,
        # Legacy field lookback readers filter on; mirrors caught_by_ours.
        "would_existing_agent_catch_it": caught,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def append(row: dict, target: Path) -> bool:
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "a+", encoding="utf-8") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        fh.seek(0)
        for line in fh:
            try:
                if json.loads(line).get("id") == row["id"]:
                    return False
            except (json.JSONDecodeError, AttributeError):
                continue
        fh.seek(0, os.SEEK_END)
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--comment-id", type=int, default=None, help="GitHub review, inline, or issue comment id (lstm, reviewer)")
    ap.add_argument("--pr-ref", default="", help="owner/repo#number; optional for fd, which runs before the PR")
    ap.add_argument("--sha", default="", help="head sha at observation time")
    ap.add_argument("--job", default="", help="fd: STATE job_id, e.g. dev-abc-123")
    ap.add_argument("--finding-id", default="", help="fd: kebab-case slug, stable across review laps")
    ap.add_argument("--reviewer", required=True, help="comment author login")
    ap.add_argument("--source", required=True, choices=SOURCES)
    ap.add_argument("--axis", required=True, choices=AXES)
    ap.add_argument("--severity", required=True, choices=SEVERITIES)
    ap.add_argument("--claim-true", required=True, choices=CLAIMS)
    ap.add_argument("--pattern", required=True, help="one sentence, no repo, file, or people names")
    ap.add_argument("--path", default="", help="bound path, empty for body-only comments")
    ap.add_argument("--line", type=int, default=None)
    ap.add_argument("--keywords", default="", help="comma list, max 6")
    ap.add_argument("--ours-open", default=None,
                    help="open= value of the latest ruver-review marker on the PR; omit when none exists")
    ap.add_argument("--file", default=None, help="override target (tests)")
    args = ap.parse_args()

    row = build(args)
    target = Path(args.file) if args.file else ruver_home() / "insights" / "observations.jsonl"
    written = append(row, target)
    print("%s %s caught_by_ours=%s" % ("written" if written else "duplicate", row["id"], row["caught_by_ours"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
