#!/usr/bin/env python3
"""Turn one agent-browser snapshot into a qa.browse question, then turn the
answer back into one agent-browser command.

`state` reads `agent-browser snapshot -i` (text or `--json`) and writes the
state file plus the dynamic target criteria: one indexed element table, and
one head per operation that can take a target, each holding only the refs
that operation can execute on.

`resolve` reads `bulma.py ask qa.browse --json` and prints the single command
to run. The operation picks which target head counts; the other heads were
speculative. A ref that was not in the observed snapshot never resolves, and
model output never becomes a selector, a coordinate, or JavaScript.

Stdlib only. Exit codes: 0 ok, 4 bad input, 5 no actionable decision (walk
the step by hand).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

OPERATIONS = (
    "CLICK",
    "TYPE_TEXT",
    "SELECT",
    "SCROLL_UP",
    "SCROLL_DOWN",
    "WAIT",
    "DONE",
    "BLOCKED",
)
# Operation -> the question head that carries its target. Operations missing
# from this map need no element.
TARGET_HEADS = {
    "CLICK": "click_target",
    "TYPE_TEXT": "type_text_target",
    "SELECT": "select_target",
}
# Accessibility roles each operation can execute on. A head only ever offers
# refs from these sets, so an impossible action cannot be proposed.
CLICKABLE = frozenset({
    "button", "link", "checkbox", "radio", "switch", "tab", "menuitem",
    "menuitemcheckbox", "menuitemradio", "combobox", "textbox", "searchbox",
    "option", "treeitem", "gridcell", "listitem", "slider", "spinbutton",
})
TYPEABLE = frozenset({"textbox", "searchbox", "spinbutton", "combobox"})
# Native dropdown choices carry their own ref; the command targets the
# owning combobox and names the option.
SELECTABLE = frozenset({"option"})
OWNS_OPTIONS = frozenset({"combobox", "listbox", "menu"})

NONE = "none"
EMPTY = "empty"
MAX_ELEMENTS = 60
MAX_LABEL = 120
MAX_HISTORY = 10
# After typing into a combobox, jev-ultrafast waits for suggestions and caps
# that wait. One WAIT is a short settle, never a sleep.
WAIT_MS = 200

# `- textbox "Email" [ref=e3]`, `- combobox [expanded=false, ref=e5]: Free`
LINE = re.compile(
    r'^(?P<indent> *)- (?P<role>[A-Za-z][\w-]*)'
    r'(?: "(?P<name>.*?)")?'
    r'(?: \[(?P<attrs>[^\]]*)\])?'
    r'(?:: (?P<value>.*))?$'
)


class BrowseError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def read_source(path):
    if not path or path == "-":
        return sys.stdin.read()
    try:
        return Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        raise BrowseError(4, "snapshot file missing: %s" % path)


def snapshot_text(raw):
    """The tree, whether the caller passed `--json` or the plain text."""
    text = raw.strip()
    if not text:
        raise BrowseError(4, "snapshot is empty")
    if not text.startswith("{"):
        return text, {}
    try:
        blob = json.loads(text)
    except json.JSONDecodeError as err:
        raise BrowseError(4, "snapshot is not valid JSON: %s" % err)
    data = blob.get("data") if isinstance(blob, dict) else None
    if not isinstance(data, dict) or not isinstance(data.get("snapshot"), str):
        raise BrowseError(4, 'snapshot JSON has no "data.snapshot" string')
    refs = data.get("refs") if isinstance(data.get("refs"), dict) else {}
    return data["snapshot"], refs


def parse_attrs(blob):
    out = {}
    for part in (blob or "").split(","):
        part = part.strip()
        if not part:
            continue
        key, _, value = part.partition("=")
        out[key.strip()] = value.strip() if value else "true"
    return out


def operations_for(role):
    ops = []
    if role in CLICKABLE:
        ops.append("CLICK")
    if role in TYPEABLE:
        ops.append("TYPE_TEXT")
    if role in SELECTABLE:
        ops.append("SELECT")
    return ops


def parse_elements(text, refs):
    """One record per ref in the tree, with the ref that owns its options."""
    elements = []
    stack = []  # (indent, element) for the enclosing nodes
    for raw in text.splitlines():
        match = LINE.match(raw.rstrip())
        if not match:
            continue
        indent = len(match.group("indent"))
        while stack and stack[-1][0] >= indent:
            stack.pop()
        attrs = parse_attrs(match.group("attrs"))
        ref = attrs.get("ref", "")
        role = match.group("role")
        known = refs.get(ref) if isinstance(refs.get(ref), dict) else {}
        element = {
            "ref": ref,
            "role": known.get("role") or role,
            "name": match.group("name") or known.get("name") or "",
            "value": (match.group("value") or "").strip(),
            "parent": next(
                (item[1]["ref"] for item in reversed(stack)
                 if item[1]["role"] in OWNS_OPTIONS and item[1]["ref"]),
                "",
            ),
            "attrs": attrs,
        }
        element["ops"] = operations_for(element["role"])
        stack.append((indent, element))
        if ref:
            elements.append(element)
    if not elements:
        raise BrowseError(4, "no refs in the snapshot; re-snapshot with `-i`")
    return elements[:MAX_ELEMENTS]


def label(element):
    value = element["value"] or EMPTY
    text = "[%s] %s  %s · %s" % (
        element["ref"], element["role"], element["name"] or "(unnamed)", value,
    )
    return text[:MAX_LABEL]


def heads(elements):
    """One criteria map per target head, `none` when nothing is compatible."""
    out = {}
    for operation, head in TARGET_HEADS.items():
        offered = {
            element["ref"]: label(element)
            for element in elements if operation in element["ops"]
        }
        offered[NONE] = "no element on this observation can take %s" % operation
        out[head] = offered
    return out


def available(elements, criteria):
    ops = ["SCROLL_UP", "SCROLL_DOWN", "WAIT", "DONE", "BLOCKED"]
    for operation, head in TARGET_HEADS.items():
        if len(criteria[head]) > 1:
            ops.append(operation)
    return sorted(ops)


def cmd_state(args):
    text, refs = snapshot_text(read_source(args.snapshot))
    elements = parse_elements(text, refs)
    criteria = heads(elements)
    history = []
    if args.history:
        history = [
            line.strip() for line in read_source(args.history).splitlines()
            if line.strip()
        ][-MAX_HISTORY:]
    state = {
        "goal": args.goal,
        "step": args.step,
        "pass_if": args.pass_if,
        "url": args.url,
        "elements": "\n".join(label(element) for element in elements),
        "available": available(elements, criteria),
        "history": history,
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(
        json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    Path(args.criteria).parent.mkdir(parents=True, exist_ok=True)
    Path(args.criteria).write_text(
        json.dumps(criteria, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("state=%s criteria=%s elements=%d" % (args.out, args.criteria, len(elements)))
    return 0


def answers_of(path):
    try:
        blob = json.loads(read_source(path))
    except json.JSONDecodeError as err:
        raise BrowseError(4, "answer file is not valid JSON: %s" % err)
    answers = blob.get("answers") if isinstance(blob, dict) else None
    if not isinstance(answers, dict):
        raise BrowseError(4, 'answer file has no "answers" object')
    return answers


def acted_choice(answers, question):
    answer = answers.get(question)
    if not isinstance(answer, dict):
        raise BrowseError(5, "no answer for %s" % question)
    if not answer.get("act"):
        raise BrowseError(5, "%s did not clear act_at (%s at %s)" % (
            question, answer.get("confidence", "?"), answer.get("act_at", "?")))
    choice = answer.get("choice")
    if not isinstance(choice, str) or not choice:
        raise BrowseError(5, "%s has no choice" % question)
    return choice


def prefix(session):
    return ["agent-browser"] + (["--session", session] if session else [])


def build_argv(operation, element, session, text):
    head = prefix(session)
    if operation == "CLICK":
        return head + ["click", "@" + element["ref"]]
    if operation == "TYPE_TEXT":
        if not text:
            raise BrowseError(4, "TYPE_TEXT needs --text; the session model writes the string")
        return head + ["fill", "@" + element["ref"], text]
    if operation == "SELECT":
        if not element["parent"]:
            raise BrowseError(5, "option %s has no owning combobox in the snapshot" % element["ref"])
        if not element["name"]:
            raise BrowseError(5, "option %s has no accessible name to select by" % element["ref"])
        return head + ["select", "@" + element["parent"], element["name"]]
    if operation == "SCROLL_UP":
        return head + ["scroll", "up"]
    if operation == "SCROLL_DOWN":
        return head + ["scroll", "down"]
    if operation == "WAIT":
        return head + ["wait", str(WAIT_MS)]
    return []


def cmd_resolve(args):
    text, refs = snapshot_text(read_source(args.snapshot))
    elements = {element["ref"]: element for element in parse_elements(text, refs)}
    answers = answers_of(args.answer)
    operation = acted_choice(answers, "operation")
    if operation not in OPERATIONS:
        raise BrowseError(4, "unknown operation %r; known: %s" % (operation, ", ".join(OPERATIONS)))
    element = None
    head = TARGET_HEADS.get(operation)
    if head:
        target = acted_choice(answers, head)
        if target == NONE:
            raise BrowseError(5, "%s is %s; nothing to act on" % (head, NONE))
        element = elements.get(target)
        if element is None:
            raise BrowseError(4, "%s=%r was not in the observed snapshot" % (head, target))
        if operation not in element["ops"]:
            raise BrowseError(4, "%s cannot take %s" % (label(element), operation))
    argv = build_argv(operation, element, args.session, args.text)
    out = {
        "operation": operation,
        "ref": element["ref"] if element else "",
        "argv": argv,
        "verify": operation == "DONE",
    }
    if operation == "DONE":
        out["note"] = "navigation says it is finished; check pass_if against the page yourself"
    elif operation == "BLOCKED":
        out["note"] = "navigation cannot proceed; this is not the QA BLOCKED verdict"
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


def build_parser():
    parser = argparse.ArgumentParser(
        prog="browse.py", description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("state", help="snapshot -> qa.browse state and criteria")
    p.add_argument("--snapshot", default="-", help="snapshot file, or - for stdin")
    p.add_argument("--goal", default="", help="what this browser pass is for")
    p.add_argument("--step", default="", help="the PLAN.md step id and intent")
    p.add_argument("--pass-if", default="", dest="pass_if")
    p.add_argument("--url", default="")
    p.add_argument("--history", help="file of already executed actions, one per line")
    p.add_argument("--out", required=True)
    p.add_argument("--criteria", required=True)
    p.set_defaults(func=cmd_state)

    p = sub.add_parser("resolve", help="ask answer -> one agent-browser command")
    p.add_argument("--snapshot", required=True, help="the same snapshot the state was built from")
    p.add_argument("--answer", required=True, help="`bulma.py ask qa.browse --json` output")
    p.add_argument("--session", default="", help="agent-browser session name")
    p.add_argument("--text", default="", help="the string to type; required for TYPE_TEXT")
    p.set_defaults(func=cmd_resolve)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except BrowseError as err:
        print("browse: %s" % err, file=sys.stderr)
        return err.code


if __name__ == "__main__":
    sys.exit(main())
