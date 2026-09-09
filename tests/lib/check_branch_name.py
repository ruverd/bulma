#!/usr/bin/env python3
"""Task git branch is always feature/<id-lowercase>.

JOBS.md owns the rule. Checkout copy elsewhere must not prefer a
tracker gitBranchName or a host {login}/<id> branch.
"""
import os
import re
import sys

PRUNE = {".git", ".worktrees", "node_modules"}

# Old recipes that produced ruverd/dev-4525 instead of feature/dev-4525.
FORBIDDEN = [
    (
        "do not prefer tracker gitBranchName over feature/<id-lowercase>",
        re.compile(
            r"gitBranchName.{0,8} if it exists"
            r"|gitBranchName` if any"
            r"|`gitBranchName` or `feature"
        ),
    ),
    (
        "do not keep a host-invented branch name",
        re.compile(r"keep that branch"),
    ),
    (
        "do not fall back to the tracker's branch name",
        re.compile(
            r"or the tracker's branch name"
            r"|tracker's branch name if it exists"
            r"|tracker name or `feature"
            r"|its branch name or `feature"
            r"|tracker_branch or feature"
        ),
    ),
]

REQUIRED_JOBS = [
    "feature/<id-lowercase>",
    "always `feature/<id-lowercase>`",
    "{login}/",
]


def files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in PRUNE]
        for name in sorted(filenames):
            if not name.endswith(".md"):
                continue
            path = os.path.join(dirpath, name)
            rel = os.path.relpath(path, root)
            if rel == "CHANGELOG.md":
                continue
            if not rel.startswith(("skills/", "agents/", "commands/")):
                continue
            yield path, rel


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    errors = []
    jobs = os.path.join(root, "skills/ruver-bus/JOBS.md")
    with open(jobs, encoding="utf-8") as handle:
        jobs_text = handle.read()
    for needle in REQUIRED_JOBS:
        if needle not in jobs_text:
            errors.append(f"skills/ruver-bus/JOBS.md: missing {needle!r}")
    for path, rel in files(root):
        with open(path, encoding="utf-8") as handle:
            for lineno, line in enumerate(handle, 1):
                for label, pattern in FORBIDDEN:
                    if pattern.search(line):
                        errors.append(f"{rel}:{lineno}: {label} -> {line.strip()!r}")
    for line in errors:
        print(line)
    if errors:
        print(f"{len(errors)} branch-name error(s)", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
