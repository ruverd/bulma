#!/usr/bin/env python3
"""Does any build/test workflow run on pull requests into this base branch?

Reads the workflow files as they exist on the base branch and prints JSON:

  {"scope": "in_scope" | "out_of_scope" | "unknown", "base": ...,
   "on_base": [...], "build_test": [...], "unparsed": [...]}

out_of_scope means the repository's own CI configuration never builds or
tests pull requests into this base (for example `pull_request.branches:
[main]` and the PR targets a feature branch). That is an infrastructure
decision, not missing evidence. The default branch is never out of scope.
Anything the parser cannot read is unknown, never out of scope.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from gate import BUILD_TEST  # noqa: E402

PR_EVENTS = ("pull_request", "pull_request_target")
ON_KEY = re.compile(r"""^(?:on|"on"|'on'|true):(.*)$""")
TOP_KEY = re.compile(r"^[^\s#-][^:]*:")


class Unparsed(Exception):
    pass


def clean(line: str) -> str:
    return re.sub(r"\s+#.*$", "", line.rstrip())


def scalar(text: str) -> str:
    return text.strip().strip("'\"")


def flow_list(text: str) -> list[str]:
    text = text.strip()
    if not (text.startswith("[") and text.endswith("]")):
        raise Unparsed(f"expected a list, got {text!r}")
    return [scalar(item) for item in text[1:-1].split(",") if scalar(item)]


def indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def block(lines: list[str], start: int) -> list[int]:
    """Indexes of the lines nested under line `start`."""
    out, parent = [], indent(lines[start])
    for j in range(start + 1, len(lines)):
        if not lines[j].strip():
            continue
        if indent(lines[j]) <= parent:
            break
        out.append(j)
    return out


def children(lines: list[str], start: int) -> list[int]:
    """Indexes of the direct children of line `start`."""
    nested = block(lines, start)
    return [j for j in nested if indent(lines[j]) == indent(lines[nested[0]])] if nested else []


def values(lines: list[str], i: int, rest: str) -> list[str]:
    if rest.strip():
        return flow_list(rest)
    items = []
    for j in block(lines, i):
        stripped = lines[j].strip()
        if not stripped.startswith("- "):
            raise Unparsed(f"expected a list item, got {stripped!r}")
        items.append(scalar(stripped[2:]))
    return items


def glob(pattern: str) -> re.Pattern[str]:
    out, i = "", 0
    while i < len(pattern):
        if pattern.startswith("**", i):
            out, i = out + ".*", i + 2
        elif pattern[i] == "*":
            out, i = out + "[^/]*", i + 1
        elif pattern[i] == "?":
            out, i = out + "[^/]", i + 1
        else:
            out, i = out + re.escape(pattern[i]), i + 1
    return re.compile(out + r"\Z")


def matches(patterns: list[str], branch: str) -> bool:
    hit = False
    for pattern in patterns:
        negate = pattern.startswith("!")
        if glob(pattern.lstrip("!")).match(branch):
            hit = not negate
    return hit


def event_covers(lines: list[str], i: int, base: str) -> bool:
    """One `pull_request:` mapping entry: does it fire for PRs into base?"""
    filters = children(lines, i)
    if not filters:
        return True
    branches = ignore = None
    for j in filters:
        key, _, rest = lines[j].strip().partition(":")
        if key == "branches":
            branches = values(lines, j, rest)
        elif key == "branches-ignore":
            ignore = values(lines, j, rest)
    if branches is not None:
        return matches(branches, base)
    if ignore is not None:
        return not matches(ignore, base)
    return True


def runs_on_base(text: str, base: str) -> bool:
    lines = [clean(line) for line in text.splitlines()]
    for i, line in enumerate(lines):
        found = ON_KEY.match(line)
        if not found:
            continue
        rest = found.group(1).strip()
        if rest:
            if rest.startswith("{"):
                raise Unparsed("flow mapping under on:")
            names = flow_list(rest) if rest.startswith("[") else [scalar(rest)]
            return any(name in PR_EVENTS for name in names)
        body = children(lines, i)
        if not body:
            raise Unparsed("empty on:")
        covered = False
        for j in body:
            stripped = lines[j].strip()
            if stripped.startswith("- "):
                covered |= scalar(stripped[2:]) in PR_EVENTS
                continue
            key, _, value = stripped.partition(":")
            if scalar(key) not in PR_EVENTS:
                continue
            if value.strip() and value.strip() not in ("{}", "null", "~"):
                raise Unparsed(f"inline filters on {key}")
            covered |= event_covers(lines, j, base)
        return covered
    raise Unparsed("no on: key")


def is_build_test(path: Path, text: str) -> bool:
    names = [path.stem]
    names += re.findall(r"^name:\s*(.+)$", text, re.M)
    names += re.findall(r"^  ([\w-]+):\s*$", text.split("\njobs:", 1)[-1], re.M) if "\njobs:" in text else []
    names += re.findall(r"^    name:\s*(.+)$", text, re.M)
    return any(BUILD_TEST.search(scalar(name).replace("-", " ").replace("_", " ")) for name in names)


def scope(files: list[Path], base: str, default: str) -> dict:
    result = {"scope": "in_scope", "base": base, "on_base": [], "build_test": [], "unparsed": []}
    for path in sorted(files):
        text = path.read_text(encoding="utf-8")
        build_test = is_build_test(path, text)
        if build_test:
            result["build_test"].append(path.name)
        try:
            if runs_on_base(text, base):
                result["on_base"].append(path.name)
        except Unparsed as exc:
            result["unparsed"].append(f"{path.name}: {exc}")
    if base == default:
        return result
    tested = [name for name in result["on_base"] if name in result["build_test"]]
    unread = [entry for entry in result["unparsed"] if entry.split(":")[0] in result["build_test"]]
    if tested:
        result["scope"] = "in_scope"
    elif unread or not result["build_test"]:
        result["scope"] = "unknown"
    else:
        result["scope"] = "out_of_scope"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--workflows", required=True, help="directory with the base branch's .github/workflows files")
    parser.add_argument("--base", required=True, help="PR baseRefName")
    parser.add_argument("--default-branch", required=True, help="repository default branch")
    args = parser.parse_args()
    files = [p for p in Path(args.workflows).iterdir() if p.suffix in (".yml", ".yaml")]
    print(json.dumps(scope(files, args.base, args.default_branch)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
