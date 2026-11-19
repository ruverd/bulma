"""Plan a delivery stack and reconcile its pull requests against GitHub and origin."""

import argparse
from graphlib import CycleError, TopologicalSorter
import json
from pathlib import Path
import re
import subprocess
import sys

sys.dont_write_bytecode = True
from delivery_pr import check_base, pull_for_head


def branch(name):
    if not name or name.startswith("-") or subprocess.run(
        ["git", "check-ref-format", f"refs/heads/{name}"], capture_output=True
    ).returncode:
        raise ValueError(f"Invalid branch: {name!r}.")
    return name


def plan(data, repo=None, default=None, anchor=None, qa="final"):
    source = data["source"]
    if source not in {"linear", "explicit", "planned", "integrated"}:
        raise ValueError(f"Unknown stack source: {source}.")
    parent = data["parent"]
    children = data["children"]
    if source == "linear":
        if data.get("children_complete") is not True or not data["parent_ids"]:
            raise ValueError("Linear child discovery is incomplete.")
        if any(child["parentId"] not in data["parent_ids"] for child in children):
            raise ValueError("Linear returned an issue outside the requested parent.")
        children = [child for child in children
                    if child["statusType"] not in {"completed", "canceled", "duplicate"}
                    and not child.get("archivedAt")]
        if not children:
            return {"mode": "delivery"}
    elif len(children) < 2 or source == "integrated":
        return {"mode": "delivery"}

    if not repo or not re.fullmatch(r"[^/\s]+/[^/\s]+", repo) or not default or not anchor:
        raise ValueError("A stack needs the forge repository, default branch and its initial SHA.")
    if not re.fullmatch(r"[0-9a-f]{40}", anchor):
        raise ValueError("Anchor must be a full GitHub commit SHA.")

    by_id = {child["id"]: child for child in children}
    if len(by_id) != len(children) or parent["id"] in by_id:
        raise ValueError("Stack members need distinct identities.")
    ids = sorted(by_id)
    predecessors = {key: sorted(set(by_id[key]["depends_on"]) & by_id.keys()) for key in ids}
    try:
        order = list(TopologicalSorter(predecessors).static_order())
    except CycleError as exc:
        raise ValueError(f"Stack dependency cycle: {' → '.join(exc.args[1])}.") from exc

    members = [by_id[key] for key in order] + [parent]
    heads = [branch("feature/" + row["id"].lower()) for row in members]
    bases = heads[1:] + [branch(default)]
    if len(set(heads + [default])) != len(heads) + 1:
        raise ValueError("Stack branches collide with each other or the default branch.")
    entries = []
    for index, (row, head, base) in enumerate(zip(members, heads, bases)):
        final = index == len(heads) - 1
        number = index + 1
        ordinal = {1: "First", 2: "Second", 3: "Third"}.get(number, f"{number} of {len(heads)}")
        entries.append({
            "id": row["id"], "task": row["task"], "head": head, "base": base,
            "depends_on": row.get("depends_on", []),
            "position": "Final / Umbrella" if final else ordinal, "final": final,
        })
    return {"mode": "stack", "repo": repo, "default": default, "anchor": anchor,
            "qa": qa, "entries": entries}


def git(checkout, *args, check=True):
    return subprocess.run(
        ["git", "-C", checkout, *args], check=check, text=True, stdout=subprocess.PIPE
    )


def origin_refs(checkout, heads):
    refs = {}
    output = git(checkout, "ls-remote", "--symref", "origin", "HEAD",
                 *(f"refs/heads/{head}" for head in heads)).stdout
    for line in output.splitlines():
        value, ref = line.split("\t", 1)
        if ref == "HEAD" and value.startswith("ref: refs/heads/"):
            refs["HEAD"] = value.removeprefix("ref: refs/heads/")
        elif ref.startswith("refs/heads/"):
            refs[ref.removeprefix("refs/heads/")] = value
    return refs


def ancestor(checkout, old, new):
    if not old or not new:
        return False
    result = git(checkout, "merge-base", "--is-ancestor", old, new, check=False)
    if result.returncode not in (0, 1):
        raise ValueError(f"Cannot verify commit ancestry {old} → {new}.")
    return result.returncode == 0


def verify_chain(stack, entries, pulls):
    # Follow observed PR bases when they exist. The saved plan supplies only the
    # missing suffix. A mismatch is drift, even if the new edges form a chain.
    by_head = {entry["head"]: (entry, pr) for entry, pr in zip(entries, pulls)}
    destinations = {}
    for head, (entry, pr) in by_head.items():
        if pr:
            check_base(pr, stack["repo"], entry["base"])
        destinations[head] = pr["base"]["ref"] if pr else entry["base"]
    current = set(by_head) - set(destinations.values())
    if len(current) != 1 or len(by_head) != len(entries):
        raise ValueError("Saved stack has no unique first branch.")
    head = current.pop()
    ordered = []
    while head in by_head:
        entry, pr = by_head.pop(head)
        ordered.append((entry, pr))
        head = destinations[head]
    if (by_head or head != stack["default"] or not ordered[-1][0]["final"]
            or any(entry["final"] for entry, _ in ordered[:-1])):
        raise ValueError("Stack does not form a single chain to the default branch.")
    preceding = set()
    ids = {entry["id"] for entry in entries}
    for entry, _ in ordered:
        if (set(entry["depends_on"]) & ids) - preceding:
            raise ValueError(f"Stack order violates dependencies for {entry['id']}.")
        preceding.add(entry["id"])
    return ordered


def verify_prior_gates(rows, gates, anchor):
    for row in rows:
        if row["status"] != "merged":
            break
        gate = gates.get(row["id"], {})
        scoped = gate.get("ci_scope", {})
        ci_passed = gate.get("ci") == "green" or (
            gate.get("ci") == "out_of_scope"
            and (scoped.get("status"), scoped.get("head"), scoped.get("base"))
            == ("out_of_scope", row["head_sha"], anchor)
        )
        if ((gate.get("head"), gate.get("base")) != (row["head_sha"], anchor)
                or not ci_passed or gate.get("review") not in {"pass", "skip"}):
            raise ValueError(f"Cannot advance past {row['id']} without CI and review receipts for its merged head and base.")


def reconcile(checkout, stack, candidate=None, prepare=False, gates=None):
    entries = stack["entries"]
    anchor = stack["anchor"]
    default = stack["default"]
    refs = origin_refs(checkout, {default, *(entry["head"] for entry in entries)})
    if refs.get("HEAD") != default or not refs.get(default):
        raise ValueError(f"Origin default branch drift: expected {default}, found {refs.get('HEAD')}.")

    pulls = [pull_for_head(stack["repo"], entry["head"]) for entry in entries]
    ordered = verify_chain(stack, entries, pulls)
    # Fetch current tips and only fetch retired PR heads if their commits are missing locally.
    live_refs = {name: refs[name] for name in [default, *(entry["head"] for entry in entries)] if name in refs}
    fetch = [f"refs/heads/{name}" for name in live_refs]
    for _, pr in ordered:
        if pr and pr["head"]["sha"] not in live_refs.values() and git(
            checkout, "cat-file", "-e", f"{pr['head']['sha']}^{{commit}}", check=False
        ).returncode:
            fetch.append(f"refs/pull/{pr['number']}/head")
    git(checkout, "fetch", "--no-tags", "origin", *fetch)
    if not ancestor(checkout, anchor, refs[default]):
        raise ValueError(f"Default branch {default} diverged from the saved stack anchor.")

    rows = []
    active = None
    incoming = None
    for index, (entry, pr) in enumerate(ordered):
        entry = {**entry, "qa_required": entry["final"] and stack["qa"] == "final"}
        head, base = entry["head"], entry["base"]
        tip, base_tip = refs.get(head), refs.get(base)
        if active is not None and (pr or tip not in (None, anchor)):
            raise ValueError(f"{head} advanced before its predecessor merged.")
        if pr and pr["merged"]:
            successor = ordered[index + 1][1] if not entry["final"] else None
            receiver = successor["head"]["sha"] if successor else base_tip
            incoming = pr["merge_commit_sha"]
            if not ancestor(checkout, incoming, receiver):
                raise ValueError(f"{pr['html_url']} merge result is missing from {base}.")
            status = "merged"
        elif active is None:
            start = incoming or anchor
            if pr:
                if tip != pr["head"]["sha"] or base_tip != pr["base"]["sha"]:
                    raise ValueError(f"GitHub and origin disagree on refs for {pr['html_url']}; retry the check.")
                if not ancestor(checkout, start, tip) or (tip == start and not entry["final"]):
                    raise ValueError(f"{head} lacks the expected stack input or has no changes to deliver.")
            elif (incoming and tip is None) or tip not in (None, start, candidate):
                raise ValueError(f"Unexpected tip on {head}; reconcile the saved worker and branch.")
            elif tip == candidate and tip and not ancestor(checkout, start, tip):
                raise ValueError(f"Unpublished candidate on {head} diverged from its start commit.")
            if not entry["final"] and (base_tip not in (None, anchor) or (pr and base_tip != anchor)):
                raise ValueError(f"Unexpected tip on destination {base}; reconcile before continuing.")
            active = {**entry, "start_sha": start, "head_sha": tip,
                      "base_sha": base_tip or anchor, "pr_url": pr["html_url"] if pr else None}
            status = "open" if pr else "next"
        else:
            status = "planned"

        rows.append({**entry, "status": status,
                     "pr_url": pr["html_url"] if pr else None,
                     "head_sha": pr["head"]["sha"] if pr else None,
                     "draft": pr["draft"] if pr else None,
                     "merge_sha": pr["merge_commit_sha"] if status == "merged" else None,
                     "title": pr["title"] if pr else None})

    if prepare and active and not active["pr_url"]:
        verify_prior_gates(rows, gates or {}, anchor)
        if active["base"] not in refs:
            target = f"refs/heads/{active['base']}"
            git(checkout, "push", f"--force-with-lease={target}:", "origin", f"{anchor}:{target}")
    return {"status": "active" if active else "merged", "active": active, "order": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("plan")
    create.add_argument("--repo")
    create.add_argument("--default")
    create.add_argument("--anchor")
    create.add_argument("--qa", choices=("final", "none"), default="final")
    check = commands.add_parser("reconcile")
    check.add_argument("--checkout", default=".")
    check.add_argument("--plan", required=True, type=Path)
    check.add_argument("--candidate")
    check.add_argument("--gates", type=Path)
    check.add_argument("--prepare", action="store_true")
    args = parser.parse_args()
    try:
        if args.command == "plan":
            result = plan(json.load(sys.stdin), args.repo, args.default, args.anchor, args.qa)
        else:
            gates = json.loads(args.gates.read_text()) if args.gates else None
            result = reconcile(args.checkout, json.loads(args.plan.read_text()),
                               args.candidate, args.prepare, gates)
        print(json.dumps(result, indent=2))
    except (KeyError, TypeError, ValueError, OSError, subprocess.CalledProcessError) as exc:
        parser.exit(2, f"{exc}\n")


if __name__ == "__main__":
    main()
