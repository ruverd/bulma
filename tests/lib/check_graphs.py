#!/usr/bin/env python3
"""Graph contracts for process nodes.

A Need() is one node that must exist as a file and be named on a
GRAPH.md path (ascii spine and/or edges table). Append here when a
later ticket adds a node. Do not start a second checker.
"""
import os
import re
import sys
from collections import defaultdict, namedtuple

Need = namedtuple("Need", "skill node after before extra_files")

NEEDS = [
    Need(
        skill="ruver-feature-delivery",
        node="evidence",
        after="tester",
        before="quality",
        extra_files=("templates/PR_BODY.md",),
    ),
    Need(
        skill="ruver-developer",
        node="bot_review",
        after="mergeable",
        before="request_qa",
        extra_files=(),
    ),
    Need(
        skill="ruver-code-review",
        node="critic",
        after="review",
        before="publish",
        extra_files=("scripts/bind-findings.py", "scripts/classify-risk.py"),
    ),
]

BOLD = re.compile(r"\*\*([A-Za-z][A-Za-z0-9_]*)\*\*")
IDENT = re.compile(r"[A-Za-z][A-Za-z0-9_]*")


def skill_dir(root, skill):
    return os.path.join(root, "skills", skill)


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def first_fence(text):
    start = text.find("```")
    if start < 0:
        return ""
    start = text.find("\n", start)
    if start < 0:
        return ""
    end = text.find("```", start + 1)
    if end < 0:
        return ""
    return text[start + 1 : end]


def word_index(text, word):
    match = re.search(r"\b" + re.escape(word) + r"\b", text)
    return match.start() if match else -1


def spine_names_between(spine, node, after, before):
    i_after = word_index(spine, after)
    i_node = word_index(spine, node)
    i_before = word_index(spine, before)
    return 0 <= i_after < i_node < i_before


def cell_node(cell):
    bold = BOLD.search(cell)
    if bold:
        return bold.group(1).lower()
    ident = IDENT.search(cell.strip())
    return ident.group(0).lower() if ident else None


def parse_edges(text):
    heading = re.search(r"^##\s+Edges\s*$", text, re.M)
    if not heading:
        return {}
    adj = defaultdict(set)
    in_table = False
    for line in text[heading.end() :].splitlines():
        if not line.startswith("|"):
            if in_table:
                break
            continue
        cells = [part.strip() for part in line.strip().strip("|").split("|")]
        if len(cells) < 3:
            continue
        if cells[0].lower() == "from" or set(cells[0]) <= {"-", ":"}:
            in_table = True
            continue
        src, dst = cell_node(cells[0]), cell_node(cells[2])
        if src and dst:
            adj[src].add(dst)
            in_table = True
    return adj


def reachable(adj, start, end, avoid=()):
    if start == end:
        return True
    blocked = set(avoid)
    seen = {start}
    stack = [start]
    while stack:
        cur = stack.pop()
        for nxt in adj.get(cur, ()):
            if nxt in blocked or nxt in seen:
                continue
            if nxt == end:
                return True
            seen.add(nxt)
            stack.append(nxt)
    return False


def on_path(text, node, after, before):
    if spine_names_between(first_fence(text), node, after, before):
        return True
    adj = parse_edges(text)
    return bool(adj) and reachable(adj, after, node) and reachable(
        adj, node, before, avoid=(after,)
    )


def check_need(root, need):
    errors = []
    directory = skill_dir(root, need.skill)
    graph = os.path.join(directory, "GRAPH.md")
    node_file = os.path.join(directory, "nodes", need.node + ".md")
    if not os.path.isfile(node_file):
        errors.append(f"{need.skill}: missing nodes/{need.node}.md")
    for rel in need.extra_files:
        if not os.path.isfile(os.path.join(directory, rel)):
            errors.append(f"{need.skill}: missing {rel}")
    if not os.path.isfile(graph):
        errors.append(f"{need.skill}: missing GRAPH.md")
        return errors
    if not on_path(read(graph), need.node, need.after, need.before):
        errors.append(
            f"{need.skill}: GRAPH.md does not name {need.node} on the "
            f"path from {need.after} to {need.before}"
        )
    return errors


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    errors = []
    for need in NEEDS:
        errors.extend(check_need(root, need))
    for line in errors:
        print(line)
    if errors:
        print(f"{len(errors)} graph problem(s)", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
