#!/usr/bin/env python3
"""Quality lookback for /bulma: what human review catches that the graphs miss.

Reads $RUVER_HOME/insights/observations.jsonl (contract:
../../ruver-bus/INSIGHTS.md), keeps human comments whose claim held, and
counts them per cluster in a window and in the equal window before it,
normalized per reviewed PR. A cluster whose `guard` names a skill section
should shrink after that section changed; one that does not is the change
to reopen.

Clustering: regexes over generalized_pattern by default, a floor. With
--classify, Jev labels each missed row through the `insight.classify` hook
(cluster, generalizable, lesson_for) and the labels are cached in
$RUVER_HOME/insights/labels.jsonl, keyed by row id and catalog version. A
label replaces the regex only where Jev acted; everywhere else the regex
decides. Without --classify no key is needed and cached labels still apply.

usage: lookback.py [--since DAYS|YYYY-MM-DD] [--until YYYY-MM-DD] [--json]
                   [--classify [--replay FILE]] [--file PATH]
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
CATALOG = HERE.parent / "decisions.json"
HOOK = "insight.classify"
BOT_MARKERS = ("ruver-", "[bot]", "bot", "agent", "claude", "copilot", "coderabbit", "decider")
MIN_PRS = 10  # below this many reviewed PRs in either window, no trend
OTHER = "other"
# Where a lesson should live. decisions.json insight.classify.lesson_for
# reads its enum from these literals.
LESSONS = ("implementer", "reviewer", "repo_rule", "none")

# guard: the skill text that should make the cluster shrink, or "repo rule"
# when the fix belongs in the target repo's CLAUDE.md / AGENTS.md. Names are
# the insight.classify cluster enum, plus "other".
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
GUARD = {name: guard for name, guard, _ in CLUSTERS}


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


def regex_clusters(row):
    text = row.get("generalized_pattern") or ""
    return [name for name, _, rx in CLUSTERS if re.search(rx, text, re.I)]


def catalog_version():
    """Labels go stale when the hook's questions change."""
    hooks = json.loads(CATALOG.read_text(encoding="utf-8"))["hooks"]
    hook = next(h for h in hooks if h["id"] == HOOK)
    return hashlib.sha256(json.dumps(hook["questions"], sort_keys=True).encode()).hexdigest()[:12]


def gate(power=None):
    """Current thresholds for insight.classify, from bulma.py's own rules."""
    sys.dont_write_bytecode = True  # no __pycache__ inside the installed skill
    spec = importlib.util.spec_from_file_location("bulma_core", HERE / "bulma.py")
    core = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(core)
    hook = core.find_hook(core.load_catalog(), HOOK)
    cfg = core.load_config()
    level, _ = core.resolve_power(power, HOOK, cfg)
    overrides = cfg.get("act_at", {})
    act_at = {qid: core.effective_act_at(overrides.get("%s.%s" % (HOOK, qid), q["act_at"]), level, q.get("direction", "act"))
              for qid, q in hook["questions"].items()}
    return level, act_at


def judged(label, level, act_at):
    """(cluster or None, one_off, lesson or None) that count under the current power."""
    if not label or level == "shadow":
        return None, False, None
    conf = lambda key: float(label.get(key) or 0.0)
    cluster = label.get("cluster") if conf("cluster_conf") >= act_at["cluster"] else None
    noul = label.get("generalizable")
    one_off = noul is not None and float(noul) <= round(1 - act_at["generalizable"], 2)
    lesson = label.get("lesson_for") if conf("lesson_conf") >= act_at["lesson_for"] else None
    return cluster, one_off, lesson


def load_labels(path, version):
    return {r["id"]: r for r in load(path) if r.get("version") == version and r.get("id")}


def window(since, until):
    end = datetime.strptime(until, "%Y-%m-%d").date() if until else datetime.now(timezone.utc).date()
    if re.fullmatch(r"\d+", since):
        start = end - timedelta(days=int(since) - 1)
    else:
        start = datetime.strptime(since, "%Y-%m-%d").date()
    span = (end - start).days + 1
    prev_end = start - timedelta(days=1)
    return (start, end), (prev_end - timedelta(days=span - 1), prev_end)


def in_window(rows, win):
    lo, hi = win[0].isoformat(), win[1].isoformat()
    return [r for r in rows if lo <= day(r) <= hi and is_human(r)]


def classify(rows, labels, labels_path, version, replay):
    """Ask Jev for every missed row without a current label; append new labels."""
    todo = [r for r in rows if r.get("id") and r["id"] not in labels]
    if not todo:
        return 0, ""
    items = []
    for row in todo:
        found = regex_clusters(row)
        item = {
            "id": row["id"], "hook": HOOK,
            "state": {"pattern": row.get("generalized_pattern", ""), "axis": row.get("axis", ""),
                      "severity": row.get("severity_inferred", ""),
                      "keywords": row.get("context_keywords") or [], "source": row.get("source", "")},
            "graph_answer": {"cluster": found[0] if found else OTHER},
            "context": {"pr": row.get("pr_ref", "")},
        }
        if replay:
            item["replay"] = replay
        items.append(item)
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
        json.dump({"items": items}, fh)
        batch = fh.name
    try:
        # Decisions log under insights/.ruver-bulma so /bulma report sees them.
        out = subprocess.run(
            [sys.executable, str(HERE / "bulma.py"), "ask-many", "--batch", batch, "--json",
             "--ruver-root", str(labels_path.parent)],
            capture_output=True, text=True)
    finally:
        os.unlink(batch)
    try:
        docs = json.loads(out.stdout)
    except ValueError:
        return 0, (out.stderr or out.stdout).strip()[:200] or "ask-many exit %d" % out.returncode
    written = 0
    with open(labels_path, "a", encoding="utf-8") as fh:
        for doc in docs:
            if doc.get("error"):
                continue  # network failure: leave unlabeled, retry next run
            answers = doc.get("answers", {})
            cluster, general, lesson = (answers.get(k, {}) for k in ("cluster", "generalizable", "lesson_for"))
            # Raw answers, not act: whether a label counts is decided at read
            # time with the current power, so labels made under shadow start
            # counting once the hook is promoted.
            label = {
                "id": doc["id"], "version": version, "decision_id": doc.get("decision_id", ""),
                "cluster": cluster.get("choice"), "cluster_conf": cluster.get("confidence"),
                "generalizable": general.get("noul"),
                "lesson_for": lesson.get("choice"), "lesson_conf": lesson.get("confidence"),
            }
            labels[label["id"]] = label
            fh.write(json.dumps(label) + "\n")
            written += 1
    errors = sum(1 for d in docs if d.get("error"))
    return written, ("%d rows failed; rerun --classify" % errors) if errors else ""


def tally(rows, win, labels, level, act_at):
    inside = in_window(rows, win)
    prs = {r.get("pr_ref") for r in inside if r.get("pr_ref")}
    miss = [r for r in inside if missed(r)]
    clusters, lessons, unclustered = {}, {}, []
    one_off = jev_used = 0
    for row in miss:
        cluster, is_one_off, lesson = judged(labels.get(row.get("id")), level, act_at)
        if is_one_off:
            one_off += 1
            continue
        if cluster:
            jev_used += 1
            names = [] if cluster == OTHER else [cluster]
        else:
            names = regex_clusters(row)
        for name in names:
            clusters.setdefault(name, []).append(row)
            if lesson:
                lessons.setdefault(name, Counter())[lesson] += 1
        if not names:
            unclustered.append(row)
    return {"human": len(inside), "prs": len(prs), "missed": len(miss) - one_off, "one_off": one_off,
            "jev_used": jev_used, "clusters": clusters, "lessons": lessons, "unclustered": unclustered}


def trend(now, prev, now_prs, prev_prs):
    if now_prs < MIN_PRS or prev_prs < MIN_PRS:
        return "need data"
    a, b = now / now_prs, prev / prev_prs
    if b == 0:
        return "new" if a else "="
    ratio = a / b
    return "down" if ratio <= 0.75 else "up" if ratio >= 1.25 else "="


def lesson_of(counter):
    """Majority lesson target, only when it holds most acted labels."""
    if not counter:
        return "-"
    name, n = counter.most_common(1)[0]
    return name if n * 2 > sum(counter.values()) else "mixed"


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--file", default=None)
    ap.add_argument("--since", default="30", help="days back from --until, or a start date")
    ap.add_argument("--until", default="", help="end date, default today (UTC)")
    ap.add_argument("--classify", action="store_true", help="label unlabeled misses with Jev (needs TYPESAFE_API_KEY)")
    ap.add_argument("--replay", default=None, help="with --classify: Jev response file for every item (tests)")
    ap.add_argument("--power", default=None, help="power for insight.classify this run (shadow|cautious|balanced|bold)")
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

    labels_path = path.with_name("labels.jsonl")
    version = catalog_version()
    labels = load_labels(labels_path, version)
    note = ""
    if args.classify:
        todo = [r for r in in_window(rows, cur_win) + in_window(rows, prev_win) if missed(r)]
        written, note = classify(todo, labels, labels_path, version, args.replay)
        note = "classify: %d new labels%s" % (written, "; " + note if note else "")
    level, act_at = gate(args.power)
    cur, prev = tally(rows, cur_win, labels, level, act_at), tally(rows, prev_win, labels, level, act_at)

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
            "lesson": lesson_of(cur["lessons"].get(name)),
            "examples": [r.get("generalized_pattern", "")[:140] for r in now_rows[:3]],
        })
    table.sort(key=lambda t: (-t["obs"], t["cluster"]))
    keywords = Counter(k.lower() for r in cur["unclustered"] for k in (r.get("context_keywords") or []))

    if args.json:
        print(json.dumps({"window": [d.isoformat() for d in cur_win], "previous": [d.isoformat() for d in prev_win],
                          "human": cur["human"], "prs": cur["prs"], "missed": cur["missed"],
                          "one_off": cur["one_off"], "jev_clustered": cur["jev_used"], "power": level,
                          "prev_prs": prev["prs"], "prev_missed": prev["missed"], "clusters": table,
                          "unclustered": len(cur["unclustered"]),
                          "unclustered_keywords": keywords.most_common(10), "note": note}, indent=2))
        return 0

    if note:
        print(note)
    print("lookback %s..%s vs %s..%s" % (cur_win[0], cur_win[1], prev_win[0], prev_win[1]))
    print("human comments %d on %d PRs, missed %d  |  previous: %d missed on %d PRs" % (
        cur["human"], cur["prs"], cur["missed"], prev["missed"], prev["prs"]))
    labeled = sum(1 for r in in_window(rows, cur_win) if missed(r) and r.get("id") in labels)
    if labeled:
        print("jev (%s): %d of %d misses labeled, %d clustered by label, %d dropped as one-off%s" % (
            level, labeled, cur["missed"] + cur["one_off"], cur["jev_used"], cur["one_off"],
            "; shadow counts none, see /bulma report --hook insight.classify" if level == "shadow" else ""))
    if not table:
        print("no clustered misses in either window")
    else:
        print()
        print("| cluster | obs | PRs | crit | per PR | prev per PR | trend | lesson | guard |")
        print("|---|---|---|---|---|---|---|---|---|")
        for t in table:
            print("| %s | %d | %d | %d | %.2f | %.2f | %s | %s | %s |" % (
                t["cluster"], t["obs"], t["prs"], t["critical"], t["per_pr"], t["prev_per_pr"],
                t["trend"], t["lesson"], t["guard"]))
    if cur["unclustered"]:
        print()
        print("unclustered: %d missed rows match no cluster. Top keywords: %s" % (
            len(cur["unclustered"]), ", ".join("%s (%d)" % kv for kv in keywords.most_common(8)) or "none"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
