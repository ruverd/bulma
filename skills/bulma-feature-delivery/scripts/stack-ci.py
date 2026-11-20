"""Verify the out-of-scope CI path for a stacked child on its live GitHub refs."""

import argparse
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile
from urllib.parse import quote

sys.dont_write_bytecode = True
from delivery_pr import gh
from stack import git

SKILLS = Path(__file__).resolve().parents[2]
CI_SCOPE = SKILLS / "bulma-code-review/scripts/ci-scope.py"
RUNTIME = SKILLS / "bulma-bus/scripts/runtime.py"
ACCEPTABLE = {"SUCCESS", "SKIPPED", "NEUTRAL"}


def at_base(checkout, base_sha, base, default):
    with tempfile.TemporaryDirectory() as folder:
        paths = git(checkout, "ls-tree", "-rz", "--name-only", base_sha, "--", ".github/workflows/").stdout
        for name in paths.split("\0"):
            file = PurePosixPath(name)
            if file.parent == PurePosixPath(".github/workflows") and file.suffix in (".yml", ".yaml"):
                content = git(checkout, "show", f"{base_sha}:{name}").stdout
                (Path(folder) / file.name).write_text(content, encoding="utf-8")
        return json.loads(subprocess.check_output(
            [sys.executable, str(CI_SCOPE), "--workflows", folder, "--base", base,
             "--default-branch", default], text=True,
        ))


def verify_required(repo, base, base_sha, pr):
    branch = quote(base, safe="")
    target = json.loads(gh("api", f"repos/{repo}/branches/{branch}"))
    if target["commit"]["sha"] != base_sha:
        raise ValueError("The base moved while reading branch protection.")
    protection = target["protection"]["required_status_checks"]
    contexts = set(protection["contexts"]) | {check["context"] for check in protection.get("checks", [])}
    pages = json.loads(gh("api", f"repos/{repo}/rules/branches/{branch}", "--paginate", "--slurp"))
    for page in pages:
        for rule in page:
            if rule["type"] == "required_status_checks":
                contexts.update(check["context"] for check in rule["parameters"]["required_status_checks"])
            elif rule["type"] in {"workflows", "required_workflows", "required_workflow_status_checks"}:
                raise ValueError("A required workflow applies to this base; use the ordinary CI gate.")
    if contexts:
        required = json.loads(gh("pr", "checks", pr, "--repo", repo, "--required", "--json", "name,bucket"))
        absent = contexts - {check["name"] for check in required if check["bucket"] == "pass"}
        if absent:
            raise ValueError(f"Required checks did not pass: {', '.join(sorted(absent))}.")


def verify_local(checkout, proof_path, head_sha, base_sha):
    if proof_path is None:
        raise ValueError("Scoped local test evidence is required.")
    proof = json.loads(proof_path.read_text())
    if (proof["head"], proof["base"]) != (head_sha, base_sha) or not proof["receipts"]:
        raise ValueError("Local test evidence is missing or belongs to another head/base pair.")
    if git(checkout, "rev-parse", "HEAD").stdout.strip() != head_sha or git(
        checkout, "status", "--porcelain"
    ).stdout:
        raise ValueError("Local checks must cover the clean, committed PR head.")
    for receipt in proof["receipts"]:
        identity = json.loads(Path(receipt).read_text())["identity"]
        env = identity["environment"]
        if identity["head"] != head_sha or not env:
            raise ValueError("Test receipt must identify the current head and test environment.")
        validated = subprocess.run(
            [sys.executable, str(RUNTIME), "check", "--repo", checkout, "--evidence", receipt,
             "--environment", env, "--", *identity["command"]],
            capture_output=True, text=True,
        )
        if validated.returncode:
            raise ValueError("The local test receipt is stale or did not pass.")


def inspect(checkout, repo, pr, head_sha, base, base_sha, default, proof):
    for sha in (head_sha, base_sha):
        if not re.fullmatch(r"[a-f0-9]{40}", sha):
            raise ValueError("Expected a full commit SHA for both head and base.")
    if base == default:
        return {"status": "in_scope"}
    live = json.loads(gh("pr", "view", pr, "--repo", repo, "--json",
                         "state,headRefOid,baseRefName,baseRefOid,statusCheckRollup"))
    if (live["state"], live["headRefOid"], live["baseRefName"], live["baseRefOid"]) != (
        "OPEN", head_sha, base, base_sha
    ):
        raise ValueError("The pull request is closed or its head/base changed.")
    scope = at_base(checkout, base_sha, base, default)
    if scope["scope"] != "out_of_scope":
        return {"status": scope["scope"], "scope": scope}
    if scope["unparsed"]:
        raise ValueError("Some workflows could not be read; CI scope is unverified.")
    for check in live["statusCheckRollup"]:
        result = check.get("conclusion") if check["__typename"] == "CheckRun" else check.get("state")
        if result not in ACCEPTABLE:
            raise ValueError("A reported check is failed, pending or unknown; use the ordinary CI gate.")
    verify_required(repo, base, base_sha, pr)
    verify_local(checkout, proof, head_sha, base_sha)
    return {"status": "out_of_scope", "scope": scope, "head": head_sha, "base": base_sha}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkout", default=".")
    for name in ("repo", "pr", "head-sha", "base", "base-sha", "default"):
        parser.add_argument(f"--{name}", required=True)
    parser.add_argument("--proof", type=Path)
    try:
        print(json.dumps(inspect(**vars(parser.parse_args()))))
    except (KeyError, OSError, TypeError, ValueError, subprocess.CalledProcessError) as exc:
        parser.exit(2, f"{exc}\n")


if __name__ == "__main__":
    main()
