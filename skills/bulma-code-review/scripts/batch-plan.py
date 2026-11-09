#!/usr/bin/env python3
"""Split a very large PR into review batches, then merge the batch results.

plan   reads the collected snapshot (files.json, PR_PATCH.diff, snapshot.json)
       and decides whether the PR is very large. Only then does it write
       batches.json and batches/<NN>/{FILES.txt,PATCH.diff}. Hotspot files go
       first; files from the same directory stay together.
merge  reads batches/<NN>/{coverage.json,findings.json} and writes the merged
       coverage.json and findings.json for the one review artifact. Exit 1
       when a batch is missing or left a file without a coverage row.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
from collections import OrderedDict
from pathlib import Path

VERY_LARGE_FILES = 50
VERY_LARGE_CHURN = 5000
MAX_FILES = 15
MAX_CHURN = 1500
SEVERITY = {"blocker": 0, "major": 1, "medium": 2, "minor": 2, "nit": 3}
GIT_B = re.compile(r"^diff --git a/(.+?) b/(.+)$")
MECHANICAL_SUFFIXES = (".lock", ".snap", ".min.js", ".map", ".svg", ".png", ".jpg", ".jpeg", ".gif", ".webp")
MECHANICAL_NAMES = frozenset({"package-lock.json", "yarn.lock", "pnpm-lock.yaml", "bun.lockb", "bun.lock"})


def _risk():
    path = Path(__file__).with_name("classify-risk.py")
    spec = importlib.util.spec_from_file_location("classify_risk", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def flat_files(directory: Path) -> list[dict]:
    pages = json.loads((directory / "files.json").read_text())
    return [item for page in pages for item in page]


def churn(item: dict) -> int:
    return int(item.get("additions") or 0) + int(item.get("deletions") or 0)


def mechanical(path: str) -> bool:
    lowered = path.lower()
    base = lowered.rsplit("/", 1)[-1]
    return base in MECHANICAL_NAMES or lowered.endswith(MECHANICAL_SUFFIXES) or "__snapshots__/" in lowered


def very_large(files: list[dict], snapshot: dict) -> tuple[bool, str]:
    total = sum(churn(f) for f in files)
    if snapshot.get("diff_source") == "local":
        return True, "api_diff_too_large"
    if len(files) > VERY_LARGE_FILES:
        return True, f"changed_files={len(files)}>{VERY_LARGE_FILES}"
    if total > VERY_LARGE_CHURN:
        return True, f"churn={total}>{VERY_LARGE_CHURN}"
    return False, f"changed_files={len(files)} churn={total}"


def split_patch(patch: str) -> dict[str, str]:
    """Map each changed path (new and old name) to its diff section."""
    sections: dict[str, str] = {}
    current: list[str] = []
    names: tuple[str, ...] = ()

    def flush():
        if names and current:
            text = "".join(current)
            for name in names:
                sections[name] = text

    for line in patch.splitlines(keepends=True):
        match = GIT_B.match(line.rstrip("\n"))
        if match:
            flush()
            current = [line]
            names = (match.group(1), match.group(2))
            continue
        current.append(line)
    flush()
    return sections


def group_key(path: str) -> str:
    parts = path.split("/")
    return "/".join(parts[:2]) if len(parts) > 2 else parts[0] if len(parts) > 1 else "."


def plan_batches(files: list[dict], max_files: int, max_churn: int) -> list[list[dict]]:
    risk = _risk()
    review = [f for f in files if not mechanical(f["filename"])]
    rest = [f for f in files if mechanical(f["filename"])]
    groups: "OrderedDict[str, list[dict]]" = OrderedDict()
    for item in review:
        groups.setdefault(group_key(item["filename"]), []).append(item)

    def rank(entry):
        key, items = entry
        high = any(risk.path_is_high(i["filename"]) for i in items)
        return (not high, -sum(churn(i) for i in items), key)

    batches: list[list[dict]] = []
    current: list[dict] = []
    size = 0
    for _, items in sorted(groups.items(), key=rank):
        items.sort(key=lambda i: (not risk.path_is_high(i["filename"]), -churn(i), i["filename"]))
        for item in items:
            if current and (len(current) >= max_files or size + churn(item) > max_churn):
                batches.append(current)
                current, size = [], 0
            current.append(item)
            size += churn(item)
    if current:
        batches.append(current)
    if rest:
        # Lockfiles, snapshots and assets: one batch, patch skim only.
        batches.append(rest)
    return batches


def plan(directory: Path, max_files: int, max_churn: int) -> dict:
    snapshot = json.loads((directory / "snapshot.json").read_text())
    files = flat_files(directory)
    large, reason = very_large(files, snapshot)
    out = directory / "batches.json"
    if not large:
        out.unlink(missing_ok=True)
        return {"batched": False, "reason": reason}
    sections = split_patch((directory / "PR_PATCH.diff").read_text(encoding="utf-8", errors="replace"))
    batches = plan_batches(files, max_files, max_churn)
    listing = []
    for index, batch in enumerate(batches, 1):
        folder = directory / "batches" / f"{index:02d}"
        folder.mkdir(parents=True, exist_ok=True)
        for stale in ("coverage.json", "findings.json"):
            (folder / stale).unlink(missing_ok=True)
        paths = [item["filename"] for item in batch]
        (folder / "FILES.txt").write_text("\n".join(paths) + "\n")
        seen: set[str] = set()
        chunks = []
        for path in paths:
            text = sections.get(path, "")
            if text and text not in seen:
                seen.add(text)
                chunks.append(text)
        (folder / "PATCH.diff").write_text("".join(chunks))
        listing.append({
            "id": f"{index:02d}",
            "dir": str(folder.relative_to(directory)),
            "files": paths,
            "churn": sum(churn(item) for item in batch),
            "mechanical": all(mechanical(p) for p in paths),
            "missing_patch": [p for p in paths if p not in sections],
        })
    result = {"head": snapshot["head"], "base": snapshot["base"], "reason": reason,
              "changed_files": len(files), "batches": listing}
    out.write_text(json.dumps(result, indent=2))
    return {"batched": True, "reason": reason, "batches": len(listing), "changed_files": len(files)}


def finding_key(finding: dict) -> tuple:
    return (str(finding.get("path") or ""), str(finding.get("line") or ""),
            str(finding.get("class") or finding.get("title") or ""))


def merge(directory: Path) -> tuple[dict, bool]:
    manifest = json.loads((directory / "batches.json").read_text())
    snapshot = json.loads((directory / "snapshot.json").read_text())
    if manifest.get("head") != snapshot.get("head") or manifest.get("base") != snapshot.get("base"):
        return {"complete": False, "error": "batches.json is for another head or base; re-plan"}, False
    coverage: list[dict] = []
    findings: dict[tuple, dict] = {}
    missing_batches: list[str] = []
    uncovered: list[str] = []
    for batch in manifest["batches"]:
        folder = directory / batch["dir"]
        try:
            rows = json.loads((folder / "coverage.json").read_text())
            found = json.loads((folder / "findings.json").read_text())
        except (OSError, ValueError):
            missing_batches.append(batch["id"])
            uncovered.extend(batch["files"])
            continue
        if isinstance(found, dict):
            found = found.get("findings", [])
        rows = [dict(row, batch=batch["id"]) for row in rows if isinstance(row, dict)]
        checked = {row.get("path") or row.get("file") for row in rows}
        uncovered.extend(p for p in batch["files"] if p not in checked)
        coverage.extend(rows)
        for item in found:
            if not isinstance(item, dict):
                continue
            key = finding_key(item)
            previous = findings.get(key)
            if previous is None or SEVERITY.get(item.get("severity"), 9) < SEVERITY.get(previous.get("severity"), 9):
                findings[key] = dict(item, batch=batch["id"])
    ordered = sorted(findings.values(), key=lambda f: (SEVERITY.get(f.get("severity"), 9), f.get("batch", "")))
    (directory / "coverage.json").write_text(json.dumps(coverage, indent=2))
    (directory / "findings.json").write_text(json.dumps(ordered, indent=2))
    complete = not missing_batches and not uncovered
    summary = {
        "complete": complete,
        "batches": len(manifest["batches"]),
        "missing_batches": missing_batches,
        "uncovered": uncovered,
        "covered_files": len({r.get("path") or r.get("file") for r in coverage}),
        "changed_files": manifest["changed_files"],
        "findings": {sev: sum(1 for f in ordered if f.get("severity") == sev) for sev in SEVERITY},
    }
    return summary, complete


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("action", choices=("plan", "merge"))
    parser.add_argument("--dir", type=Path, required=True, help="review_dir with a collected snapshot")
    parser.add_argument("--max-files", type=int, default=MAX_FILES)
    parser.add_argument("--max-churn", type=int, default=MAX_CHURN)
    args = parser.parse_args()
    try:
        if args.action == "plan":
            print(json.dumps(plan(args.dir, args.max_files, args.max_churn)))
            return 0
        summary, complete = merge(args.dir)
        print(json.dumps(summary))
        return 0 if complete else 1
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(2, f"{exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
