#!/usr/bin/env python3
"""The project's pre-rename name must not come back.

The legacy word is read from install.sh (`LEGACY="..."`), so it is written in
exactly one place. It may appear only between the `legacy layout migration
(begin)` and `(end)` markers in install.sh and tests/install.sh, which move an
old install to the new layout. Every other tracked file, and every tracked
path, must be free of it, case-insensitively.
"""
import os
import re
import subprocess
import sys

BLOCK_FILES = ("install.sh", "tests/install.sh")
BEGIN = "legacy layout migration (begin)"
END = "legacy layout migration (end)"


def legacy_word(root):
    text = open(os.path.join(root, "install.sh"), encoding="utf-8").read()
    match = re.search(r'^LEGACY="([a-z]+)"$', text, re.M)
    if not match:
        raise SystemExit("install.sh: no LEGACY=\"...\" line inside the migration block")
    return match.group(1)


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    word = legacy_word(root)
    pattern = re.compile(re.escape(word), re.I)
    tracked = subprocess.run(["git", "-C", root, "ls-files", "-z"], capture_output=True, text=True, check=True)
    errors = []
    for rel in filter(None, tracked.stdout.split("\0")):
        if pattern.search(rel):
            errors.append("%s: path contains the legacy name" % rel)
        path = os.path.join(root, rel)
        try:
            lines = open(path, encoding="utf-8").read().splitlines()
        except (UnicodeDecodeError, FileNotFoundError, IsADirectoryError):
            continue
        inside = False
        for lineno, line in enumerate(lines, 1):
            if rel in BLOCK_FILES and BEGIN in line:
                inside = True
            if not inside and pattern.search(line):
                errors.append("%s:%d: legacy name -> %s" % (rel, lineno, line.strip()[:100]))
            if rel in BLOCK_FILES and END in line:
                inside = False
    for line in errors:
        print(line)
    if errors:
        print("%d legacy-name reference(s)" % len(errors), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
