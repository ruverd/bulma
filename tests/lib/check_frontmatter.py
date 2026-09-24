#!/usr/bin/env python3
"""Frontmatter contract for skills, agents and commands."""
import os
import sys

from frontmatter import flat_files, parse, skill_files

SKILL_KEYS = {
    "name",
    "description",
    "category",
    "argument-hint",
    "disable-model-invocation",
    "user-invocable",
}
AGENT_KEYS = {
    "name",
    "description",
    "tools",
    "model",
    "color",
    # Grok-only. Claude Code ignores unknown keys, and dropping them breaks Grok.
    "prompt_mode",
    "permission_mode",
    "agents_md",
}
COMMAND_KEYS = {"name", "description", "argument-hint"}
CATEGORIES = {"graph", "engine", "lib"}
MAX_DESCRIPTION = 1024
# Every host pastes name + description for every skill into the system prompt on
# every turn, so this block is the one cost the repo pays whether a skill runs or
# not. Codex caps it at 2% of the context window, or 8,000 characters when it
# cannot read the window; past the cap it shortens descriptions and can drop
# skills entirely. Hold the sum under the documented floor, and spend the
# characters on trigger phrases rather than on restating the body.
MAX_DISCOVERY_CHARS = 8000
# Progressive disclosure: SKILL.md says when to run and what the invariants are,
# then points at GRAPH.md, nodes/ and references/ for the detail.
MAX_SKILL_LINES = 250
MAX_CODEX_MIGRATED_COMMAND_BYTES = 4000

# Item 1: the LSTM acronym stays in bodies, never in a description a picker or
# a marketplace listing renders.
BANNED_IN_DESCRIPTION = ("shit", "fuck", "damn")


def report(errors, path, root, message):
    errors.append(f"{os.path.relpath(path, root)}: {message}")


def check_common(errors, path, root, fields, allowed, want_name=None):
    for key in fields:
        if key not in allowed:
            report(errors, path, root, f"frontmatter key not allowed: {key}")
    name = fields.get("name", "")
    if want_name is not None:
        if not name:
            report(errors, path, root, "missing name")
        elif name != want_name:
            report(errors, path, root, f"name {name!r} does not match {want_name!r}")
    description = fields.get("description", "")
    if not description:
        report(errors, path, root, "missing or empty description")
        return
    if len(description) > MAX_DESCRIPTION:
        report(errors, path, root, f"description is {len(description)} chars, max {MAX_DESCRIPTION}")
    lowered = description.lower()
    for word in BANNED_IN_DESCRIPTION:
        if word in lowered:
            report(errors, path, root, f"description contains {word!r}; keep it in the body only")


def check_discovery_budget(errors, entries):
    """The always-on cost of this repo: what a host reads before any skill runs."""
    total = sum(len(name) + len(description) + 4 for name, description in entries)
    if total > MAX_DISCOVERY_CHARS:
        widest = sorted(entries, key=lambda e: -(len(e[0]) + len(e[1])))[:5]
        listed = ", ".join(f"{n} ({len(n) + len(d) + 4})" for n, d in widest)
        errors.append(
            f"skills: discovery block is {total} chars, max {MAX_DISCOVERY_CHARS}; "
            f"shorten the widest descriptions: {listed}"
        )


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    errors = []
    discovery = []

    for path in skill_files(root):
        fields, _ = parse(path)
        if fields is None:
            report(errors, path, root, "no frontmatter")
            continue
        name = os.path.basename(os.path.dirname(path))
        discovery.append((name, fields.get("description", "")))
        check_common(errors, path, root, fields, SKILL_KEYS, want_name=name)
        with open(path, encoding="utf-8") as handle:
            lines = sum(1 for _ in handle)
        if lines > MAX_SKILL_LINES:
            report(errors, path, root,
                   f"SKILL.md is {lines} lines, max {MAX_SKILL_LINES}; "
                   "move detail into nodes/ or references/")
        category = fields.get("category", "")
        if not category:
            report(errors, path, root, "missing category (graph|engine|lib)")
        elif category not in CATEGORIES:
            report(errors, path, root, f"category {category!r} not in {sorted(CATEGORIES)}")

    check_discovery_budget(errors, discovery)

    for path in flat_files(root, "agents"):
        fields, _ = parse(path)
        if fields is None:
            report(errors, path, root, "no frontmatter")
            continue
        stem = os.path.basename(path)[: -len(".md")]
        check_common(errors, path, root, fields, AGENT_KEYS, want_name=stem)
        if not fields.get("tools"):
            report(errors, path, root, "missing tools; declare least privilege explicitly")

    for path in flat_files(root, "commands"):
        stem = os.path.basename(path)[: -len(".md")]
        # Underscore slash aliases doubled the command picker on every host and
        # were never documented. The role names bulma_* live in agents/ instead.
        if "_" in stem:
            report(errors, path, root, "underscore command alias; use the hyphen form")
        fields, _ = parse(path)
        if fields is None:
            report(errors, path, root, "no frontmatter")
            continue
        check_common(errors, path, root, fields, COMMAND_KEYS)
        with open(path, encoding="utf-8") as handle:
            command_text = handle.read()
        unsupported = []
        if "$ARGUMENTS" in command_text:
            unsupported.append("$ARGUMENTS")
        if any(f"${number}" in command_text for number in range(10)):
            unsupported.append("numbered argument placeholder")
        if "{{" in command_text and "}}" in command_text:
            unsupported.append("template expression")
        if "!`" in command_text or "! `" in command_text:
            unsupported.append("shell interpolation")
        if any(token.startswith("@") and len(token) > 1
               for token in command_text.split()):
            unsupported.append("file mention")
        if unsupported:
            report(errors, path, root,
                   "Codex command migration rejects: " + ", ".join(unsupported))
        # Codex adds a small skill wrapper around each command and caps the
        # rendered result at 4,000 bytes. Keep enough room for that wrapper.
        if len(command_text.encode("utf-8")) > MAX_CODEX_MIGRATED_COMMAND_BYTES - 500:
            report(errors, path, root,
                   f"command is too large for Codex migration: "
                   f"{len(command_text.encode('utf-8'))} bytes")

    for line in errors:
        print(line)
    if errors:
        print(f"{len(errors)} frontmatter problem(s)", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
