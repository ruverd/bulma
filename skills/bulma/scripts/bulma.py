#!/usr/bin/env python3
"""Bulma: ask TypeSafe Jev at bulma graph forks and log every answer.

Stdlib only. Subcommands: catalog, power, tune, model, doctor, state, ask,
ask-many, outcome, report, dispatch. Never prints TYPESAFE_API_KEY.

Exit codes: 0 ok, 2 requirement missing, 3 network or API, 4 bad input.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import http.client
import json
import math
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Skills install as plain folders: keep __pycache__ out of them.
sys.dont_write_bytecode = True
import decision_cache
import dispatch  # noqa: E402  (sibling module, after the bytecode switch)

API = "https://api.typesafe.ai/v1"
# Pin releases so an alias cannot change decisions between runs. Compare new
# models under shadow before retuning the catalog thresholds.
DEFAULT_MODEL = "jev-1.14.0"
DEFAULT_TIMEOUT = 8.0
ENTRY_TIMEOUT = 3.0
LEVELS = {"shadow": None, "cautious": 0.10, "balanced": 0.0, "bold": -0.10}
# Hooks that stay under this level until power_by_hook, env or flag names one.
HOOK_DEFAULT_POWER = {"dispatch.tier": "shadow", "insight.classify": "shadow"}
FLOOR = 0.50
CEIL = 0.99
PER_KEY_CAP = 8000
TOTAL_CAP = 90000
STAKES = ("low", "normal", "high")
TYPES = ("choice", "noul", "score")
TSV_COLUMNS = [
    "ts_iso", "decision_id", "hook", "question", "power", "model", "answer",
    "confidence", "act_at", "acted", "graph_answer", "outcome", "repo", "pr",
    "sha", "ticket", "note", "input_tokens", "latency_ms",
    "question_type", "policy_id", "source",
]
LOG_TAIL_LINES = 200
PR_BODY_CAP = 3000
REDACT = [
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"sk-[A-Za-z0-9_-]{16,}"),
    re.compile(r"apikey_[A-Za-z0-9_]{16,}"),
    re.compile(r"AKIA[A-Z0-9]{12,}"),
    re.compile(r"Bearer [A-Za-z0-9._~+/=-]{16,}"),
    re.compile(r"(?i)(password|passwd|secret|token)\s*[=:]\s*\S+"),
]
SKILL_DIR = Path(__file__).resolve().parent.parent
CATALOG_PATH = SKILL_DIR / "decisions.json"
REQUIREMENT = (
    "/bulma needs TypeSafe Jev.\n"
    "  missing: TYPESAFE_API_KEY  (create one at https://console.typesafe.ai)\n"
    "  python3: {py}\n"
    "Set the key, then run /bulma again.\n"
    "Without Jev, run the graph directly: /developer, /qa, /reviewer, /lstm, /bulma-triage."
)


class BulmaError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


# --- disk -------------------------------------------------------------------

def bulma_home():
    env = os.environ.get("BULMA_HOME")
    if env:
        return Path(env)
    return Path.home() / ".bulma"


def bulma_root(override=None):
    if override:
        return Path(override)
    try:
        top = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        top = os.getcwd()
    slug = top.lstrip("/").replace("/", "-")
    return bulma_home() / slug


def config_path():
    return bulma_home() / "bulma.json"


def load_config():
    path = config_path()
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError as err:
        raise BulmaError(4, "config %s is not valid JSON: %s" % (path, err))


def save_config(cfg):
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cfg, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def load_json_file(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise BulmaError(4, "file missing: %s" % path)
    except json.JSONDecodeError as err:
        raise BulmaError(4, "%s is not valid JSON: %s" % (path, err))


# --- catalog ----------------------------------------------------------------

def validate_catalog(data):
    errors = []
    hooks = data.get("hooks") if isinstance(data, dict) else None
    if not isinstance(hooks, list) or not hooks:
        return ['top level must be {"hooks": [...]}']
    seen = set()
    for hook in hooks:
        hid = hook.get("id", "<no id>")
        if hid in seen:
            errors.append("%s: duplicate id" % hid)
        seen.add(hid)
        for key in ("graph", "node", "fallback"):
            if not isinstance(hook.get(key), str) or not hook[key]:
                errors.append("%s: %s must be a non-empty string" % (hid, key))
        if hook.get("stakes") not in STAKES:
            errors.append("%s: stakes must be one of %s" % (hid, list(STAKES)))
        if not isinstance(hook.get("state_keys"), list) or not hook["state_keys"]:
            errors.append("%s: state_keys must be a non-empty list" % hid)
        questions = hook.get("questions")
        if not isinstance(questions, dict) or not questions:
            errors.append("%s: questions must be a non-empty map" % hid)
            continue
        for qid, question in questions.items():
            where = "%s.%s" % (hid, qid)
            qtype = question.get("type")
            if qtype not in TYPES:
                errors.append("%s: type must be one of %s" % (where, list(TYPES)))
            if not isinstance(question.get("instructions"), str) or not question["instructions"]:
                errors.append("%s: instructions required" % where)
            act_at = question.get("act_at")
            if not isinstance(act_at, (int, float)) or not FLOOR <= act_at <= CEIL:
                errors.append("%s: act_at must be within [%s, %s]" % (where, FLOOR, CEIL))
            if question.get("direction", "act") not in ("act", "ask"):
                errors.append("%s: direction must be act or ask" % where)
            criteria = question.get("criteria")
            if qtype == "choice":
                if criteria == "dynamic":
                    continue
                if not isinstance(criteria, dict) or not criteria:
                    errors.append('%s: choice criteria must be a non-empty map or "dynamic"' % where)
                elif not isinstance(question.get("enum_source"), str):
                    errors.append("%s: static choice needs enum_source" % where)
            elif qtype == "score":
                if not isinstance(criteria, list) or len(criteria) < 2:
                    errors.append("%s: score criteria must list at least two levels" % where)
            elif criteria is not None and (not isinstance(criteria, dict) or set(criteria) - {"true", "false"}):
                errors.append("%s: noul criteria keys must be true/false" % where)
    return errors


def load_catalog(path=CATALOG_PATH):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise BulmaError(4, "catalog missing: %s" % path)
    except json.JSONDecodeError as err:
        raise BulmaError(4, "catalog is not valid JSON: %s" % err)
    errors = validate_catalog(data)
    if errors:
        raise BulmaError(4, "catalog invalid:\n  " + "\n  ".join(errors))
    return {hook["id"]: hook for hook in data["hooks"]}


# --- power ------------------------------------------------------------------

def check_level(level):
    if level not in LEVELS:
        raise BulmaError(4, "unknown power level %r; use one of %s" % (level, ", ".join(LEVELS)))
    return level


def resolve_power(flag, hook, cfg):
    if flag:
        return check_level(flag), "flag"
    env = os.environ.get("BULMA_POWER")
    if env:
        return check_level(env), "env"
    by_hook = cfg.get("power_by_hook", {})
    if hook and hook in by_hook:
        return check_level(by_hook[hook]), "hook"
    if hook in HOOK_DEFAULT_POWER:
        return HOOK_DEFAULT_POWER[hook], "hook default"
    if cfg.get("power"):
        return check_level(cfg["power"]), "config"
    return "balanced", "default"


def effective_act_at(base, power, direction):
    offset = LEVELS[power]
    if offset is None:
        return round(float(base), 2)
    if direction == "ask":
        offset = -offset
    return round(min(CEIL, max(FLOOR, float(base) + offset)), 2)


# --- state hygiene ----------------------------------------------------------

def sanitize(value, budget):
    if isinstance(value, str):
        text = value
        for pattern in REDACT:
            text = pattern.sub("[redacted]", text)
        cap = min(PER_KEY_CAP, budget["remaining"])
        if len(text) > cap:
            text = text[: max(cap - 14, 0)] + "...[truncated]"
            budget["truncated"] = True
        budget["remaining"] = max(0, budget["remaining"] - len(text))
        return text
    if isinstance(value, dict):
        return {key: sanitize(item, budget) for key, item in value.items()}
    if isinstance(value, list):
        return [sanitize(item, budget) for item in value]
    return value


def missing_keys(state, keys):
    missing = []
    for key in keys:
        node = state
        found = True
        for part in key.split("."):
            if isinstance(node, dict) and part in node:
                node = node[part]
            else:
                found = False
                break
        if not found:
            missing.append(key)
    return missing


# --- request / response -----------------------------------------------------

def build_request(hook, state, model, criteria_override):
    questions = {}
    for qid, question in hook["questions"].items():
        body = {"type": question["type"], "instructions": question["instructions"]}
        criteria = question.get("criteria")
        if criteria == "dynamic":
            if qid not in criteria_override:
                raise BulmaError(4, "hook %s question %s needs --criteria FILE with key %r" % (hook["id"], qid, qid))
            criteria = criteria_override[qid]
        if criteria is not None:
            body["criteria"] = criteria
        questions[qid] = body
    return {"state": state, "model": model, "questions": questions}


def api_key():
    key = os.environ.get("TYPESAFE_API_KEY")
    if not key:
        raise BulmaError(2, "TYPESAFE_API_KEY is not set")
    return key


def decision_timeout(hook_id, cfg):
    default = ENTRY_TIMEOUT if hook_id.startswith("entry.") else DEFAULT_TIMEOUT
    value = cfg.get("timeout_by_hook", {}).get(hook_id, cfg.get("timeout_seconds", default))
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value) or value <= 0:
        raise BulmaError(4, "decision timeout must be a finite positive number")
    return float(value)


def post_json(path, body, timeout=DEFAULT_TIMEOUT):
    key = api_key()
    data = json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        API + path, data=data, method="POST",
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json", "User-Agent": "bulma"},
    )
    deadline = time.monotonic() + timeout
    delays = [1, 2, 4]
    for attempt in range(4):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise BulmaError(3, "decision timeout")
        try:
            with urllib.request.urlopen(request, timeout=remaining) as response:
                result = json.loads(response.read().decode("utf-8"))
            if time.monotonic() >= deadline:
                raise BulmaError(3, "decision timeout")
            if not isinstance(result, dict):
                raise BulmaError(3, "API response must be an object")
            return result
        except urllib.error.HTTPError as err:
            err.close()
            if err.code != 429 and err.code < 500:
                raise BulmaError(3, "HTTP %s" % err.code)
            if attempt == 3:
                raise BulmaError(3, "HTTP %s after 3 retries" % err.code)
            retry_after = err.headers.get("retry-after") if err.headers else None
            wait = float(retry_after) if retry_after and re.fullmatch(r"\d+(\.\d+)?", retry_after) else delays[attempt]
        except (urllib.error.URLError, TimeoutError, OSError, http.client.HTTPException) as err:
            if attempt == 3:
                raise BulmaError(3, "network: %s" % err)
            wait = delays[attempt]
        except (ValueError, UnicodeError):
            raise BulmaError(3, "API response is not valid JSON")
        remaining = deadline - time.monotonic()
        if wait >= remaining:
            raise BulmaError(3, "decision timeout before retry")
        time.sleep(wait)
    raise BulmaError(3, "unreachable")


def probability(value):
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and 0 <= value <= 1 and math.isfinite(value))


def valid_answer(question, raw):
    if not isinstance(raw, dict):
        return False
    kind = question["type"]
    if kind == "noul":
        return probability(raw.get("noul"))
    if not probability(raw.get("confidence")):
        return False
    value = raw.get(kind)
    criteria = question.get("criteria")
    if kind == "choice":
        return isinstance(value, str) and isinstance(criteria, dict) and value in criteria
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and 0 <= value <= 1 and math.isfinite(value))


def judge(question, raw, act_at, power, hook_id=""):
    if not valid_answer(question, raw):
        return {"act": False, "act_at": act_at, "invalid": True}
    live = power != "shadow"
    if str(hook_id).startswith("entry.") and power in ("cautious", "shadow"):
        live = False
    qtype = question["type"]
    if qtype == "noul":
        value = float(raw["noul"])
        if value == 0.5:
            decisive = "undecided"
        elif value >= act_at:
            decisive = "yes"
        elif value <= round(1 - act_at, 2):
            decisive = "no"
        else:
            decisive = "undecided"
        return {"noul": round(value, 3), "act_at": act_at, "decisive": decisive, "act": live and decisive != "undecided"}
    confidence = float(raw["confidence"])
    picked = raw.get("choice") if qtype == "choice" else raw.get("score")
    out = {qtype: picked, "confidence": round(confidence, 3), "act_at": act_at, "act": live and confidence >= act_at}
    if raw.get("probabilities") is not None:
        out["probabilities"] = raw["probabilities"]
    return out


def answer_value(judged):
    for key in ("choice", "score", "noul"):
        if key in judged:
            return judged[key]
    return ""


def confidence_value(judged):
    if "confidence" in judged:
        return judged["confidence"]
    return judged.get("noul", "")


# --- ledger -----------------------------------------------------------------

def clean(value):
    return re.sub(r"[\t\r\n]+", " ", "" if value is None else str(value))


def ledger_path(root):
    return Path(root) / ".bulma-core" / "DECISIONS.tsv"


def append_rows(root, rows, path=None, columns=TSV_COLUMNS):
    path = path or ledger_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        with path.open(encoding="utf-8") as handle:
            header = handle.readline().rstrip("\n").split("\t")
        if header != columns:
            # Ledger from an older column set: rewrite once under the current header.
            write_rows(path, read_rows(path, columns), columns)
    new = not path.exists()
    with path.open("a", encoding="utf-8") as handle:
        if new:
            handle.write("\t".join(columns) + "\n")
        for row in rows:
            handle.write("\t".join(clean(row.get(col, "")) for col in columns) + "\n")
    return path


def read_rows(path, columns=TSV_COLUMNS):
    """Rows keyed by the file's own header, so older ledgers stay readable."""
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return []
    if not lines:
        return []
    header = lines[0].split("\t")
    rows = []
    for line in lines[1:]:
        parts = line.split("\t")
        if len(parts) != len(header):
            continue
        row = dict.fromkeys(columns, "")
        row.update(zip(header, parts))
        rows.append(row)
    return rows


def write_rows(path, rows, columns=TSV_COLUMNS):
    Path(path).write_text(
        "\t".join(columns) + "\n" + "".join("\t".join(clean(r.get(c, "")) for c in columns) + "\n" for r in rows),
        encoding="utf-8",
    )


def rows_for(doc, hook, thresholds, graph_answers, context, note):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    input_tokens = (doc.get("usage") or {}).get("input_tokens", "")
    rows = []
    for qid in hook["questions"]:
        judged = doc["answers"].get(qid, {})
        rows.append({
            "ts_iso": ts,
            "decision_id": doc["decision_id"],
            "hook": hook["id"],
            "question": qid,
            "power": doc["power"],
            "model": doc["model"],
            "answer": answer_value(judged),
            "confidence": confidence_value(judged),
            "act_at": thresholds[qid],
            "acted": "true" if judged.get("act") else "false",
            "graph_answer": graph_answers.get(qid, ""),
            "outcome": "",
            "repo": context.get("repo", ""),
            "pr": context.get("pr", ""),
            "sha": context.get("sha", ""),
            "ticket": context.get("ticket", ""),
            "note": note,
            "input_tokens": input_tokens,
            "latency_ms": doc.get("latency_ms", ""),
            "question_type": hook["questions"][qid]["type"],
            "policy_id": doc.get("policy_id", ""),
            "source": doc.get("source", ""),
        })
    return rows


def new_decision_id(hook_id):
    return "%s-%s-%s" % (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"), hook_id, uuid.uuid4().hex[:4])


def parse_kv(items):
    out = {}
    for item in items or []:
        if "=" not in item:
            raise BulmaError(4, "expected key=value, got %r" % item)
        key, _, value = item.partition("=")
        out[key.strip()] = value.strip()
    return out


# --- output -----------------------------------------------------------------

def yaml_scalar(value):
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value)
    if re.fullmatch(r"[A-Za-z0-9_./:-]+", text):
        return text
    return json.dumps(text, ensure_ascii=False)


def yaml_inline(value):
    if isinstance(value, dict):
        return "{ " + ", ".join("%s: %s" % (yaml_scalar(k), yaml_inline(v)) for k, v in value.items()) + " }"
    if isinstance(value, list):
        return "[" + ", ".join(yaml_inline(v) for v in value) + "]"
    return yaml_scalar(value)


def to_yaml(doc):
    lines = []
    for key, value in doc.items():
        if key == "answers":
            lines.append("answers:")
            for qid, judged in value.items():
                shown = {k: v for k, v in judged.items() if k != "probabilities"}
                lines.append("  %s: %s" % (qid, yaml_inline(shown)))
        elif isinstance(value, (dict, list)):
            lines.append("%s: %s" % (key, yaml_inline(value)))
        else:
            lines.append("%s: %s" % (key, yaml_scalar(value)))
    return "\n".join(lines) + "\n"


def j_line(doc):
    """One overlay chat line, e.g. `J: path=debug_fix .88 ok · risk=elevated .61 -> fallback`."""
    if doc.get("error"):
        return "J: %s jev unavailable -> fallback [%s]" % (doc["hook"], doc["decision_id"])
    parts = []
    for qid, judged in doc["answers"].items():
        if "noul" in judged:
            shown = {"yes": "yes", "no": "no"}.get(judged.get("decisive"), "?")
            text = "%s=%s %.2f" % (qid, shown, judged["noul"])
        elif "confidence" in judged:
            text = "%s=%s %.2f" % (qid, answer_value(judged), judged["confidence"])
        else:
            text = "%s=none" % qid
        parts.append(text.replace(" 0.", " .") + (" ok" if judged.get("act") else " -> fallback"))
    prefix = "J(shadow):" if doc["power"] == "shadow" else "J:"
    return "%s %s %s [%s]" % (prefix, doc["hook"], " · ".join(parts), doc["decision_id"])


def emit(doc, fmt):
    if fmt == "json":
        print(json.dumps(doc, indent=2, ensure_ascii=False))
    elif fmt == "line":
        print(j_line(doc))
    else:
        sys.stdout.write(to_yaml(doc))


def output_format(args):
    if getattr(args, "json", False):
        return "json"
    return "line" if getattr(args, "line", False) else "yaml"


# --- commands ---------------------------------------------------------------

def cmd_catalog(args):
    catalog = load_catalog()
    if args.json:
        print(json.dumps(sorted(catalog), indent=2))
    else:
        print("ok %d hooks: %s" % (len(catalog), ", ".join(sorted(catalog))))
    return 0


def cmd_power(args):
    cfg = load_config()
    if args.action == "set":
        check_level(args.level)
        if args.hook:
            find_hook(load_catalog(), args.hook)
            cfg.setdefault("power_by_hook", {})[args.hook] = args.level
            path = save_config(cfg)
            print("power_by_hook[%s]=%s written to %s" % (args.hook, args.level, path))
            return 0
        cfg["power"] = args.level
        path = save_config(cfg)
        print("power=%s written to %s" % (args.level, path))
        return 0
    level, source = resolve_power(args.power, args.hook, cfg)
    print("%s (%s)" % (level, source))
    return 0


# --- state builders ---------------------------------------------------------
# Recipes from HOOKS.md that code can assemble from world.json and gh, so the
# orchestrator does not hand-write them. Hooks that need graph-local evidence
# (findings, comments, tickets) stay hand-built.

def trim_world(world):
    states = [
        {"graph": s.get("graph", ""), "status": s.get("status", ""), "waiting_user": s.get("waiting_user", "")}
        for s in world.get("states") or []
    ]
    return {"stack_top": world.get("stack_top"), "jobs": world.get("jobs") or {}, "states": states}


def load_world(args, root):
    path = Path(args.world) if args.world else root / ".bulma-core" / "world.json"
    if not path.exists():
        raise BulmaError(4, "no world.json at %s; run scripts/world.sh first" % path)
    return load_json_file(path)


def gh_pr_json(args, fields):
    if args.pr_json:
        return load_json_file(args.pr_json)
    if not args.pr:
        raise BulmaError(4, "needs --pr <number|url> or --pr-json FILE")
    cmd = ["gh", "pr", "view", str(args.pr), "--json", fields]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except FileNotFoundError:
        raise BulmaError(4, "gh not found; pass --pr-json FILE")
    except subprocess.CalledProcessError as err:
        raise BulmaError(4, "gh pr view failed: %s" % err.stderr.strip()[:200])
    return json.loads(result.stdout)


def pr_paths(pr):
    return [f.get("path", "") for f in pr.get("files") or []]


def build_entry_route(args, root):
    world = load_world(args, root)
    state = {"args": args.args or "", "world": trim_world(world), "user_login": world.get("user") or ""}
    if world.get("pr"):
        state["pr"] = world["pr"]
    return state, None


def build_entry_next_step(args, root):
    world = load_world(args, root)
    candidates = [
        {"id": c.get("id", ""), "target": c.get("target", ""), "why": c.get("why", "")}
        for c in world.get("candidates") or []
    ]
    if args.resume:
        candidates = [c for c in candidates if c["id"].startswith("resume:")]
        if not candidates:
            raise BulmaError(4, "resume: no resume:* candidate in world.json")
    criteria = {"candidate": {c["id"]: c["why"] or c["target"] for c in candidates}}
    return {"args": args.args or "", "candidates": candidates, "world": trim_world(world)}, criteria


def build_review_risk(args, root):
    pr = gh_pr_json(args, "title,body,files,changedFiles,additions,deletions")
    return {
        "pr_title": pr.get("title", ""),
        "pr_body": (pr.get("body") or "")[:PR_BODY_CAP],
        "files": pr_paths(pr),
        "changed_files": pr.get("changedFiles", len(pr.get("files") or [])),
        "churn": int(pr.get("additions") or 0) + int(pr.get("deletions") or 0),
    }, None


def build_failure_class(args, root):
    if not args.check_name or not args.log_file:
        raise BulmaError(4, "reviewer.failure_class needs --check-name and --log-file")
    pr = gh_pr_json(args, "files,mergeable")
    try:
        lines = Path(args.log_file).read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as err:
        raise BulmaError(4, "cannot read %s: %s" % (args.log_file, err))
    return {
        "check_name": args.check_name,
        "log_tail": "\n".join(lines[-LOG_TAIL_LINES:]),
        "pr": {"files": pr_paths(pr)},
        "same_fail_on_base": args.same_fail_on_base,
        "mergeable": pr.get("mergeable", ""),
    }, None


BUILDERS = {
    "entry.route": build_entry_route,
    "entry.next_step": build_entry_next_step,
    "review.risk": build_review_risk,
    "reviewer.failure_class": build_failure_class,
}


def save_state(root, hook_id, state, criteria):
    """Write the state (and dynamic criteria) under .bulma-core/state/, kept for humans."""
    folder = Path(root) / ".bulma-core" / "state"
    folder.mkdir(parents=True, exist_ok=True)
    stamp = "%s-%s" % (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"), uuid.uuid4().hex[:4])
    state_path = folder / ("%s-%s.json" % (hook_id, stamp))
    state_path.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    criteria_path = None
    if criteria is not None:
        criteria_path = folder / ("%s-%s.criteria.json" % (hook_id, stamp))
        criteria_path.write_text(json.dumps(criteria, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return state_path, criteria_path


def build_state(hook_id, args, root):
    builder = BUILDERS.get(hook_id)
    if not builder:
        raise BulmaError(4, "no state builder for %s (have: %s); write the state per HOOKS.md" % (hook_id, ", ".join(sorted(BUILDERS))))
    state, criteria = builder(args, root)
    return save_state(root, hook_id, state, criteria)


def cmd_state(args):
    load_catalog()
    state_path, criteria_path = build_state(args.hook, args, bulma_root(args.bulma_root))
    print(state_path)
    if criteria_path:
        print(criteria_path)
    return 0


# --- ask --------------------------------------------------------------------

def prepare(hook, state, cfg, power_flag, model, criteria):
    """Validate and build one request. Raises BulmaError(4) before any network call."""
    if not isinstance(state, (dict, list, str)):
        raise BulmaError(4, "state must be a JSON object, array or string")
    power, source = resolve_power(power_flag, hook["id"], cfg)
    budget = {"remaining": TOTAL_CAP, "truncated": False}
    missing = missing_keys(state if isinstance(state, dict) else {}, hook["state_keys"])
    if missing:
        raise BulmaError(4, "state missing key(s): %s" % ", ".join(missing))
    roots = {key.split(".")[0] for key in hook["state_keys"] + hook.get("optional_state_keys", [])}
    state = {key: value for key, value in state.items() if key in roots}
    request = build_request(hook, sanitize(state, budget), model, criteria)
    overrides = cfg.get("act_at", {})
    thresholds = {
        qid: effective_act_at(overrides.get("%s.%s" % (hook["id"], qid), q["act_at"]), power, q.get("direction", "act"))
        for qid, q in hook["questions"].items()
    }
    doc = {
        "hook": hook["id"], "decision_id": new_decision_id(hook["id"]), "model": model,
        "power": power, "power_source": source, "truncated": budget["truncated"], "warnings": [],
        "timeout_seconds": decision_timeout(hook["id"], cfg),
    }
    return request, thresholds, doc


def ask_one(hook, request, thresholds, doc, replay, graph_answers, context):
    """Send one prepared request (or read a replay). Returns (doc, ledger rows, exit code)."""
    started = time.monotonic()
    policy = hashlib.sha256(CATALOG_PATH.read_bytes() + Path(__file__).read_bytes()
                            + Path(decision_cache.__file__).read_bytes()).hexdigest()
    doc["policy_id"] = hashlib.sha256((policy + json.dumps(request["questions"], sort_keys=True)).encode()).hexdigest()[:16]
    doc["source"] = "replay" if replay else "live"
    if doc["truncated"]:
        doc["answers"] = {qid: {"act": False, "act_at": thresholds[qid], "fallback": hook["fallback"]}
                          for qid in hook["questions"]}
        doc["warnings"].append("truncated state: refresh relevant evidence before asking again")
        return doc, rows_for(doc, hook, thresholds, graph_answers, context, "truncated"), 0
    key = None if replay else decision_cache.cache_key(
        hook, request, thresholds, doc, graph_answers, context, policy)
    folder = bulma_home() / "jev-cache"
    response = decision_cache.read(folder, key)
    if response is not None and (not isinstance(response.get("answers"), dict) or not all(
            valid_answer(request["questions"][qid], response["answers"].get(qid)) for qid in hook["questions"])):
        response = None
    hit = response is not None
    doc["cache_hit"] = hit
    try:
        if not hit:
            response = load_json_file(replay) if replay else post_json("/systemone", request, timeout=doc["timeout_seconds"])
    except BulmaError as err:
        if err.code != 3:
            raise
        doc["latency_ms"] = int((time.monotonic() - started) * 1000)
        doc["error"] = {"code": 3, "message": str(err)}
        doc["answers"] = {qid: {"act": False, "act_at": thresholds[qid], "fallback": hook["fallback"]} for qid in hook["questions"]}
        return doc, rows_for(doc, hook, thresholds, graph_answers, context, ("error:" + str(err))[:80]), 3
    if not replay:
        doc["latency_ms"] = int((time.monotonic() - started) * 1000)
    if not isinstance(response, dict):
        response = {}
    doc["model"] = response.get("model") or doc["model"]
    answers = response.get("answers")
    if not isinstance(answers, dict):
        answers = {}
    doc["answers"] = {}
    for qid, question in hook["questions"].items():
        raw = answers.get(qid)
        if raw is None:
            doc["warnings"].append("no answer for %s" % qid)
            doc["answers"][qid] = {"act": False, "act_at": thresholds[qid], "fallback": hook["fallback"]}
            continue
        judged = judge(request["questions"][qid], raw, thresholds[qid], doc["power"], hook["id"])
        if judged.get("invalid"):
            doc["warnings"].append("invalid answer for %s" % qid)
        if not judged["act"]:
            judged["fallback"] = hook["fallback"]
        doc["answers"][qid] = judged
    usage = response.get("usage")
    doc["usage"] = {"input_tokens": 0} if hit else usage if isinstance(usage, dict) else {}
    complete = all(valid_answer(request["questions"][qid], answers.get(qid)) for qid in hook["questions"])
    if not hit and not replay and complete:
        decision_cache.write(folder, key, response)
    note = "cache_hit" if hit else ""
    rows = rows_for(doc, hook, thresholds, graph_answers, context, note)
    for row in rows:
        if not valid_answer(request["questions"][row["question"]], answers.get(row["question"])):
            row["note"] = "invalid_answer"
    return doc, rows, 0


def find_hook(catalog, hook_id):
    hook = catalog.get(hook_id)
    if not hook:
        raise BulmaError(4, "unknown hook %r; known: %s" % (hook_id, ", ".join(sorted(catalog))))
    return hook


def cmd_ask(args):
    catalog = load_catalog()
    hook = find_hook(catalog, args.hook)
    root = bulma_root(args.bulma_root)
    if args.build:
        if args.state or args.criteria:
            raise BulmaError(4, "--build writes the state itself; drop --state and --criteria")
        state_path, criteria_path = build_state(hook["id"], args, root)
    elif args.state:
        state_path, criteria_path = args.state, args.criteria
    else:
        raise BulmaError(4, "ask needs --state FILE or --build")
    cfg = load_config()
    model = args.model or cfg.get("model") or DEFAULT_MODEL
    criteria = load_json_file(criteria_path) if criteria_path else {}
    request, thresholds, doc = prepare(hook, load_json_file(state_path), cfg, args.power, model, criteria)
    if args.dry_run:
        print(json.dumps(request, indent=2, ensure_ascii=False))
        return 0
    doc, rows, code = ask_one(hook, request, thresholds, doc, args.replay, parse_kv(args.graph_answer), parse_kv(args.context))
    append_rows(root, rows)
    emit(doc, output_format(args))
    return code


def batch_items(path):
    data = load_json_file(path)
    items = data.get("items") if isinstance(data, dict) else data
    if not isinstance(items, list) or not items:
        raise BulmaError(4, "batch file needs a non-empty list, or {\"items\": [...]}")
    shared = data.get("context", {}) if isinstance(data, dict) else {}
    return items, shared


def kv_map(value, where):
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise BulmaError(4, "%s must be an object of key: value" % where)
    return {str(k): str(v) for k, v in value.items()}


def cmd_ask_many(args):
    """Many asks in one process: validate all, send in parallel, log once, one line each."""
    catalog = load_catalog()
    cfg = load_config()
    model = args.model or cfg.get("model") or DEFAULT_MODEL
    items, shared = batch_items(args.batch)
    base_context = dict(kv_map(shared, "context"), **parse_kv(args.context))
    jobs = []
    for index, item in enumerate(items):
        if not isinstance(item, dict) or "hook" not in item or "state" not in item:
            raise BulmaError(4, "item %d needs hook and state" % index)
        hook = find_hook(catalog, item["hook"])
        state = item["state"] if isinstance(item["state"], (dict, list)) else load_json_file(item["state"])
        criteria = item.get("criteria") or {}
        if isinstance(criteria, str):
            criteria = load_json_file(criteria)
        request, thresholds, doc = prepare(hook, state, cfg, args.power, model, criteria)
        context = dict(base_context, **kv_map(item.get("context"), "item %d context" % index))
        jobs.append((str(item.get("id", index)), hook, request, thresholds, doc, item.get("replay"),
                     kv_map(item.get("graph_answer"), "item %d graph_answer" % index), context))
    workers = max(1, min(args.workers, len(jobs)))
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(lambda job: (job[0],) + ask_one(*job[1:]), jobs))
    rows = [row for _, _, item_rows, _ in results for row in item_rows]
    append_rows(bulma_root(args.bulma_root), rows)
    code = max(item_code for _, _, _, item_code in results)
    if args.json:
        print(json.dumps([dict(doc, id=item_id) for item_id, doc, _, _ in results], indent=2, ensure_ascii=False))
    else:
        for item_id, doc, _, _ in results:
            print("%s %s" % (item_id, j_line(doc)))
    return code


def python_ok():
    return sys.version_info >= (3, 9)


def get_models(timeout=5):
    request = urllib.request.Request(
        API + "/models", method="GET",
        headers={"Authorization": "Bearer " + api_key(), "User-Agent": "bulma"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        raise BulmaError(3, "HTTP %s" % err.code)
    except (urllib.error.URLError, TimeoutError, OSError) as err:
        raise BulmaError(3, "network: %s" % err)
    return [m.get("name", "") for m in data.get("models", [])]


def cmd_doctor(args):
    py = "%d.%d.%d" % sys.version_info[:3]
    lines = []
    code = 0
    lines.append(("python3", ("ok (%s)" % py) if python_ok() else ("too old (%s), need 3.9" % py)))
    if not python_ok():
        code = 2
    has_key = bool(os.environ.get("TYPESAFE_API_KEY"))
    lines.append(("key", "ok" if has_key else "missing"))
    if not has_key:
        code = 2
    try:
        catalog = load_catalog()
        lines.append(("catalog", "ok (%d hooks)" % len(catalog)))
    except BulmaError as err:
        lines.append(("catalog", "invalid: %s" % err))
        code = code or 4
    try:
        cfg = load_config()
        lines.append(("config", ("ok (%s)" % config_path()) if cfg else "none (defaults)"))
    except BulmaError as err:
        cfg = {}
        lines.append(("config", "invalid: %s" % err))
        code = code or 4
    try:
        level, source = resolve_power(None, None, cfg)
        lines.append(("power", "%s (%s)" % (level, source)))
    except BulmaError as err:
        lines.append(("power", "invalid: %s" % err))
        code = code or 4
    if has_key and not args.offline:
        try:
            names = get_models()
            lines.append(("jev", "ok (%s)" % ", ".join(names) if names else "ok"))
        except BulmaError as err:
            lines.append(("jev", "unreachable: %s" % err))
            code = code or 3
    elif has_key:
        lines.append(("jev", "skipped (--offline)"))
    else:
        lines.append(("jev", "skipped (no key)"))
    if args.json:
        print(json.dumps({"exit": code, "checks": dict(lines)}, indent=2))
    else:
        for name, value in lines:
            print("%-8s %s" % (name, value))
        if code == 2:
            print()
            print(REQUIREMENT.format(py=("ok (%s)" % py) if python_ok() else ("too old (%s)" % py)))
        elif code == 3:
            print()
            print("Jev unreachable. Check the network and the key, then run /bulma again.")
    return code


def set_outcome(root, decision_id, question, value, note=""):
    if value not in ("confirmed", "reversed"):
        raise BulmaError(4, "outcome must be confirmed or reversed")
    path = ledger_path(root)
    rows = read_rows(path)
    hits = [r for r in rows if r["decision_id"] == decision_id and r["question"] == question]
    if not hits:
        raise BulmaError(4, "no row for %s %s in %s" % (decision_id, question, path))
    for row in hits:
        row["outcome"] = value
        if note:
            row["note"] = (row["note"] + " | " if row["note"] else "") + note
    write_rows(path, rows)


def cmd_outcome(args):
    set_outcome(bulma_root(args.bulma_root), args.decision_id, args.question, args.value, args.note)
    print("updated %s %s outcome=%s" % (args.decision_id, args.question, args.value))
    return 0


def cmd_tune(args):
    catalog = load_catalog()
    hook_id, _, qid = args.question.rpartition(".")
    if hook_id not in catalog or qid not in catalog[hook_id]["questions"]:
        raise BulmaError(4, "unknown question %r; use <hook>.<question>" % args.question)
    try:
        value = float(args.act_at)
    except ValueError:
        raise BulmaError(4, "act_at must be a number")
    if not FLOOR <= value <= CEIL:
        raise BulmaError(4, "act_at must be within [%s, %s]" % (FLOOR, CEIL))
    cfg = load_config()
    cfg.setdefault("act_at", {})[args.question] = round(value, 2)
    path = save_config(cfg)
    print("act_at[%s]=%.2f written to %s" % (args.question, value, path))
    return 0


def cmd_model(args):
    cfg = load_config()
    if args.action == "set":
        if not args.model_id:
            raise BulmaError(4, "model set needs a model id")
        cfg["model"] = args.model_id
        path = save_config(cfg)
        print("model=%s written to %s" % (args.model_id, path))
        return 0
    if cfg.get("model"):
        print("%s (config)" % cfg["model"])
    else:
        print("%s (default)" % DEFAULT_MODEL)
    return 0


def parse_ts(value):
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def row_evaluation(row, catalog):
    if (row.get("note", "").startswith(("invalid_answer", "truncated", "error:"))
            or not row.get("answer")):
        return None
    question = catalog.get(row["hook"], {}).get("questions", {}).get(row["question"], {})
    kind = row.get("question_type") or question.get("type")
    try:
        value = float(row["confidence"])
        if not probability(value):
            return None
        if kind == "noul":
            p = float(row["answer"])
            if not probability(p) or p == 0.5:
                return None
            return ("yes" if p > 0.5 else "no"), max(p, 1 - p)
        if not row["answer"]:
            return None
        return row["answer"], value
    except (ValueError, TypeError):
        return None


def graph_label(value, kind):
    if kind == "noul":
        return {"true": "yes", "false": "no", "yes": "yes", "no": "no"}.get(value.lower(), value)
    return value


def suggest_threshold(rows, current, catalog=None):
    catalog = load_catalog() if catalog is None else catalog
    labeled = [(r, row_evaluation(r, catalog)) for r in rows
               if r["outcome"] in ("confirmed", "reversed") and not r.get("note", "").startswith("cache_hit")]
    labeled = [(r, result) for r, result in labeled if result is not None]
    if len(labeled) < 20:
        return "need >=20 outcomes"
    for step in range(10, 20):
        threshold = step / 20.0
        selected = [r for r, (_, certainty) in labeled if certainty >= threshold]
        if len(selected) >= 20 and sum(r["outcome"] == "confirmed" for r in selected) / len(selected) >= 0.95:
            return "keep" if abs(threshold - current) < 0.001 else "%.2f" % threshold
    return "no supported threshold"


def percentile(values, fraction):
    return sorted(values)[max(0, math.ceil(len(values) * fraction) - 1)] if values else "-"


def cmd_report(args):
    root = bulma_root(args.bulma_root)
    paths = [ledger_path(root)] if args.repo_only else sorted(bulma_home().glob("*/.bulma-core/DECISIONS.tsv"))
    rows = []
    for path in paths:
        rows.extend(read_rows(path))
    if args.since:
        cutoff = datetime.now(timezone.utc) - timedelta(days=int(args.since))
        rows = [r for r in rows if (parse_ts(r["ts_iso"]) or cutoff) >= cutoff]
    for field in ("hook", "model", "policy_id", "source"):
        wanted = getattr(args, field, None)
        if wanted:
            rows = [r for r in rows if (r.get(field) or "legacy") == wanted]
    if not rows:
        print("no decisions found under %s" % (root if args.repo_only else bulma_home()))
        return 0
    catalog = load_catalog()
    groups = {}
    for row in rows:
        if not row["note"].startswith("cache_hit"):
            key = (row["model"], row.get("policy_id") or "legacy", row.get("source") or "legacy", row["power"])
            groups.setdefault(key, {}).setdefault((row["hook"], row["question"]), []).append(row)
    for (model, policy, source, power), questions in sorted(groups.items()):
        print("model=%s policy=%s source=%s power=%s" % (model, policy, source, power))
        print("| hook.question | n | acted% | certainty | agree% | confirmed | reversed | unlabeled | act_at | suggest effective | p95 ms |")
        print("|---|---|---|---|---|---|---|---|---|---|---|")
        for (hook, question), items in sorted(questions.items()):
            n = len(items)
            acted = sum(r["acted"] == "true" for r in items)
            evaluated = [(r, row_evaluation(r, catalog)) for r in items]
            certainty = [result[1] for _, result in evaluated if result is not None]
            kind = items[-1].get("question_type") or catalog.get(hook, {}).get("questions", {}).get(question, {}).get("type")
            with_graph = [(r, result) for r, result in evaluated if r["graph_answer"] and result is not None]
            agree = ("%d%%" % round(100 * sum(result[0] == graph_label(r["graph_answer"], kind)
                                               for r, result in with_graph) / len(with_graph))) if with_graph else "-"
            confirmed = sum(r["outcome"] == "confirmed" for r in items)
            reversed_count = sum(r["outcome"] == "reversed" for r in items)
            current = float(items[-1]["act_at"] or 0)
            latencies = [int(r["latency_ms"]) for r in items if r["latency_ms"].isdigit()]
            suggestion = "replay only" if source == "replay" else suggest_threshold(items, current, catalog)
            print("| %s.%s | %d | %d%% | %.2f | %s | %d | %d | %d | %.2f | %s | %s |" % (
                hook, question, n, round(100 * acted / n), sum(certainty) / len(certainty) if certainty else 0,
                agree, confirmed, reversed_count, n - confirmed - reversed_count, current, suggestion,
                percentile(latencies, .95)))
    calls = {}
    for row in rows:
        calls.setdefault(row["decision_id"], row)
    cache_hits = sum(r["note"].startswith("cache_hit") for r in calls.values())
    if cache_hits:
        print("decision cache: %d hits, %d fresh/replayed decisions" % (cache_hits, len(calls) - cache_hits))
    tokens = [int(r["input_tokens"]) for r in calls.values() if r["input_tokens"].isdigit()]
    latencies = [int(r["latency_ms"]) for r in calls.values() if r["latency_ms"].isdigit()]
    if tokens or latencies:
        print("calls: %d · input_tokens: %d (avg %d) · latency p50 %s ms, p95 %s ms, max %s ms" % (
            len(calls), sum(tokens), sum(tokens) // len(tokens) if tokens else 0,
            percentile(latencies, .5), percentile(latencies, .95), max(latencies) if latencies else "-"))
    print("note: agree% compares the graph heuristic, not correctness; unlabeled outcomes are unknown.")
    print("note: Noul certainty is max(p, 1-p); Choice/Score use API confidence. Cached rows do not calibrate.")
    if any(r.get("source") in ("", "replay") for r in rows):
        print("note: legacy rows have unknown provenance; replay usage is fixture data, not billing.")
    return 0


def cmd_timeout(args):
    cfg = load_config()
    if args.hook:
        find_hook(load_catalog(), args.hook)
    if args.seconds is not None:
        if not math.isfinite(args.seconds) or args.seconds <= 0:
            raise BulmaError(4, "decision timeout must be a finite positive number")
        if args.hook:
            cfg.setdefault("timeout_by_hook", {})[args.hook] = args.seconds
        else:
            cfg["timeout_seconds"] = args.seconds
        save_config(cfg)
    print("timeout=%g seconds" % decision_timeout(args.hook or "", cfg))


def add_builder_args(p):
    p.add_argument("--args", default="", help="raw /bulma args (entry.*)")
    p.add_argument("--world", help="world.json path; default .bulma-core/world.json")
    p.add_argument("--resume", action="store_true", help="entry.next_step: keep only resume:* candidates")
    p.add_argument("--pr", help="PR number or URL for gh pr view")
    p.add_argument("--pr-json", help="gh pr view --json output, instead of calling gh")
    p.add_argument("--check-name")
    p.add_argument("--log-file", help="failed check log; the last %d lines are sent" % LOG_TAIL_LINES)
    p.add_argument("--same-fail-on-base", default="unknown", choices=["yes", "no", "unknown"])


def build_parser():
    parser = argparse.ArgumentParser(prog="bulma.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("catalog", help="validate decisions.json")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_catalog)

    p = sub.add_parser("power", help="print or set the power level")
    p.add_argument("action", nargs="?", choices=["set"])
    p.add_argument("level", nargs="?")
    p.add_argument("--hook", help="print, or with set write, one hook's level (power_by_hook)")
    p.add_argument("--power")
    p.set_defaults(func=cmd_power)

    p = sub.add_parser("state", help="build a hook's state file from world.json / gh and print its path")
    p.add_argument("hook")
    add_builder_args(p)
    p.add_argument("--bulma-root")
    p.set_defaults(func=cmd_state)

    p = sub.add_parser("ask", help="ask Jev one hook's questions")
    p.add_argument("hook")
    p.add_argument("--state")
    p.add_argument("--build", action="store_true", help="build the state in code (see `state`) instead of --state")
    add_builder_args(p)
    p.add_argument("--line", action="store_true", help="print one J: chat line")
    p.add_argument("--power")
    p.add_argument("--model")
    p.add_argument("--criteria")
    p.add_argument("--graph-answer", action="append", default=[])
    p.add_argument("--context", action="append", default=[])
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--replay")
    p.add_argument("--bulma-root")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_ask)

    p = sub.add_parser("ask-many", help="ask many hooks/states in parallel from one batch file")
    p.add_argument("--batch", required=True, help='JSON: [{"id","hook","state","criteria","graph_answer","context","replay"}]')
    p.add_argument("--power")
    p.add_argument("--model")
    p.add_argument("--context", action="append", default=[])
    p.add_argument("--workers", type=int, default=8)
    p.add_argument("--bulma-root")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_ask_many)

    p = sub.add_parser("doctor", help="check python, key, catalog, config, and the Jev endpoint")
    p.add_argument("--json", action="store_true")
    p.add_argument("--offline", action="store_true", help="skip the network check")
    p.set_defaults(func=cmd_doctor)

    p = sub.add_parser("outcome", help="mark a logged decision confirmed or reversed")
    p.add_argument("decision_id")
    p.add_argument("question")
    p.add_argument("value")
    p.add_argument("--note", default="")
    p.add_argument("--bulma-root")
    p.set_defaults(func=cmd_outcome)

    p = sub.add_parser("timeout", help="show or set the shared request/retry budget")
    p.add_argument("seconds", type=float, nargs="?")
    p.add_argument("--hook")
    p.set_defaults(func=cmd_timeout)

    p = sub.add_parser("report", help="calibration table from DECISIONS.tsv")
    p.add_argument("--hook")
    p.add_argument("--model")
    p.add_argument("--policy-id")
    p.add_argument("--source", choices=("live", "replay", "legacy"))
    p.add_argument("--since", type=int)
    p.add_argument("--repo-only", action="store_true")
    p.add_argument("--bulma-root")
    p.set_defaults(func=cmd_report)

    p = sub.add_parser("tune", help="override act_at for one question")
    p.add_argument("question", help="<hook>.<question>")
    p.add_argument("act_at")
    p.set_defaults(func=cmd_tune)

    p = sub.add_parser("model", help="print or pin the model id")
    p.add_argument("action", nargs="?", choices=["set"])
    p.add_argument("model_id", nargs="?")
    p.set_defaults(func=cmd_model)

    dispatch.register(sub, sys.modules[__name__])
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "power" and args.action == "set" and not args.level:
        parser.error("power set needs a level")
    try:
        return args.func(args)
    except BulmaError as err:
        print("bulma: %s" % err, file=sys.stderr)
        return err.code


if __name__ == "__main__":
    sys.exit(main())
