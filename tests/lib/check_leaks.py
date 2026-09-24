#!/usr/bin/env python3
"""Host and vendor specifics belong in bulma-host, adapters and agent contracts.
A skill that names a harness tool, a model id or a person is no longer portable."""
import os
import re
import sys

PRUNE = {".git", ".worktrees", "node_modules"}

RULES = [
    # (label, pattern, predicate deciding whether the file may contain it)
    (
        "vendor-specific state field; use tracker_* and select the adapter with tracker:",
        re.compile(r"\blinear_[a-z_*]+|^\s*linear:\s"),
        # A changelog has to be able to name the field it renamed.
        lambda rel: rel.endswith("LINEAR.md") or "/adapters/" in rel
        or rel == "CHANGELOG.md",
    ),
    (
        "a real person's handle; use a placeholder such as octocat",
        re.compile(r"izaiasneto4"),
        lambda rel: False,
    ),
    (
        "vendor named as *the* tracker; say tracker and let PRODUCT.md detect",
        re.compile(r"\bLinear\b"),
        # Files whose job is exactly to map a capability onto a vendor, plus the
        # changelog, which has to be able to say what it renamed.
        lambda rel: (
            os.path.basename(rel) in ("LINEAR.md", "MCP_CONTEXT.md", "PRODUCT.md")
            or rel.startswith("skills/why/")
            or rel == "skills/bulma-host/SKILL.md"
            or "/adapters/" in rel
            or not rel.startswith(("skills/", "agents/", "commands/"))
        ),
    ),
    (
        "HOST.md is not a file any more; name the skill bulma-host",
        re.compile(r"HOST\.md"),
        # The changelog has to be able to name the file it moved.
        lambda rel: rel == "CHANGELOG.md",
    ),
    (
        "harness MCP tool name",
        re.compile(r"mcp__[a-z0-9_-]+"),
        lambda rel: rel == "skills/bulma-host/SKILL.md"
        or "/adapters/" in rel
        or rel.startswith("agents/")
        or rel.startswith("docs/"),
    ),
]


def files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in PRUNE]
        for name in sorted(filenames):
            if name.endswith(".md"):
                path = os.path.join(dirpath, name)
                yield path, os.path.relpath(path, root)


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    errors = []
    for path, rel in files(root):
        with open(path, encoding="utf-8") as handle:
            for lineno, line in enumerate(handle, 1):
                for label, pattern, allowed in RULES:
                    if allowed(rel):
                        continue
                    found = pattern.search(line)
                    if found:
                        errors.append(f"{rel}:{lineno}: {label} -> {found.group(0)!r}")
    for line in errors:
        print(line)
    if errors:
        print(f"{len(errors)} leak(s)", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
