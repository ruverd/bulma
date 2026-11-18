#!/usr/bin/env python3
"""Run a bounded Bulma QA reproduction selected from a host-owned catalog."""

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from tempfile import TemporaryDirectory
from urllib.parse import urlsplit
from uuid import uuid4

SKILLS = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True
sys.path.insert(0, str(SKILLS / "bulma/scripts"))
from answer_privacy import SENSITIVE_LOCATOR, redact


TARGET_ID = re.compile(r"[a-z][a-z0-9-]{0,79}")
REQUEST_ID = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9._-]{0,95}")
TEMPLATE = SKILLS / "bulma-bus/templates/JOBS.md"


class Busy(RuntimeError):
    pass


class Blocked(RuntimeError):
    pass


def read_catalog(path):
    if not path.is_file():
        return {}
    if path.is_symlink() or path.stat().st_uid != os.getuid() or path.stat().st_mode & 0o022:
        raise Blocked("The approved QA target registry has unsafe ownership or permissions.")
    return json.loads(path.read_text())["targets"]


def catalog_description(targets):
    description = []
    for key, item in targets.items():
        if not TARGET_ID.fullmatch(key):
            continue
        target = {"id": key, "environment": item["environment"], "pr": item.get("pr", "")}
        if "surfaces" in item:
            target["surfaces"] = [
                {"id": name, "label": surface["label"],
                 "controls": [{"id": action, "label": control["label"]}
                              for action, control in surface.get("controls", {}).items()]}
                for name, surface in item["surfaces"].items()
            ]
        else:
            target["steps"] = item["steps"]
        description.append(target)
    return description


def resolve_repro(config, plan):
    if "surfaces" not in config and plan is None:
        return config
    if (not isinstance(plan, dict) or set(plan) != {"surface", "actions", "bug_text", "success_text"}
            or not isinstance(plan["surface"], str)):
        raise Blocked("The reproduction needs one approved surface and two visible assertions.")
    surface = config.get("surfaces", {}).get(plan["surface"])
    if not surface or not TARGET_ID.fullmatch(plan["surface"]):
        raise Blocked("The reproduction surface is not approved for this environment.")
    controls = surface.get("controls", {})
    actions = plan["actions"]
    if (not isinstance(actions, list) or len(actions) > 8
            or any(not isinstance(action, str) or not TARGET_ID.fullmatch(action) or action not in controls
                   for action in actions)):
        raise Blocked("The reproduction uses a control outside its approved surface.")
    markers = [plan["bug_text"], plan["success_text"]]
    if any(not isinstance(marker, str) or not 3 <= len(marker) <= 160 or "\n" in marker
           or redact(marker) != marker or SENSITIVE_LOCATOR.search(marker) or "[redacted]" in marker
           for marker in markers):
        raise Blocked("The reproduction assertions are incomplete or contain sensitive material.")
    symptom, success = (marker.casefold() for marker in markers)
    if symptom in success or success in symptom:
        raise Blocked("The reproduction assertions do not distinguish the expected outcomes.")
    path = surface["path"]
    if not path.startswith("/") or (path != "/" and any(
        not re.fullmatch(r"[A-Za-z0-9_~-][A-Za-z0-9._~-]*", part)
        for part in path.strip("/").split("/")
    )) or "//" in path:
        raise Blocked("The approved surface must have a fixed path within the test origin.")
    origin(config["url"])
    return {
        **config,
        "url": urlsplit(config["url"])._replace(path=path).geturl(),
        "exact_route": True,
        "steps": [f"Open {surface['label']}", *(controls[action]["label"] for action in actions)],
        "clicks": [controls[action]["selector"] for action in actions],
        "evidence_selector": surface["evidence_selector"],
        "bug_text": markers[0], "success_text": markers[1],
    }


def set_fields(content, fields):
    for name, value in fields.items():
        content, count = re.subn(rf"(?m)^{name}:[^\n]*$", lambda _: f'{name}: "{value}"', content, count=1)
        if count != 1:
            raise Blocked("The existing Bulma QA slot has an unsupported format.")
    return content


def field(content, name):
    match = re.search(rf"(?m)^{name}:\s*([^\n]*)$", content)
    return match[1].strip().strip("\"'") if match else ""


def atomic(path, text):
    temp = path.with_name(f".{path.name}.{uuid4().hex}")
    try:
        fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w") as stream:
            stream.write(text)
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)


def active_claim(content, bus, active):
    if not active:
        return False
    if not re.fullmatch(r"[a-zA-Z0-9.-]+", active):
        return True
    if not (bus / "jobs" / active).is_dir():
        return False
    row = re.search(rf"(?m)^\|\s*{re.escape(active)}\s*\|[^|]*\|[^|]*\|\s*([^|]+)\|", content)
    if row and row[1].strip() in {"done", "done_notes", "escalated", "handed_off", "blocked"}:
        return False
    try:
        stamp = datetime.fromisoformat(field(content, "qa_claimed_at").replace("Z", "+00:00"))
        age = (datetime.now(timezone.utc) - stamp).total_seconds()
        return age <= 60 * int(field(content, "qa_lease_minutes") or "90")
    except (ValueError, TypeError):
        return True


@contextmanager
def qa_slot(repo, job):
    home = Path(os.environ.get("BULMA_HOME", Path.home() / ".bulma"))
    bus = home / str(repo).lstrip("/").replace("/", "-") / ".bulma-bus"
    bus.mkdir(mode=0o700, parents=True, exist_ok=True)
    jobs = bus / "JOBS.md"
    with (bus / "thread-qa.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise Busy("Bulma QA slot is in use.") from None
        if not jobs.exists():
            atomic(jobs, TEMPLATE.read_text())
        starting = jobs.read_text()
        active = field(starting, "qa_active")
        if (active != job and active_claim(starting, bus, active)) or field(starting, "qa_waiting"):
            raise Busy("Bulma QA already has active or queued work.")
        request_dir = bus / "jobs" / job
        request_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        atomic(jobs, set_fields(starting, {
            "qa_active": job, "qa_claimed_at": datetime.now(timezone.utc).isoformat(),
        }))
        try:
            yield
        finally:
            final = jobs.read_text()
            if field(final, "qa_active") == job:
                atomic(jobs, set_fields(final, {"qa_active": "", "qa_claimed_at": ""}))


def origin(url):
    parsed = urlsplit(url)
    if (not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment
            or parsed.scheme not in ("http", "https")):
        raise Blocked("The configured QA origin is invalid.")
    return parsed.scheme, parsed.hostname, parsed.port or (443 if parsed.scheme == "https" else 80)


def qa_repro(config, out, run):
    kind = config["kind"]
    target = config["url"]
    boundary = origin(target)
    if (kind not in ("local", "dev", "preview")
            or (kind == "local" and boundary[1] not in ("localhost", "127.0.0.1", "::1"))
            or (kind != "local" and boundary[0] != "https")):
        raise Blocked("The QA target is outside the authorized test environments.")
    if config.get("isolated_data") is not True:
        raise Blocked("The target has no verified isolated test data or auth boundary.")
    if config.get("synthetic_evidence") is not True or not config.get("evidence_selector"):
        raise Blocked("This target has no approved synthetic evidence area.")
    actions = config.get("clicks", [])
    if not isinstance(actions, list) or len(actions) > 8 or any(not isinstance(s, str) or not s for s in actions):
        raise Blocked("The target has no bounded QA plan.")
    if not config["steps"] or not config["bug_text"] or not config["success_text"]:
        raise Blocked("The reproduction steps or outcome assertions are missing.")

    session = "bulma-thread-qa-" + uuid4().hex
    base = ["agent-browser", "--session", session, "--allowed-domains", boundary[1]]
    state = config.get("auth_state")
    if state and not Path(state).is_file():
        raise Blocked("The approved QA session is missing or expired.")

    def verify_location():
        observed = urlsplit(run(*base, "get", "url").strip())
        clean_url = observed._replace(query="", fragment="").geturl()
        if (origin(clean_url) != boundary
                or (config.get("exact_route") and (observed.path != urlsplit(target).path
                                                   or observed.query or observed.fragment))):
            raise Blocked("The browser left the approved QA surface.")

    try:
        run("agent-browser", "doctor", "--offline", "--quick")
        run(*(base + (["--state", state] if state else [])), "open", target)
        for selector in ["", *actions]:
            if selector:
                run(*base, "click", selector)
            verify_location()
        run(*base, "wait", config["evidence_selector"])
        if config.get("exact_route"):
            verify_location()
        shown = run(*base, "get", "text", config["evidence_selector"])
        succeeded = config["success_text"] in shown
        failed = config["bug_text"] in shown
        if failed == succeeded:
            raise Blocked("The expected UI outcomes were inconclusive, or the test session did not reach the target.")
        marker = config["bug_text"] if failed else config["success_text"]
        if redact(shown) != shown or SENSITIVE_LOCATOR.search(shown):
            raise Blocked("The observed UI contains data that could not be cleared for sharing.")
        with TemporaryDirectory(prefix="bulma-qa-capture-") as private:
            capture = Path(private) / "proof.png"
            run(*base, "screenshot", config["evidence_selector"], str(capture))
            if config.get("exact_route"):
                verify_location()
            ocr = run("tesseract", str(capture), "stdout")
            if (marker.casefold() not in " ".join(ocr.split()).casefold()
                    or redact(ocr) != ocr or SENSITIVE_LOCATOR.search(ocr)
                    or not capture.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
                    or capture.stat().st_size > 8_000_000):
                raise Blocked("The screenshot could not be cleared as evidence.")
            shutil.copyfile(capture, out / "proof.png")
        return {"status": "reproduced" if failed else "not_reproduced",
                "environment": config["environment"], "steps": config["steps"],
                "observation": marker, "evidence": "reviewed_synthetic_png",
                "evidence_sha256": hashlib.sha256((out / "proof.png").read_bytes()).hexdigest()}
    finally:
        try:
            run(*base, "close")
        except Blocked:
            pass


def run_job(args, targets, plan=None):
    if not REQUEST_ID.fullmatch(args.event) or args.target not in targets:
        raise Blocked("The request has no approved QA target.")
    config = resolve_repro(targets[args.target], plan)
    plan_hash = hashlib.sha256(json.dumps(plan, sort_keys=True).encode()).hexdigest() if plan is not None else None
    if config.get("pr", "") != args.pr:
        raise Blocked("There is no approved preview for this PR.")
    checkout = Path(config["checkout"]).resolve(strict=True)
    repo = Path(subprocess.check_output(
        ["git", "-C", str(checkout), "rev-parse", "--show-toplevel"], text=True,
        stderr=subprocess.DEVNULL, timeout=5,
    ).strip()).resolve()
    if checkout != repo:
        raise Blocked("The approved QA checkout root could not be verified.")
    with qa_slot(repo, f"qa-thread-{args.event}"):
        result_path = args.out / "result.json"
        if result_path.exists():
            saved = json.loads(result_path.read_text())
            if saved["target"] != args.target or saved["pr"] != args.pr or saved.get("plan_hash") != plan_hash:
                raise Blocked("This request already has a different QA target or plan.")
            return saved["result"]
        def verify_head():
            if not args.pr:
                return
            if not re.fullmatch(r"https://github\.com/[\w.-]+/[\w.-]+/pull/[1-9]\d*", args.pr):
                raise Blocked("The requested PR cannot be verified.")
            head = subprocess.check_output(
                ["gh", "pr", "view", args.pr, "--json", "headRefOid", "--jq", ".headRefOid"],
                text=True, stderr=subprocess.DEVNULL, timeout=20,
            ).strip()
            if head != config.get("head"):
                raise Blocked("The approved preview is not pinned to the current PR commit.")
        verify_head()
        shim = SKILLS / "before-and-after/scripts/ensure-session.sh"
        with TemporaryDirectory(prefix="bulma-qa-run-") as folder:
            env = {key: os.environ[key] for key in ("HOME", "PATH", "TMPDIR", "BULMA_HOME") if key in os.environ}
            config_file = Path(folder) / "agent-browser.json"
            config_file.write_text('{"headed":false}\n')
            env["AGENT_BROWSER_CONFIG"] = str(config_file)
            deadline = time.monotonic() + 270

            def run(*argv):
                try:
                    remaining = 10 if argv[-1] == "close" else min(25, deadline - time.monotonic())
                    if remaining <= 0:
                        raise Blocked("The configured QA case exceeded its execution budget.")
                    return subprocess.check_output(argv, cwd=folder, env=env, text=True,
                                                   stderr=subprocess.DEVNULL, timeout=remaining)
                except (OSError, subprocess.SubprocessError):
                    raise Blocked("The QA browser or evidence checkout could not complete a configured step.") from None

            subprocess.run(["bash", str(shim)], cwd=repo, env=env, check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=20)
            args.out.mkdir(mode=0o700, parents=True, exist_ok=True)
            atomic(args.out / "plan.json", json.dumps({"environment": config["environment"], "steps": config["steps"]}))
            try:
                result = qa_repro(config, args.out, run)
                verify_head()
            except Blocked as exc:
                result = {"status": "blocked", "reason": str(exc)}
                (args.out / "proof.png").unlink(missing_ok=True)
            atomic(result_path, json.dumps({"target": args.target, "pr": args.pr,
                                           "plan_hash": plan_hash, "result": result}))
            return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--catalog", action="store_true")
    parser.add_argument("--event")
    parser.add_argument("--target")
    parser.add_argument("--pr", default="")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--plan-stdin", action="store_true")
    args = parser.parse_args()
    try:
        targets = read_catalog(args.registry)
        plan = None
        if args.plan_stdin:
            payload = sys.stdin.read(8193)
            if len(payload) > 8192:
                raise Blocked("The reproduction plan exceeds its input limit.")
            plan = json.loads(payload)
        result = catalog_description(targets) if args.catalog else run_job(args, targets, plan)
    except Busy:
        return 75
    except Blocked as exc:
        result = {"status": "blocked", "reason": str(exc)}
    except (OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError):
        result = {"status": "blocked", "reason": "The authorized QA target or its local tooling could not be resolved."}
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
