#!/usr/bin/env bash
# Snapshot the delivery world for /bulma: bus stack, .ruver-* STATEs, the
# user's open PRs, and ranked candidates. Read-only apart from world.json and
# candidates.json. No Jev call. gh is optional; without it prs is null.
set -euo pipefail

usage() {
  echo "usage: world.sh [--ruver-root DIR] [--pr URL] [--limit N] [--out FILE]" >&2
}

ROOT_OVERRIDE="" PR_URL="" LIMIT=10 OUT=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --ruver-root) ROOT_OVERRIDE="$2"; shift 2 ;;
    --pr) PR_URL="$2"; shift 2 ;;
    --limit) LIMIT="$2"; shift 2 ;;
    --out) OUT="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) usage; exit 4 ;;
  esac
done

resolve_root() {
  if [[ -n "$ROOT_OVERRIDE" ]]; then
    echo "$ROOT_OVERRIDE"
    return
  fi
  local top slug home
  top="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
  slug="$(echo "$top" | sed 's|^/||; s|/|-|g')"
  home="${RUVER_HOME:-$HOME/.ruver}"
  if [[ ! -e "$home" && -d "$HOME/.grok/ruver" ]]; then
    home="$HOME/.grok/ruver"
  fi
  echo "$home/$slug"
}

ROOT="$(resolve_root)"
if [[ -z "$OUT" ]]; then
  mkdir -p "$ROOT/.ruver-bulma"
  OUT="$ROOT/.ruver-bulma/world.json"
fi
mkdir -p "$(dirname "$OUT")"

python3 - "$ROOT" "$OUT" "$PR_URL" "$LIMIT" <<'PY'
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone

root, out, pr_url, limit = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
warnings = []
GRAPHS = ("developer", "qa", "reviewer", "lstm", "triage", "goal")
FIELDS = "number,url,title,isDraft,headRefOid,mergeable,reviewDecision,statusCheckRollup,author"
RANK = {"resume": 0, "lstm": 1, "reviewer": 2, "qa": 3, "qa_waiting": 4, "nothing": 9}


def frontmatter(path):
    try:
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
    except OSError:
        return {}, ""
    match = re.match(r"^---\n(.*?)\n---", text, re.S)
    # Older STATE files have no frontmatter: bare `key: value` lines under the
    # title, up to the first section heading.
    head = match.group(1) if match else text.split("\n## ", 1)[0]
    fields = {}
    for line in head.splitlines():
        if re.match(r"^[a-z_]+:", line):
            key, _, value = line.partition(":")
            fields.setdefault(key.strip(), value.strip().strip("\"'"))
    return fields, text


def read_lines(path):
    try:
        with open(path, encoding="utf-8") as handle:
            return [line.strip() for line in handle if line.strip()]
    except OSError:
        return []


def gh(*args):
    try:
        result = subprocess.run(["gh", *args], capture_output=True, text=True, timeout=30)
    except (FileNotFoundError, subprocess.TimeoutExpired) as err:
        warnings.append("gh %s failed: %s" % (args[0], err.__class__.__name__))
        return None
    if result.returncode != 0:
        warnings.append("gh %s failed: %s" % (" ".join(args[:2]), result.stderr.strip()[:120]))
        return None
    return result.stdout


def ci_from(rollup):
    states = {str(c.get("conclusion") or c.get("state") or "").upper() for c in rollup or []}
    if not states:
        return "unknown"
    if states & {"FAILURE", "ERROR", "TIMED_OUT", "CANCELLED", "ACTION_REQUIRED", "STARTUP_FAILURE"}:
        return "red"
    if states & {"PENDING", "IN_PROGRESS", "QUEUED", "WAITING", "EXPECTED", "REQUESTED", ""}:
        return "pending"
    if states <= {"SUCCESS", "NEUTRAL", "SKIPPED", "COMPLETED"}:
        return "green"
    return "unknown"


def repo_of(url):
    match = re.search(r"github\.com/([^/]+)/([^/]+)/pull/(\d+)", url or "")
    return (match.group(1), match.group(2), int(match.group(3))) if match else (None, None, None)


def unresolved_threads(owner, repo, number):
    query = ("query($o:String!,$r:String!,$n:Int!){repository(owner:$o,name:$r)"
             "{pullRequest(number:$n){reviewThreads(first:100){nodes{isResolved}}}}}")
    raw = gh("api", "graphql", "-f", "query=" + query, "-F", "o=" + owner, "-F", "r=" + repo, "-F", "n=%d" % number)
    if raw is None:
        return None
    try:
        nodes = json.loads(raw)["data"]["repository"]["pullRequest"]["reviewThreads"]["nodes"]
    except (KeyError, TypeError, ValueError):
        return None
    return sum(1 for node in nodes if not node.get("isResolved"))


def qa_marker_on_head(owner, repo, number, sha):
    raw = gh("api", "repos/%s/%s/issues/%d/comments" % (owner, repo, number), "--paginate", "--jq", ".[].body")
    if raw is None:
        return None
    return any(re.search(r"<!--\s*ruver-qa:.*sha=" + re.escape(sha), body) for body in raw.split("\n"))


def shape(pr, user):
    owner, repo, number = repo_of(pr.get("url", ""))
    sha = pr.get("headRefOid", "") or ""
    login = (pr.get("author") or {}).get("login", "") or ""
    return {
        "number": pr.get("number"),
        "url": pr.get("url"),
        "title": pr.get("title"),
        "is_draft": bool(pr.get("isDraft")),
        "head_sha": sha,
        "mergeable": pr.get("mergeable"),
        "review_decision": pr.get("reviewDecision") or "",
        "ci": ci_from(pr.get("statusCheckRollup")),
        "unresolved_threads": unresolved_threads(owner, repo, number) if owner else None,
        "qa_marker_on_head": qa_marker_on_head(owner, repo, number, sha) if owner and sha else None,
        "author": login,
        "author_is_user": bool(user) and login == user,
    }

bus = os.path.join(root, ".ruver-bus")
stack = read_lines(os.path.join(bus, "STACK.md"))
env_fields, _ = frontmatter(os.path.join(bus, "ENVELOPE.md"))
envelope = {k: env_fields.get(k, "") for k in ("type", "from", "to", "pr_url", "job_id")} if env_fields else None
jobs_fields, _ = frontmatter(os.path.join(bus, "JOBS.md"))
jobs = {
    "qa_active": jobs_fields.get("qa_active", ""),
    "qa_claimed_at": jobs_fields.get("qa_claimed_at", ""),
    "qa_waiting": [x.strip() for x in jobs_fields.get("qa_waiting", "").split(",") if x.strip()],
}

states = []
if os.path.isdir(root):
    for name in sorted(os.listdir(root)):
        if not name.startswith(".ruver-") or name in (".ruver-bus", ".ruver-bulma"):
            continue
        path = os.path.join(root, name, "STATE.md")
        if not os.path.isfile(path):
            continue
        fields, text = frontmatter(path)
        question = fields.get("waiting_user", "")
        if not question and fields.get("status") == "waiting_user":
            match = re.search(r"\*\*Question:\*\*\s*(.+)", text)
            question = match.group(1).strip() if match else ""
        states.append({
            "graph": name[len(".ruver-"):],
            "status": fields.get("status", ""),
            "job_id": fields.get("job_id", ""),
            "pr_url": fields.get("pr_url", ""),
            "sha": fields.get("sha", ""),
            "waiting_user": question,
            "updated_at": fields.get("updated_at", ""),
        })

prs = None
pr_given = None
user = ""
if gh("--version") is not None and gh("auth", "status") is not None:
    user = (gh("api", "user", "--jq", ".login") or "").strip()
    raw = gh("pr", "list", "--author", "@me", "--state", "open", "--limit", str(limit), "--json", FIELDS)
    if raw is not None:
        try:
            prs = [shape(pr, user) for pr in json.loads(raw)]
        except ValueError:
            warnings.append("gh pr list returned invalid JSON")
    if pr_url:
        raw = gh("pr", "view", pr_url, "--json", FIELDS)
        if raw:
            try:
                pr_given = shape(json.loads(raw), user)
            except ValueError:
                warnings.append("gh pr view returned invalid JSON")
else:
    warnings.append("gh not found or not authenticated: prs omitted")

# PRs /bulma watch already saw merged or closed: nothing left to resume.
try:
    with open(os.path.join(os.path.dirname(root), "bulma-watch.json"), encoding="utf-8") as handle:
        closed = json.load(handle).get("closed", {})
except (OSError, ValueError, AttributeError):
    closed = {}

candidates = []
for state in states:
    if state["pr_url"] in closed:
        continue
    if state["status"] in ("waiting_user", "escalated"):
        job = state["job_id"] or state["graph"]
        why = "%s %s since %s" % (state["graph"], state["status"], state["updated_at"] or "unknown")
        if state["waiting_user"]:
            why += ": " + state["waiting_user"][:120]
        target = state["graph"] if state["graph"] in GRAPHS else "developer"
        candidates.append({"id": "resume:" + job, "target": target, "args": "resume", "why": why, "rank": RANK["resume"]})
for pr in prs or []:
    number = pr["number"]
    if pr["review_decision"] == "CHANGES_REQUESTED" or (pr["unresolved_threads"] or 0) > 0:
        candidates.append({"id": "lstm:pr-%s" % number, "target": "lstm", "args": pr["url"],
                           "why": "%s unresolved review threads, %s" % (pr["unresolved_threads"] or 0, pr["review_decision"] or "no decision"),
                           "rank": RANK["lstm"]})
    elif pr["ci"] == "red":
        candidates.append({"id": "reviewer:pr-%s" % number, "target": "reviewer", "args": pr["url"], "why": "CI red", "rank": RANK["reviewer"]})
    elif pr["ci"] == "green" and pr["mergeable"] == "MERGEABLE" and pr["qa_marker_on_head"] is False:
        candidates.append({"id": "qa:pr-%s" % number, "target": "qa", "args": pr["url"],
                           "why": "CI green, MERGEABLE, no QA comment on head SHA", "rank": RANK["qa"]})
for job in jobs["qa_waiting"]:
    candidates.append({"id": "qa:" + job, "target": "qa", "args": job, "why": "parked in qa_waiting", "rank": RANK["qa_waiting"]})
candidates.append({"id": "nothing", "target": "none", "args": "", "why": "no open item, or start new work", "rank": RANK["nothing"]})
candidates.sort(key=lambda c: c["rank"])
for candidate in candidates:
    candidate.pop("rank")

world = {
    "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "ruver_root": root,
    "user": user,
    "stack": stack,
    "stack_top": stack[-1] if stack else "",
    "envelope": envelope,
    "jobs": jobs,
    "states": states,
    "prs": prs,
    "pr": pr_given,
    "candidates": candidates,
    "warnings": warnings,
}
with open(out, "w", encoding="utf-8") as handle:
    json.dump(world, handle, indent=2)
with open(os.path.join(os.path.dirname(out), "candidates.json"), "w", encoding="utf-8") as handle:
    json.dump({"candidate": {c["id"]: c["why"] for c in candidates}}, handle, indent=2)
print("world: %s" % out)
print("stack_top=%s qa_active=%s states=%d prs=%s" % (world["stack_top"], jobs["qa_active"], len(states), "null" if prs is None else len(prs)))
print("candidates: " + ", ".join(c["id"] for c in candidates))
for warning in warnings:
    print("warn: " + warning)
PY
