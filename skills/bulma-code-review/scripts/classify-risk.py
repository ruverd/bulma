#!/usr/bin/env python3
"""Print high/low risk, or JSON paths requiring human sign-off.

Path tokens and added-line keywords live here, not in the skill prose.
"""
from __future__ import annotations

import argparse
import json
import re
import sys

HIGH_TOKENS = frozenset(
    {
        "auth",
        "authentication",
        "authenticator",
        "authorization",
        "authorize",
        "billing",
        "crypto",
        "csrf",
        "impersonate",
        "impersonation",
        "invoice",
        "invoices",
        "jwt",
        "migrate",
        "migration",
        "migrations",
        "concurrent",
        "concurrency",
        "mutex",
        "oauth",
        "openapi",
        "passwd",
        "password",
        "payment",
        "payments",
        "permission",
        "permissions",
        "protobuf",
        "proto",
        "rbac",
        "schema",
        "semaphore",
        "swagger",
        "secret",
        "secrets",
        "session",
        "sessions",
        "sso",
        "tenant",
        "tenants",
        "webhook",
        "webhooks",
    }
)

# Lowercased needles matched only on added lines (not the +++ header).
HIGH_ADDED = (
    "$queryraw",
    "queryraw",
    "executeraw",
    "dangerouslysetinnerhtml",
    "innerhtml",
    "eval(",
    "child_process",
    "execsync",
    "sync.mutex",
    "deadlock",
    "waitgroup",
    "atomic.",
)

# Same thresholds as SKILL.md "Large PR".
WIDE_FILES = 25
WIDE_CHURN = 2500

CAMEL = re.compile(r"([a-z])([A-Z])")
ACRONYM = re.compile(r"([A-Z]+)([A-Z][a-z])")
SPLIT = re.compile(r"[^a-z0-9]+")

HUMAN_TOKENS = frozenset({
    "auth", "authentication", "authenticator", "authorization", "authorize",
    "oauth", "jwt", "rbac", "sso", "permission", "permissions",
    "impersonate", "impersonation", "password", "passwd", "session", "sessions",
    "billing", "seat", "seats", "payment", "payments", "invoice", "invoices",
    "secret", "secrets", "credential", "credentials", "terraform",
})


def tokens(path: str) -> set[str]:
    split = CAMEL.sub(r"\1 \2", path.replace("\\", "/"))
    split = ACRONYM.sub(r"\1 \2", split)
    return {part for part in SPLIT.split(split.lower()) if part}


def path_is_high(path: str) -> bool:
    lowered = path.replace("\\", "/").lower()
    if lowered.endswith(".sql") or path_needs_human(path):
        return True
    return bool(tokens(path) & HIGH_TOKENS)


def path_needs_human(path: str) -> bool:
    lowered = path.replace("\\", "/").lower()
    parts = lowered.split("/")
    return (
        ".github/workflows/" in lowered
        or lowered.endswith((".tf", ".tf.json", ".tfvars", ".tfvars.json", ".pem", ".key"))
        or any(part == ".env" or part.startswith(".env.") for part in parts)
        or bool(tokens(path) & HUMAN_TOKENS)
    )


def added_lines(patch: str) -> list[str]:
    out = []
    for raw in patch.splitlines():
        if raw.startswith("+++") or not raw.startswith("+"):
            continue
        out.append(raw[1:])
    return out


def patch_is_high(patch: str) -> bool:
    for line in added_lines(patch):
        lowered = line.lower()
        if any(needle in lowered for needle in HIGH_ADDED):
            return True
    return False


def read_files(args: argparse.Namespace) -> list[str]:
    paths: list[str] = list(args.paths)
    if args.files_from:
        source = sys.stdin if args.files_from == "-" else open(
            args.files_from, encoding="utf-8"
        )
        with source as handle:
            paths.extend(line.strip() for line in handle if line.strip())
    return paths


def classify(
    paths: list[str],
    patch: str,
    changed_files: int = 0,
    churn: int = 0,
) -> str:
    if changed_files > WIDE_FILES or churn > WIDE_CHURN:
        return "high"
    if any(path_is_high(path) for path in paths):
        return "high"
    if patch and patch_is_high(patch):
        return "high"
    return "low"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*")
    parser.add_argument("--files-from")
    parser.add_argument("--patch")
    parser.add_argument("--human-signoff", action="store_true",
                        help="print JSON paths that require human sign-off")
    parser.add_argument("--changed-files", type=int, default=0)
    parser.add_argument("--churn", type=int, default=0)
    args = parser.parse_args()
    paths = read_files(args)
    if args.human_signoff:
        print(json.dumps([path for path in paths if path_needs_human(path)]))
        return 0
    patch = ""
    if args.patch:
        patch = open(args.patch, encoding="utf-8").read()
    print(
        classify(
            paths,
            patch,
            changed_files=args.changed_files,
            churn=args.churn,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
