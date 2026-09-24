#!/usr/bin/env python3
"""Quality lookback for /bulma: what human review catches that the graphs miss.

Reads $RUVER_HOME/insights/observations.jsonl (contract:
../../ruver-bus/INSIGHTS.md), keeps human comments whose claim held, and
counts them per cluster in a window and in the equal window before it,
normalized per reviewed PR. A cluster whose `guard` names a skill section
should shrink after that section changed; one that does not is the change
to reopen. Clusters are regexes over generalized_pattern, so counts are a
floor. Read-only. No Jev, no key.

usage: lookback.py [--since DAYS|YYYY-MM-DD] [--until YYYY-MM-DD] [--json] [--file PATH]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

BOT_MARKERS = ("ruver-", "[bot]", "bot", "agent", "claude", "copilot", "coderabbit", "decider")
MIN_PRS = 10  # below this many reviewed PRs in either window, no trend

# guard: the skill text that should make the cluster shrink, or "repo rule"
# when the fix belongs in the target repo's CLAUDE.md / AGENTS.md.
CLUSTERS = [
    ("sibling-path parity", "ruver-code-review Phase 5",
     r"sibling|every (hook|path|caller)|all (callers|sibling|interactive controls|commit paths)|symmetric|bulk_operation|one block without|other callers|grep for all|repo-wide"),
    ("multi-store write / side effect", "ruver-code-review Phase 6",
     r"dual.?write|audit (event|emit)|emit|idempot|at-least-once|rollback|orphan|split-brain|readback|mirror|partial(ly)? succe|transaction"),
    ("test that cannot fail", "ruver-code-review Phase 4",
     r"vacuous|never fail|test\.skip|describe\.skip|zero (assertions|automat|default ci)|skips? when|only asserts?.*called|spy .* without|gated e2e|never wired"),
    ("unvalidated input into typed column", "ruver-code-review Phase 6",
     r"uuid|@db\.|format validation|runtime.validat|cast error|as-cast|typed column"),
    ("reviewer self-defect", "ruver-code-review bind-findings",
     r"line numbers?|diff-offset|pre-?exist|appear(s)? in the (pr )?diff|already (inspected|raised|cleared)|human reviewer (has )?(already|explicitly)|false-positive|invent|dedup"),
    ("acceptance-criteria completeness", "ruver-code-review Phase 3",
     r"acceptance criteri|\bac\b|enumerat|inventory|deferral"),
    ("authz / privilege", "repo rule",
     r"outrank|privilege|role tier|pkce|oauth state|csrf|issuer|fail(s)? open|open redirect"),
    ("silent catch / no error report", "repo rule",
     r"sentry|silent(ly)? (catch|swallow|fail)|swallow|breadcrumb|without .*capture"),
    ("effect lifecycle", "ruver-code-review Phase 5",
     r"useeffect|cleanup|teardown|unsubscribe|removeeventlistener|abort"),
    ("pagination / unbounded", "ruver-code-review Phase 9",
     r"paginat|without a take|unbounded|take/limit|hasmore|hasnextpage"),
    ("tenant / cache-key isolation", "ruver-code-review Phase 6",
     r"tenant|cross-session|query ?key"),
]


def ruver_home():
    env = os.environ.get("RUVER_HOME")
    if env:
        return Path(env)
    home = Path.home() / ".ruver"
    grok = Path.home() / ".grok" / "ruver"
    return grok if not home.exists() and grok.is_dir() else home


def load(path):
    rows = []
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
    except OSError:
        return rows
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows


def day(row):
    return (row.get("timestamp") or row.get("date") or "")[:10]


def is_human(row):
    who = (row.get("reviewer") or "").lower()
    return bool(who) and not any(m in who for m in BOT_MARKERS)


def missed(row):
    """Human caught it and we did not. Newer rows carry caught_by_ours."""
    if row.get("claim_true") == "no":
        return False  # lstm verified the reviewer was wrong
    caught = str(row.get("caught_by_ours") or row.get("would_existing_agent_catch_it") or "").lower()
    return caught.startswith(("no", "partially", "not", "unknown"))


def window(since, until):
    end = datetime.strptime(until, "%Y-%m-%d").date() if until else datetime.now(timezone.utc).date()
    if re.fullmatch(r"\d+", since):
        start = end - timedelta(days=int(since) - 1)
    else:
        start = datetime.strptime(since, "%Y-%m-%d").date()
    span = (end - start).days + 1
    prev_end = start - timedelta(days=1)
    return (start, end), (prev_end - timedelta(days=span - 1), prev_end)


def tally(rows, win):
    lo, hi = win[0].isoformat(), win[1].isoformat()
    inside = [r for r in rows if lo <= day(r) <= hi and is_human(r)]
    prs = {r.get("pr_ref") for r in inside if r.get("pr_ref")}
    miss = [r for r in inside if missed(r)]
    clusters, unclustered = {}, []
    for row in miss:
        text = row.get("generalized_pattern") or ""
        hit = False
        for name, _, rx in CLUSTERS:
            if re.search(rx, text, re.I):
                clusters.setdefault(name, []).append(row)
                hit = True
        if not hit:
            unclustered.append(row)
    return {"human": len(inside), "prs": len(prs), "missed": len(miss),
            "clusters": clusters, "unclustered": unclustered}


def trend(now, prev, now_prs, prev_prs):
    if now_prs < MIN_PRS or prev_prs < MIN_PRS:
        return "need data"
    a, b = now / now_prs, prev / prev_prs
    if b == 0:
        return "new" if a else "="
    ratio = a / b
    return "down" if ratio <= 0.75 else "up" if ratio >= 1.25 else "="


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--file", default=None)
    ap.add_argument("--since", default="30", help="days back from --until, or a start date")
    ap.add_argument("--until", default="", help="end date, default today (UTC)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    path = Path(args.file) if args.file else ruver_home() / "insights" / "observations.jsonl"
    rows = load(path)
    if not rows:
        print("lookback: no observations at %s. ruver-lstm and ruver-reviewer write them (INSIGHTS.md)." % path)
        return 0
    try:
        cur_win, prev_win = window(args.since, args.until)
    except ValueError:
        print("lookback: --since takes a day count or YYYY-MM-DD, --until YYYY-MM-DD", file=sys.stderr)
        return 4
    cur, prev = tally(rows, cur_win), tally(rows, prev_win)

    table = []
    for name, guard, _ in CLUSTERS:
        now_rows = cur["clusters"].get(name, [])
        prev_n = len(prev["clusters"].get(name, []))
        if not now_rows and not prev_n:
            continue
        table.append({
            "cluster": name, "guard": guard, "obs": len(now_rows),
            "prs": len({r.get("pr_ref") for r in now_rows}),
            "critical": sum(1 for r in now_rows if r.get("severity_inferred") == "critical"),
            "per_pr": round(len(now_rows) / cur["prs"], 2) if cur["prs"] else 0.0,
            "prev_per_pr": round(prev_n / prev["prs"], 2) if prev["prs"] else 0.0,
            "trend": trend(len(now_rows), prev_n, cur["prs"], prev["prs"]),
            "examples": [r.get("generalized_pattern", "")[:140] for r in now_rows[:3]],
        })
    table.sort(key=lambda t: (-t["obs"], t["cluster"]))
    keywords = Counter(k.lower() for r in cur["unclustered"] for k in (r.get("context_keywords") or []))

    if args.json:
        print(json.dumps({"window": [d.isoformat() for d in cur_win], "previous": [d.isoformat() for d in prev_win],
                          "human": cur["human"], "prs": cur["prs"], "missed": cur["missed"],
                          "prev_prs": prev["prs"], "prev_missed": prev["missed"], "clusters": table,
                          "unclustered": len(cur["unclustered"]),
                          "unclustered_keywords": keywords.most_common(10)}, indent=2))
        return 0

    print("lookback %s..%s vs %s..%s" % (cur_win[0], cur_win[1], prev_win[0], prev_win[1]))
    print("human comments %d on %d PRs, missed %d  |  previous: %d missed on %d PRs" % (
        cur["human"], cur["prs"], cur["missed"], prev["missed"], prev["prs"]))
    if not table:
        print("no clustered misses in either window")
    else:
        print()
        print("| cluster | obs | PRs | crit | per PR | prev per PR | trend | guard |")
        print("|---|---|---|---|---|---|---|---|")
        for t in table:
            print("| %s | %d | %d | %d | %.2f | %.2f | %s | %s |" % (
                t["cluster"], t["obs"], t["prs"], t["critical"], t["per_pr"], t["prev_per_pr"], t["trend"], t["guard"]))
    if cur["unclustered"]:
        print()
        print("unclustered: %d missed rows match no cluster. Top keywords: %s" % (
            len(cur["unclustered"]), ", ".join("%s (%d)" % kv for kv in keywords.most_common(8)) or "none"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
