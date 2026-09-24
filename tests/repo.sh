#!/usr/bin/env bash
# Repo invariants. Structure, links, frontmatter, manifests.
# Dev-only: needs python3. End users installing skills need just git and curl.
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LIB="$ROOT/tests/lib"
FAILED=0

ok() { echo "ok  $*"; }
bad() { echo "FAIL: $*" >&2; FAILED=1; }

check() {
  local name="$1"
  shift
  local out
  if out="$("$@" 2>&1)"; then
    ok "$name"
  else
    bad "$name"
    if [[ -n "$out" ]]; then
      while IFS= read -r line; do
        printf '      %s\n' "$line" >&2
      done <<<"$out"
    fi
  fi
}

need_python() {
  command -v python3 >/dev/null 2>&1 && return 0
  echo "FAIL: python3 is required to run tests/repo.sh" >&2
  exit 1
}

need_python

# CI lints every tracked script. Locally the linter is optional, so this suite
# still works on a machine that does not have it. (Do not start a comment with
# the linter's name: it gets parsed as a directive.)
if command -v shellcheck >/dev/null 2>&1; then
  # shellcheck disable=SC2046  # word splitting is what we want here
  check shellcheck shellcheck $(git -C "$ROOT" ls-files '*.sh' | sed "s|^|$ROOT/|")
else
  echo "skip shellcheck (not installed)"
fi

check links python3 "$LIB/check_links.py" "$ROOT"
check frontmatter env PYTHONPATH="$LIB" python3 "$LIB/check_frontmatter.py" "$ROOT"
check manifests env PYTHONPATH="$LIB" python3 "$LIB/check_manifests.py" "$ROOT"
check enums env PYTHONPATH="$LIB" python3 "$LIB/check_enums.py" "$ROOT"
check structure python3 "$LIB/check_structure.py" "$ROOT"
check graphs python3 "$LIB/check_graphs.py" "$ROOT"
check leaks python3 "$LIB/check_leaks.py" "$ROOT"
check branch-name python3 "$LIB/check_branch_name.py" "$ROOT"
check legacy-name python3 "$LIB/check_legacy_name.py" "$ROOT"

if [[ "$FAILED" -ne 0 ]]; then
  echo "repo checks failed" >&2
  exit 1
fi
echo "all passed"
