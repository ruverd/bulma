#!/usr/bin/env python3
"""Files and directories a published repo is expected to carry."""
import os
import sys

REQUIRED = [
    "CONTRIBUTING.md",
    "CHANGELOG.md",
    "SECURITY.md",
    ".github/PULL_REQUEST_TEMPLATE.md",
    ".github/ISSUE_TEMPLATE/bug_report.md",
    ".github/ISSUE_TEMPLATE/feature_request.md",
]
# Internal working notes do not belong on every user's disk.
FORBIDDEN = ["docs/superpowers"]
# Reference material sits exactly one directory below SKILL.md, so a partial read
# of the skill shows an agent everything it can load. A second level hides
# material nothing points at.
MAX_REFERENCE_DEPTH = 1


def reference_depth(root, errors):
    from frontmatter import skill_files

    for path in skill_files(root):
        directory = os.path.dirname(path)
        name = os.path.basename(directory)
        for dirpath, _, filenames in os.walk(directory):
            rel = os.path.relpath(dirpath, directory)
            depth = 0 if rel == "." else rel.count(os.sep) + 1
            if depth <= MAX_REFERENCE_DEPTH:
                continue
            for filename in sorted(filenames):
                if filename.endswith(".md"):
                    errors.append(
                        f"{name}: {os.path.join(rel, filename)} is {depth} levels "
                        f"below SKILL.md, max {MAX_REFERENCE_DEPTH}"
                    )


def graph_file_sets(root, errors):
    """docs/GRAPH_ENGINEER.md lists what a graph ships. Hold it to that."""
    sys.path.insert(0, os.path.join(root, "tests", "lib"))
    from frontmatter import parse, skill_files

    for path in skill_files(root):
        fields, _ = parse(path)
        if not fields or fields.get("category") != "graph":
            continue
        directory = os.path.dirname(path)
        name = os.path.basename(directory)
        for needed in ("GRAPH.md", "STATE.schema.md"):
            if not os.path.exists(os.path.join(directory, needed)):
                errors.append(
                    f"{name}: category is graph but {needed} is missing "
                    "(add it, or give the skill a category that fits)"
                )
        nodes = os.path.join(directory, "nodes")
        if not os.path.isdir(nodes) or not os.listdir(nodes):
            errors.append(f"{name}: category is graph but nodes/ is empty")


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    errors = []
    graph_file_sets(root, errors)
    reference_depth(root, errors)
    for rel in REQUIRED:
        if not os.path.exists(os.path.join(root, rel)):
            errors.append(f"missing: {rel}")
    for rel in FORBIDDEN:
        if os.path.exists(os.path.join(root, rel)):
            errors.append(f"should not be published: {rel}")
    # Claude Code is the biggest audience and .claude-plugin/marketplace.json
    # exists, so the README has to say how to use it.
    readme = os.path.join(root, "README.md")
    if os.path.exists(readme):
        text = open(readme, encoding="utf-8").read()
        for needed in ("claude plugin marketplace add", "claude plugin install"):
            if needed not in text:
                errors.append(f"README.md does not document: {needed}")
    for line in errors:
        print(line)
    if errors:
        print(f"{len(errors)} structure problem(s)", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
