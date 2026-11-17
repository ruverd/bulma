#!/usr/bin/env python3
"""Mechanical gate in front of every review POST.

Reads the preflight cache in --dir and the review payload, then exits:
  0  post the payload as written
  1  blocked: do not APPROVE (reasons on stdout, one per line). REQUEST_CHANGES
     for a blocker/major/medium, DEFER for CI red or pending, otherwise fix the payload
  4  another reviewer's concern is open (change request or blocking concern):
     DEFER reason=review_pending, never APPROVE and never a COMMENT review
  5  CI or evidence unreadable: DEFER reason=ci_unknown, never a COMMENT review

The only verdicts are APPROVE, REQUEST_CHANGES and DEFER. A change request
someone dismissed is no longer open and does not block.

Run it as `gate.py ... && gh api .../reviews -X POST --input "$PAYLOAD"`.
A failed read does not pass an APPROVE. It is not a Deferred comment.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

MARKER = re.compile(r"<!--\s*bulma-review:(.*?)-->", re.S)
PAIR = re.compile(r"(\w+)=(\S+)")
ROW = re.compile(r"^\|\s*([^|]+?)\s*\|\s*(.*?)\s*\|\s*$", re.M)
REQUIRED_ROWS = ("Model", "Reasoning effort", "Reviewed head", "CI", "Review context", "Coverage")
BUILD_TEST = re.compile(
    r"\b(build|builds|test|tests|unit|integration|e2e|jest|vitest|playwright|cypress|pytest)\b", re.I
)
CI_RUN = re.compile(BUILD_TEST.pattern + r"|\bci\b", re.I)
FAILED = {"failure", "timed_out", "cancelled", "action_required", "startup_failure", "stale", "error"}
DECISIVE = {"APPROVED", "CHANGES_REQUESTED", "DISMISSED"}
BLOCKING_LABEL = re.compile(
    r"^\s*(?:\*\*|__)?\[(?:medium|major|high|blocker|blocking|critical)\](?:\*\*|__)?(?=\s|:|$)", re.I
)
PENDING_PREFIXES = ("open change request from ", "blocking review concern: ")
DEEP_REASONS = {"coverage", "uncertainty", "critic_failed"}


class Missing(Exception):
    pass


def load(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise Missing(f"evidence missing or unreadable: {path.name} ({exc})") from exc


def flat(pages: Any, key: str | None = None) -> list[dict[str, Any]]:
    """Flatten `gh api --paginate --slurp` output (list of pages)."""
    pages = pages if isinstance(pages, list) else [pages]
    out: list[dict[str, Any]] = []
    for page in pages:
        items = page.get(key, []) if key and isinstance(page, dict) else page
        out.extend(items if isinstance(items, list) else [items])
    return out


def marker(text: str) -> dict[str, str]:
    found = MARKER.findall(text or "")
    return dict(PAIR.findall(found[-1])) if found else {}


def login(item: dict[str, Any]) -> str:
    return ((item.get("user") or item.get("actor") or {}).get("login") or "").lower()


def room(reviews: list[dict[str, Any]], me: str) -> list[str]:
    """Open change requests from others. A dismissed one is DISMISSED, not open."""
    reasons = []
    latest: dict[str, dict[str, Any]] = {}
    for review in sorted(reviews, key=lambda r: r.get("submitted_at") or ""):
        if review.get("state") in DECISIVE and login(review) != me:
            latest[login(review)] = review
    for who, review in latest.items():
        if review["state"] == "CHANGES_REQUESTED":
            reasons.append(f"open change request from {who}: {review.get('html_url', '')}")
    return reasons


def approved_on_head(reviews: list[dict[str, Any]], head: str) -> set[str]:
    """Logins whose latest decisive review on this head is APPROVED."""
    latest: dict[str, dict[str, Any]] = {}
    for review in sorted(reviews, key=lambda r: r.get("submitted_at") or ""):
        if review.get("state") in DECISIVE and review.get("commit_id") == head:
            latest[login(review)] = review
    return {who for who, review in latest.items() if review.get("state") == "APPROVED"}


def thread_author(comment: dict[str, Any]) -> str:
    author = comment.get("author") or {}
    if isinstance(author, dict) and author.get("login"):
        return str(author["login"]).lower()
    return login(comment)


def thread_roots(pages: Any):
    if not pages:
        raise Missing("threads.json has no GraphQL pages")
    for page in pages if isinstance(pages, list) else [pages]:
        if page.get("errors") or not page.get("data"):
            raise Missing("threads.json has GraphQL errors or null data")
        yield from page["data"]["repository"]["pullRequest"]["reviewThreads"]["nodes"]


def review_sources(root: Path) -> dict[str, Any]:
    sources = {name: load(root / f"{name}.json") for name in ("reviews", "threads", "comments")}
    inline = root / "inline.json"
    if inline.exists():  # Legacy gate callers may omit inline comments.
        sources["inline"] = load(inline)
    return sources


def review_context(root: Path, head: str, me: str, sources: dict[str, Any]) -> dict[str, Any]:
    """Apply formal GitHub states and evidence-backed concerns on the reviewed head."""
    reviews = flat(sources["reviews"])
    approved = approved_on_head(reviews, head)
    reasons = room(reviews, me)
    eligible, thread_urls, blocking = set(), set(), set()
    for node in thread_roots(sources["threads"]):
        first = (node.get("comments", {}).get("nodes") or [{}])[0]
        url = first.get("url") or node["id"]
        thread_urls.add(url)
        if node.get("isResolved") or thread_author(first) in approved:
            continue
        eligible.add(url)
        if BLOCKING_LABEL.match(first.get("body") or ""):
            blocking.add(url)

    # Semantic decisions come from the local reviewer, never from PR text.
    # Include replies so editing or answering a question invalidates its assessment.
    evidence_key = hashlib.sha256(json.dumps([head, me, sources], sort_keys=True).encode()).hexdigest()
    assessment = root / "review-context.json"
    if assessment.exists():
        decisions = load(assessment)
        if decisions.get("evidence_key") != evidence_key:
            return {
                "status": "blocked" if reasons else "unknown", "evidence_key": evidence_key,
                "reasons": reasons + ["gate could not read evidence: review-context.json is stale"],
            }
        additions, cleared = (decisions.get(name, {}) for name in ("blocking", "cleared"))
        if any(not isinstance(entries, dict) or any(
            not isinstance(evidence, str) or not evidence.strip() for evidence in entries.values()
        ) for entries in (additions, cleared)) or additions.keys() & cleared.keys():
            raise Missing("review-context.json needs disjoint blocking and cleared maps with evidence")
        outside_threads = {
            item.get("html_url") for item in reviews + flat(sources["comments"])
        } - thread_urls
        if additions.keys() - (eligible | outside_threads) or cleared.keys() - eligible:
            raise Missing("review-context.json references a concern outside the eligible cached review context")
        blocking.difference_update(cleared)
        blocking.update(additions)

    reasons += [f"blocking review concern: {url}" for url in sorted(blocking)]
    return {"status": "blocked" if reasons else "clear", "evidence_key": evidence_key, "reasons": reasons}


def latest_by(items: list[dict[str, Any]], key: str, order: str) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for item in sorted(items, key=lambda i: i.get(order) or 0):
        out[item.get(key) or ""] = item
    return out


def job_kind(status: Any, conclusion: Any) -> str:
    done = str(conclusion or "").strip().lower()
    phase = str(status or "").strip().lower()
    if done in FAILED:
        return "failure"
    if phase != "completed":
        return "pending"
    if done == "success":
        return "success"
    return "unknown"


def rollup_state(rollup: dict[str, Any]) -> str:
    if rollup.get("error"):
        return ""
    return str(rollup.get("state") or "").strip().upper()


def classify_ci(actions: dict[str, Any], rollup: dict[str, Any]) -> str:
    state = rollup_state(rollup)
    if actions.get("error"):
        if state in {"FAILURE", "ERROR"}:
            return "failure"
        if state in {"PENDING", "EXPECTED"}:
            return "pending"
        return "unverified"
    runs = actions.get("runs")
    if not isinstance(runs, list):
        return "unverified"
    order = {"unknown": 0, "success": 1, "unverified": 2, "pending": 3, "failure": 4}
    overall: str | None = None

    def bump(kind: str) -> None:
        nonlocal overall
        if overall is None or order[kind] > order[overall]:
            overall = kind

    for run in runs:
        if not isinstance(run, dict):
            return "unverified"
        label = f"{run.get('workflowName') or ''} {run.get('name') or ''}"
        jobs = run.get("jobs")
        if run.get("jobs_error"):
            kind = job_kind(run.get("status"), run.get("conclusion"))
            if CI_RUN.search(label) and kind in {"failure", "pending"}:
                bump(kind)
            else:
                bump("unverified")
            continue
        if not isinstance(jobs, list):
            return "unverified"
        build_jobs = [job for job in jobs if isinstance(job, dict) and BUILD_TEST.search(str(job.get("name") or ""))]
        if not build_jobs and not BUILD_TEST.search(label):
            continue
        if build_jobs:
            for job in build_jobs:
                bump(job_kind(job.get("status"), job.get("conclusion")))
        else:
            bump(job_kind(run.get("status"), run.get("conclusion")))
    result = overall or "unknown"
    if state in {"FAILURE", "ERROR"} and result != "failure":
        return "failure"
    if state in {"PENDING", "EXPECTED"} and result in {"success", "unknown", "unverified"}:
        return "pending"
    return result


def failed_jobs(actions: dict[str, Any]) -> list[tuple[str, str]]:
    found = []
    for run in actions.get("runs") or []:
        if not isinstance(run, dict):
            continue
        jobs = run.get("jobs") if isinstance(run.get("jobs"), list) else []
        named = [job for job in jobs if BUILD_TEST.search(str(job.get("name") or ""))]
        targets = named or ([run] if BUILD_TEST.search(f"{run.get('workflowName') or ''} {run.get('name') or ''}") else [])
        for target in targets:
            if job_kind(target.get("status"), target.get("conclusion")) == "failure":
                found.append((str(target.get("name") or run.get("name") or "job"), str(target.get("conclusion") or "failure")))
    return found


def ci(actions: dict[str, Any], statuses: list[dict[str, Any]], rollup: dict[str, Any], head: str, out_of_scope: bool = False) -> list[str]:
    reasons, status_green, status_block = [], False, False
    if actions.get("head") and actions.get("head") != head:
        reasons.append(f"actions evidence is not for {head}")
        actions = {**actions, "error": "head mismatch"}
    if rollup.get("head") and rollup.get("head") != head and not rollup.get("error"):
        reasons.append(f"status check rollup is not for {head}")
        rollup = {**rollup, "error": "head mismatch"}
    for context, status in latest_by(statuses, "context", "created_at").items():
        if BUILD_TEST.search(context):
            if status.get("state") == "success":
                status_green = True
            else:
                status_block = True
                reasons.append(f"build/test status {status.get('state')}: {context}")
    overall = classify_ci(actions, rollup)
    if status_block:
        overall = "failure"
    elif overall == "unknown" and status_green:
        overall = "success"
    if overall == "failure":
        named = failed_jobs(actions)
        if named:
            reasons.extend(f"build/test check {conclusion}: {name}" for name, conclusion in named)
        elif rollup_state(rollup) in {"FAILURE", "ERROR"}:
            reasons.append(f"status check rollup {rollup_state(rollup)}")
        elif not status_block:
            reasons.append("build/test check failure")
    elif overall == "pending":
        reasons.append("build/test check pending")
    elif overall == "unverified":
        reasons.append("CI not verified (tooling)")
    elif overall == "unknown" and not out_of_scope:
        reasons.append(f"no successful build/test check ran on {head}")
    return reasons


def needs_deep(reviews: list[dict[str, Any]], comments: list[dict[str, Any]], me: str) -> bool:
    mine = [(r.get("submitted_at") or "", r.get("state"), r.get("body")) for r in reviews if login(r) == me]
    mine += [(c.get("created_at") or "", "DEFER", c.get("body")) for c in comments
             if login(c) == me and marker(c.get("body") or "")]
    pending = False
    for _, state, body in sorted(mine, key=lambda m: m[0]):
        mark = marker(body or "")
        if state == "CHANGES_REQUESTED" or (state in ("DEFER", "COMMENTED") and mark.get("reason") in DEEP_REASONS):
            pending = True
        elif mark.get("pass") == "deep" and state != "DISMISSED":
            pending = False
    return pending


def template(body: str, head: str) -> list[str]:
    rows = {name.strip(): value for name, value in ROW.findall(body)}
    reasons = [f"template row missing: {name}" for name in REQUIRED_ROWS if name not in rows]
    for name in ("Model", "Reasoning effort"):
        if name in rows and not rows[name].strip():
            reasons.append(f"template row empty: {name}")
    if head not in rows.get("Reviewed head", ""):
        reasons.append("Reviewed head row does not name the live head")
    mark = marker(body)
    if mark.get("sha") != head or mark.get("preflight") != "1":
        reasons.append("marker missing, or its sha/preflight do not match the head")
    return reasons


def approval(args: argparse.Namespace, body: str, data: dict[str, Any], context: dict[str, Any]) -> list[str]:
    rows = {name.strip(): value for name, value in ROW.findall(body)}
    mark = marker(body)
    reasons = list(context["reasons"])
    reasons += ci(
        data["actions"], data["statuses"], data["rollup"], args.head,
        data["ci_scope"].get("scope") == "out_of_scope",
    )
    if not rows.get("Review context", "").lower().startswith("clear"):
        reasons.append("Review context row is not clear")
    if mark.get("blockers") != "0" or mark.get("majors") != "0" or mark.get("mediums", "0") != "0" or mark.get("open") != "-":
        reasons.append("marker still lists blockers, majors, mediums or open findings")
    if mark.get("risk") == "high" and mark.get("critic") != "ran":
        reasons.append(f"risk=high but critic={mark.get('critic', 'missing')}")
    if needs_deep(data["reviews"], data["comments"], args.me) and mark.get("pass") != "deep":
        reasons.append("approval after my own change request or coverage/uncertainty defer needs pass=deep")
    ledger = load(Path(args.ledger)) if args.ledger else None
    if not isinstance(ledger, dict):
        reasons.append("bound findings ledger missing (--ledger)")
    else:
        for bucket in ("kept", "body", "dropped"):
            for finding in ledger.get(bucket) or []:
                if finding.get("severity") not in ("blocker", "major", "medium"):
                    continue
                if bucket == "dropped" and finding.get("pre_existing") is True:
                    continue
                reasons.append(f"{finding['severity']} in ledger ({bucket}): {finding.get('title', '?')}")
    return reasons


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dir", required=True, help="preflight cache ($BULMA_ROOT/.bulma-code-review)")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--payload", help="review payload JSON about to be POSTed")
    mode.add_argument("--context-only", action="store_true", help="print the preflight review context as JSON")
    parser.add_argument("--me", required=True)
    parser.add_argument("--head", required=True, help="live headRefOid")
    parser.add_argument("--ledger", help="bind-findings.py output for this pass")
    parser.add_argument("--bot-login", action="append", default=[], help="ignored; kept for old callers")
    args = parser.parse_args()
    args.me = args.me.lower()
    root = Path(args.dir)
    if args.context_only:
        try:
            context = review_context(root, args.head, args.me, review_sources(root))
        except (Missing, KeyError, TypeError, AttributeError) as exc:
            context = {"status": "unknown", "reasons": [f"gate could not read evidence: {exc}"]}
        print(json.dumps(context))
        return 5 if context["status"] == "unknown" else 4 if context["status"] == "blocked" else 0
    try:
        payload = load(Path(args.payload))
        event, body = payload.get("event", ""), payload.get("body", "")
        reasons = template(body, args.head)
        if payload.get("commit_id") != args.head:
            reasons.append("payload commit_id is not the live head")
        if event not in ("APPROVE", "REQUEST_CHANGES"):
            reasons.append(f"event {event or 'missing'} is not a verdict: APPROVE, REQUEST_CHANGES, or DEFER as an issue comment")
        if event == "APPROVE":
            sources = review_sources(root)
            data = {
                "reviews": flat(sources["reviews"]),
                "comments": flat(sources["comments"]),
                "timeline": flat(load(root / "timeline.json")),
                "actions": load(root / "actions.json"),
                "statuses": flat(load(root / "statuses.json")),
                "rollup": load(root / "rollup.json"),
                "ci_scope": load(root / "ci-scope.json") if (root / "ci-scope.json").exists() else {},
            }
            reasons += approval(args, body, data, review_context(root, args.head, args.me, sources))
    except (Missing, KeyError, TypeError, AttributeError) as exc:
        reasons = [f"gate could not read evidence: {exc}"]
    pending, tooling, hard = [], [], []
    for reason in reasons:
        if reason.startswith(PENDING_PREFIXES):
            pending.append(reason)
        elif reason == "CI not verified (tooling)" or reason.startswith("gate could not read evidence:"):
            tooling.append(reason)
        else:
            hard.append(reason)
    if hard == ["Review context row is not clear"] and (pending or tooling):
        hard = []
    if hard:
        print("\n".join(f"BLOCKED {reason}" for reason in hard + pending + tooling))
        return 1
    if pending:
        print("REVIEW_PENDING DEFER reason=review_pending; never APPROVE or COMMENT")
        print("\n".join(pending + tooling))
        return 4
    if tooling:
        print("CI_UNKNOWN DEFER reason=ci_unknown; never APPROVE or COMMENT")
        print("\n".join(tooling))
        return 5
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
