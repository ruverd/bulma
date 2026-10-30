#!/usr/bin/env python3
"""Mechanical gate in front of every review POST.

Reads the preflight cache in --dir and the review payload, then exits:
  0  post the payload as written
  1  blocked: DEFER instead (reasons on stdout, one per line)
  3  bot quorum: post the same body as a COMMENT review, not an APPROVE

Run it as `gate.py ... && gh api .../reviews -X POST --input "$PAYLOAD"`.
Missing or unreadable evidence blocks; it never passes.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

MARKER = re.compile(r"<!--\s*bulma-review:(.*?)-->", re.S)
PAIR = re.compile(r"(\w+)=(\S+)")
ROW = re.compile(r"^\|\s*([^|]+?)\s*\|\s*(.*?)\s*\|\s*$", re.M)
REQUIRED_ROWS = ("Model", "Reasoning effort", "Reviewed head", "CI", "Review context", "Human sign-off", "Coverage")
BUILD_TEST = re.compile(
    r"\b(build|builds|test|tests|unit|integration|e2e|jest|vitest|playwright|cypress|pytest)\b", re.I
)
FAILED = {"failure", "timed_out", "cancelled", "action_required", "startup_failure", "stale", "error"}
DECISIVE = {"APPROVED", "CHANGES_REQUESTED", "DISMISSED"}
DEEP_REASONS = {"coverage", "uncertainty", "critic_failed"}
# AI QA verdict prefix. FAIL needs human approval; BLOCKED (QA could not run) does not gate.
QA_FAIL = re.compile(r"^FAIL(ED)?\b", re.I)


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


def is_bot(user: dict[str, Any], bots: set[str]) -> bool:
    name = (user.get("login") or "").lower()
    return user.get("type") == "Bot" or name.endswith("[bot]") or name in bots


def room(reviews: list[dict[str, Any]], timeline: list[dict[str, Any]], me: str) -> list[str]:
    reasons = []
    latest: dict[str, dict[str, Any]] = {}
    for review in sorted(reviews, key=lambda r: r.get("submitted_at") or ""):
        if review.get("state") in DECISIVE and login(review) != me:
            latest[login(review)] = review
    for who, review in latest.items():
        if review["state"] == "CHANGES_REQUESTED":
            reasons.append(f"open change request from {who}: {review.get('html_url', '')}")
    by_id = {r.get("id"): r for r in reviews}
    for event in timeline:
        if event.get("event") != "review_dismissed":
            continue
        dismissed = event.get("dismissed_review") or {}
        review = by_id.get(dismissed.get("review_id"))
        if dismissed.get("state", "").lower() != "changes_requested" or not review:
            continue
        reviewer = login(review)
        if reviewer in (me, login(event)):
            continue
        cleared = any(
            login(r) == reviewer and r.get("state") == "APPROVED"
            and (r.get("submitted_at") or "") > (event.get("created_at") or "")
            for r in reviews
        )
        if not cleared:
            reasons.append(f"change request from {reviewer} dismissed by {login(event)}, never cleared")
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


def threads(pages: Any, reviews: list[dict[str, Any]], head: str) -> list[str]:
    """Unresolved threads block, except notes from someone who approved this head.

    Their APPROVED review is the decision. A thread with no author still blocks.
    An approval on an older SHA does not cover a thread on the current head.
    """
    cleared = approved_on_head(reviews, head)
    reasons = []
    for page in pages if isinstance(pages, list) else [pages]:
        if page.get("errors") or not page.get("data"):
            raise Missing("threads.json has GraphQL errors or null data")
        nodes = page["data"]["repository"]["pullRequest"]["reviewThreads"]["nodes"]
        for node in nodes:
            if node.get("isResolved"):
                continue
            first = (node.get("comments", {}).get("nodes") or [{}])[0]
            if thread_author(first) in cleared:
                continue
            reasons.append(f"unresolved thread: {first.get('url', node.get('id'))}")
    return reasons


def latest_by(items: list[dict[str, Any]], key: str, order: str) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for item in sorted(items, key=lambda i: i.get(order) or 0):
        out[item.get(key) or ""] = item
    return out


def ci(checks: list[dict[str, Any]], statuses: list[dict[str, Any]], head: str, out_of_scope: bool = False) -> list[str]:
    reasons, green = [], False
    runs = latest_by([c for c in checks if c.get("head_sha") == head], "name", "id")
    for name, run in runs.items():
        title = ((run.get("output") or {}).get("title") or "").strip()
        if QA_FAIL.match(title):
            reasons.append(f"needs human approval: check {name} says {title}")
        if not BUILD_TEST.search(name):
            continue
        if run.get("status") != "completed":
            reasons.append(f"build/test check pending: {name}")
        elif run.get("conclusion") in FAILED:
            reasons.append(f"build/test check {run['conclusion']}: {name}")
        elif run.get("conclusion") == "success":
            green = True
    for context, status in latest_by(statuses, "context", "created_at").items():
        description = (status.get("description") or "").strip()
        if QA_FAIL.match(description):
            reasons.append(f"needs human approval: status {context} says {description}")
        if BUILD_TEST.search(context):
            if status.get("state") == "success":
                green = True
            else:
                reasons.append(f"build/test status {status.get('state')}: {context}")
    if not green and not out_of_scope:
        reasons.append(f"no successful build/test check ran on {head}")
    return reasons


def needs_deep(reviews: list[dict[str, Any]], comments: list[dict[str, Any]], me: str) -> bool:
    mine = [(r.get("submitted_at") or "", r.get("state"), r.get("body")) for r in reviews if login(r) == me]
    mine += [(c.get("created_at") or "", "DEFER", c.get("body")) for c in comments
             if login(c) == me and marker(c.get("body") or "")]
    pending = False
    for _, state, body in sorted(mine, key=lambda m: m[0]):
        mark = marker(body or "")
        if state == "CHANGES_REQUESTED" or (state == "DEFER" and mark.get("reason") in DEEP_REASONS):
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


def approval(args: argparse.Namespace, body: str, data: dict[str, Any]) -> list[str]:
    rows = {name.strip(): value for name, value in ROW.findall(body)}
    mark = marker(body)
    reasons = room(data["reviews"], data["timeline"], args.me)
    reasons += threads(data["threads"], data["reviews"], args.head)
    reasons += ci(data["checks"], data["statuses"], args.head, data["ci_scope"].get("scope") == "out_of_scope")
    signoff = load(Path(args.signoff)) if args.signoff else None
    if not isinstance(signoff, list):
        reasons.append("human sign-off evidence missing (--signoff)")
    if not rows.get("Review context", "").lower().startswith("clear"):
        reasons.append("Review context row is not clear")
    if mark.get("blockers") != "0" or mark.get("majors") != "0" or mark.get("open") != "-":
        reasons.append("marker still lists blockers, majors or open findings")
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
                if finding.get("severity") not in ("blocker", "major"):
                    continue
                if bucket == "dropped" and finding.get("pre_existing") is True:
                    continue
                reasons.append(f"{finding['severity']} in ledger ({bucket}): {finding.get('title', '?')}")
    return reasons


def bot_quorum(reviews: list[dict[str, Any]], args: argparse.Namespace, bots: set[str]) -> bool:
    others: dict[str, dict[str, Any]] = {}
    for review in sorted(reviews, key=lambda r: r.get("submitted_at") or ""):
        if review.get("state") in DECISIVE and login(review) != args.me:
            others[login(review)] = review
    approvers = [r for r in others.values() if r["state"] == "APPROVED" and r.get("commit_id") == args.head]
    return bool(approvers) and all(is_bot(r.get("user") or {}, bots) for r in approvers)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dir", required=True, help="preflight cache ($BULMA_ROOT/.bulma-code-review)")
    parser.add_argument("--payload", required=True, help="review payload JSON about to be POSTed")
    parser.add_argument("--me", required=True)
    parser.add_argument("--head", required=True, help="live headRefOid")
    parser.add_argument("--signoff", help="classify-risk.py --human-signoff output")
    parser.add_argument("--ledger", help="bind-findings.py output for this pass")
    parser.add_argument("--bot-login", action="append", default=[], help="reviewer login that is a bot")
    args = parser.parse_args()
    args.me = args.me.lower()
    bots = {b.lower() for b in args.bot_login} | {args.me}
    root = Path(args.dir)
    try:
        payload = load(Path(args.payload))
        event, body = payload.get("event", ""), payload.get("body", "")
        reasons = template(body, args.head)
        if payload.get("commit_id") != args.head:
            reasons.append("payload commit_id is not the live head")
        if event == "APPROVE":
            data = {
                "reviews": flat(load(root / "reviews.json")),
                "comments": flat(load(root / "comments.json")),
                "timeline": flat(load(root / "timeline.json")),
                "threads": load(root / "threads.json"),
                "checks": flat(load(root / "checks.json"), "check_runs"),
                "statuses": flat(load(root / "statuses.json")),
                "ci_scope": load(root / "ci-scope.json") if (root / "ci-scope.json").exists() else {},
            }
            reasons += approval(args, body, data)
    except (Missing, KeyError, TypeError, AttributeError) as exc:
        reasons = [f"gate could not read evidence: {exc}"]
        event = ""
    if reasons:
        print("\n".join(f"BLOCKED {reason}" for reason in reasons))
        return 1
    if event == "APPROVE" and bot_quorum(data["reviews"], args, bots):
        print("BOT_QUORUM only bot approvals on this head; post a COMMENT review instead")
        return 3
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
