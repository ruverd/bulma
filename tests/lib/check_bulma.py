#!/usr/bin/env python3
"""Bulma catalog stays true to the graphs it hooks.

Every static Choice in skills/bulma/decisions.json must list exactly the enum
the target graph declares, every hook must point at an existing node file, and
HOOKS.md must list the same hook ids as the catalog.
"""
import json
import os
import re
import sys

CATALOG = os.path.join("skills", "bulma", "decisions.json")
HOOKS_MD = os.path.join("skills", "bulma", "HOOKS.md")
PROTOCOL = os.path.join("skills", "ruver-bus", "PROTOCOL.md")
ROUTE_EXTRA = {"memory", "none"}

BACKTICK = re.compile(r"`([^`]+)`")
HOOK_ROW = re.compile(r"^\|\s*`([a-z_]+\.[a-z_]+)`")


def read(root, rel):
    with open(os.path.join(root, rel), encoding="utf-8") as handle:
        return handle.read()


def yaml_enum(text, field):
    match = re.search(r"^%s:\s*(.+)$" % re.escape(field), text, re.M)
    if not match:
        return None
    return {part.strip() for part in match.group(1).split("|") if part.strip()}


def table_row_backticks(text, field):
    for line in text.splitlines():
        if line.startswith("| `%s`" % field):
            tokens = BACKTICK.findall(line)
            return set(tokens[1:])
    return None


def failures_classes(text):
    out = set()
    for line in text.splitlines():
        if line.startswith("| `"):
            out.add(BACKTICK.findall(line)[0])
    return out or None


def slash_enum(text, field):
    for line in text.splitlines():
        if line.startswith("| `%s` |" % field):
            cell = line.split("|")[2].strip()
            head = cell.split(".", 1)[0]
            return {part.strip() for part in head.split("/") if part.strip()}
    return None


def script_literals(text, keys):
    missing = [key for key in keys if '"%s"' % key not in text]
    return None if missing else set(keys)


def expected_enum(root, source, question_id, field, keys):
    text = read(root, os.path.join("skills", source))
    base = os.path.basename(source)
    if base == "ROUTING.md":
        return yaml_enum(text, field or question_id)
    if source.endswith("ruver-triage/STATE.schema.md"):
        return table_row_backticks(text, "classification")
    if base == "FAILURES.md":
        return failures_classes(text)
    if base == "verify.md":
        return slash_enum(text, field or question_id)
    if base.endswith(".py"):
        return script_literals(text, keys)
    return None


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    errors = []
    try:
        data = json.loads(read(root, CATALOG))
    except (OSError, json.JSONDecodeError) as err:
        print("%s: %s" % (CATALOG, err))
        return 1
    hooks = data.get("hooks", [])
    ids = [hook.get("id", "") for hook in hooks]

    for hook in hooks:
        hid = hook.get("id", "<no id>")
        graph, node = hook.get("graph", ""), hook.get("node", "")
        node_file = os.path.join(root, "skills", graph, "nodes", node + ".md")
        if not os.path.isfile(node_file):
            errors.append("%s: node file missing: skills/%s/nodes/%s.md" % (hid, graph, node))
        for qid, question in hook.get("questions", {}).items():
            criteria = question.get("criteria")
            if question.get("type") != "choice" or criteria == "dynamic":
                continue
            keys = sorted(criteria)
            if hid == "entry.route":
                try:
                    allowed = set(BACKTICK.findall(
                        [l for l in read(root, PROTOCOL).splitlines() if l.startswith("Allowed names:")][0]
                    )) | ROUTE_EXTRA
                except (OSError, IndexError):
                    errors.append("%s.%s: PROTOCOL.md missing or has no \"Allowed names:\" line" % (hid, qid))
                    continue
                extra = set(keys) - allowed
                if extra:
                    errors.append("%s.%s: targets not allowed by PROTOCOL.md: %s" % (hid, qid, sorted(extra)))
                continue
            source = question.get("enum_source")
            if not source:
                errors.append("%s.%s: static choice without enum_source" % (hid, qid))
                continue
            try:
                expected = expected_enum(root, source, qid, question.get("field"), keys)
            except OSError as err:
                errors.append("%s.%s: enum_source unreadable: %s" % (hid, qid, err))
                continue
            if expected is None:
                errors.append("%s.%s: could not parse enum from %s" % (hid, qid, source))
            elif expected != set(keys):
                errors.append("%s.%s: criteria %s != %s enum %s" % (hid, qid, keys, source, sorted(expected)))

    try:
        rows = [HOOK_ROW.match(l).group(1) for l in read(root, HOOKS_MD).splitlines() if HOOK_ROW.match(l)]
    except OSError:
        rows = []
        errors.append("%s: missing" % HOOKS_MD)
    if rows and sorted(rows) != sorted(ids):
        errors.append("HOOKS.md ids %s != catalog ids %s" % (sorted(rows), sorted(ids)))

    for line in errors:
        print(line)
    if errors:
        print("%d bulma catalog problem(s)" % len(errors), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
