#!/usr/bin/env python3
"""Recurring review lessons for one repo, as a block for a coder brief.

Reads the same observations and label cache as lookback.py, keeps the misses
from --repo, and ranks clusters by distinct PRs. With --kind implementer
(default) it prints the rule for each top cluster from
../../ruver-feature-delivery/LESSONS.md plus one example from this repo, ready
to paste into the ruver-fd-coder prompt. With --kind repo_rule it lists the
clusters whose lesson belongs in the repo's own CLAUDE.md, with examples to
draft that rule from.

Advisory, not a gate: a cached label counts when its confidence clears the
catalog act_at, whatever the hook's power, because a hint in a brief costs
nothing when it is wrong. Prints nothing when there is nothing to say.

usage: lessons.py --repo owner/repo [--files a.ts,b.tsx] [--since DAYS]
                  [--limit N] [--kind implementer|repo_rule] [--json] [--file PATH]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.dont_write_bytecode = True  # no __pycache__ inside the installed skill
sys.path.insert(0, str(Path(__file__).resolve().parent))
import lookback as lb  # noqa: E402

LESSONS_MD = lb.HERE.parent.parent / "ruver-feature-delivery" / "LESSONS.md"
UI_EXT = (".tsx", ".jsx", ".vue", ".svelte")
UI_ONLY = {"effect lifecycle"}  # only worth a line when the ticket touches UI files
EXAMPLE_CAP = 140
KINDS = ("implementer", "repo_rule")


def rules(path=LESSONS_MD):
    """cluster name -> first paragraph under its ### heading."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return {}
    out = {}
    for match in re.finditer(r"^### (.+?)\n+(.+?)(?=\n\n|\n###|\Z)", text, re.S | re.M):
        out[match.group(1).strip()] = " ".join(match.group(2).split())
    return out


def label_act_at():
    hooks = json.loads(lb.CATALOG.read_text(encoding="utf-8"))["hooks"]
    questions = next(h for h in hooks if h["id"] == lb.HOOK)["questions"]
    return {qid: q["act_at"] for qid, q in questions.items()}


def row_view(row, labels, act_at):
    """(clusters, lesson or None) for one row, labels first where confident."""
    label = labels.get(row.get("id")) or {}
    if float(label.get("cluster_conf") or 0) >= act_at["cluster"] and label.get("cluster"):
        names = [] if label["cluster"] == lb.OTHER else [label["cluster"]]
    else:
        names = lb.regex_clusters(row)
    lesson = label.get("lesson_for") if float(label.get("lesson_conf") or 0) >= act_at["lesson_for"] else None
    return names, lesson


def collect(rows, labels, repo, since_days, files):
    cutoff = (datetime.now(timezone.utc).date() - timedelta(days=since_days)).isoformat()
    act_at = label_act_at()
    ui = any(f.endswith(UI_EXT) for f in files) if files else True
    prefix = repo + "#"
    stats = {}
    for row in rows:
        if lb.day(row) < cutoff or not (row.get("pr_ref") or "").startswith(prefix):
            continue
        fd = row.get("source") == "fd"
        if not fd and not (lb.is_human(row) and lb.missed(row)):
            continue
        names, lesson = row_view(row, labels, act_at)
        for name in names:
            if name in UI_ONLY and not ui:
                continue
            s = stats.setdefault(name, {"prs": set(), "obs": 0, "critical": 0, "gate": 0,
                                        "lessons": Counter(), "examples": []})
            if fd:
                s["gate"] += 1
                continue
            s["prs"].add(row.get("pr_ref"))
            s["obs"] += 1
            s["critical"] += row.get("severity_inferred") == "critical"
            if lesson:
                s["lessons"][lesson] += 1
            s["examples"].append((lb.day(row), (row.get("generalized_pattern") or "")[:EXAMPLE_CAP]))
    return stats


def majority(counter):
    if not counter:
        return None
    name, n = counter.most_common(1)[0]
    return name if n * 2 > sum(counter.values()) else None


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", required=True, help="owner/repo, as in STATE repo")
    ap.add_argument("--files", default="", help="comma list of ticket files; drops UI-only lessons for non-UI work")
    ap.add_argument("--since", type=int, default=120, help="days of history")
    ap.add_argument("--limit", type=int, default=5)
    ap.add_argument("--kind", default="implementer", choices=KINDS)
    ap.add_argument("--file", default=None)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    path = Path(args.file) if args.file else lb.ruver_home() / "insights" / "observations.jsonl"
    rows = lb.load(path)
    labels = lb.load_labels(path.with_name("labels.jsonl"), lb.catalog_version())
    files = [f.strip() for f in args.files.split(",") if f.strip()]
    stats = collect(rows, labels, args.repo, args.since, files)
    guide = rules()

    picked = []
    for name, s in stats.items():
        if not s["obs"]:
            continue
        lesson = majority(s["lessons"])
        if args.kind == "implementer":
            # A confident majority elsewhere means this is not the coder's lesson.
            if lesson not in (None, "implementer") or name not in guide:
                continue
        elif lesson != "repo_rule":
            continue
        examples = [p for _, p in sorted(s["examples"], reverse=True)]
        picked.append({"cluster": name, "prs": len(s["prs"]), "obs": s["obs"], "critical": s["critical"],
                       "gate": s["gate"], "lesson": lesson or "-", "rule": guide.get(name, ""),
                       "examples": examples[:2]})
    picked.sort(key=lambda p: (-p["prs"], -p["critical"], p["cluster"]))
    picked = picked[:args.limit]

    if args.json:
        print(json.dumps({"repo": args.repo, "kind": args.kind, "since_days": args.since, "lessons": picked}, indent=2))
        return 0
    if not picked:
        return 0
    if args.kind == "implementer":
        print("## Recurring review lessons in %s (last %d days)" % (args.repo, args.since))
        print()
        print("Human reviewers kept catching these after our gates passed. Apply them while you write the code.")
        print()
        for p in picked:
            print("- **%s** (%d PRs). %s" % (p["cluster"], p["prs"], p["rule"]))
            if p["examples"]:
                print("  Seen here: %s" % p["examples"][0])
    else:
        print("## Candidate CLAUDE.md rules for %s (last %d days)" % (args.repo, args.since))
        print()
        for p in picked:
            print("- **%s** (%d PRs, %d critical)" % (p["cluster"], p["prs"], p["critical"]))
            for example in p["examples"]:
                print("  - %s" % example)
    return 0


if __name__ == "__main__":
    sys.exit(main())
