#!/usr/bin/env python3
"""Keep findings whose path:line sits in the unified diff (or an allow-path)."""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from typing import Any

HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")
GIT_B = re.compile(r"^diff --git a/.+ b/(.+)$")


def load_findings(raw: str) -> list[dict[str, Any]]:
    data = json.loads(raw)
    if isinstance(data, dict) and "findings" in data:
        data = data["findings"]
    if not isinstance(data, list):
        raise SystemExit("findings must be a JSON array or {\"findings\": [...]}")
    return data


def new_lines_by_path(patch: str) -> dict[str, set[int]]:
    current = ""
    covered: dict[str, set[int]] = defaultdict(set)
    new_line = 0
    in_hunk = False
    for raw in patch.splitlines():
        git = GIT_B.match(raw)
        if git:
            current = git.group(1).strip()
            in_hunk = False
            continue
        if raw.startswith("+++"):
            rest = raw[4:].strip()
            if rest == "/dev/null":
                current = ""
                in_hunk = False
                continue
            if rest.startswith("b/"):
                rest = rest[2:]
            current = rest.split("\t", 1)[0]
            in_hunk = False
            continue
        hunk = HUNK.match(raw)
        if hunk:
            new_line = int(hunk.group(3))
            in_hunk = True
            continue
        if not in_hunk or not current:
            continue
        if raw.startswith("\\"):
            continue
        if raw.startswith("-"):
            continue
        if raw.startswith("+") or raw.startswith(" "):
            covered[current].add(new_line)
            new_line += 1
            continue
        in_hunk = False
    return covered


def line_number(finding: dict[str, Any]) -> int | None:
    value = finding.get("line")
    if value is None or value == "":
        return None
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def bind(
    findings: list[dict[str, Any]],
    covered: dict[str, set[int]],
    allow: set[str],
) -> dict[str, list[dict[str, Any]]]:
    kept: list[dict[str, Any]] = []
    dropped: list[dict[str, Any]] = []
    for finding in findings:
        path = str(finding.get("path") or "")
        number = line_number(finding)
        record = dict(finding)
        if finding.get("in_diff") is False:
            record["drop_reason"] = "in_diff_false"
            dropped.append(record)
            continue
        if not path or number is None:
            record["drop_reason"] = "missing_line"
            dropped.append(record)
            continue
        if path in allow:
            kept.append(finding)
            continue
        if number in covered.get(path, ()):
            kept.append(finding)
            continue
        record["drop_reason"] = "not_in_patch"
        dropped.append(record)
    return {"kept": kept, "dropped": dropped}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--patch", required=True)
    parser.add_argument("--findings", required=True)
    parser.add_argument("--allow-path", action="append", default=[])
    args = parser.parse_args()
    patch = open(args.patch, encoding="utf-8").read()
    source = sys.stdin if args.findings == "-" else open(args.findings, encoding="utf-8")
    with source as handle:
        findings = load_findings(handle.read())
    json.dump(
        bind(findings, new_lines_by_path(patch), set(args.allow_path)),
        sys.stdout,
        indent=2,
    )
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
