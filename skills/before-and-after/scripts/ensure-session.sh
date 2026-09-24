#!/usr/bin/env bash
# Shared agent-browser session for this GitHub repo (not per-worktree).
# Prints KEY=value. Cookies live under $BULMA_HOME/agent-browser/, never git.
set -euo pipefail

BULMA_HOME="${BULMA_HOME:-$HOME/.bulma}"

owner_repo=""
if command -v gh >/dev/null 2>&1; then
  owner_repo="$(gh repo view --json nameWithOwner --jq -r .nameWithOwner 2>/dev/null || true)"
fi
if [[ -z "$owner_repo" ]]; then
  url="$(git remote get-url origin 2>/dev/null || true)"
  url="${url%.git}"
  case "$url" in
    git@*:*/*)
      owner_repo="${url#*:}"
      ;;
    https://github.com/*|http://github.com/*|ssh://git@github.com/*)
      owner_repo="${url#*github.com/}"
      owner_repo="${owner_repo#*:}"
      ;;
    *)
      owner_repo=""
      ;;
  esac
fi
if [[ -z "$owner_repo" ]]; then
  echo "cannot resolve owner/repo (gh repo view or git remote origin)" >&2
  exit 1
fi

session="$(printf '%s' "$owner_repo" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g; s/--*/-/g; s/^-//; s/-$//')"
session="bulma-${session}"
dir="${BULMA_HOME}/agent-browser/${session}"
mkdir -p "${dir}/captures"

printf 'SESSION=%s\n' "$session"
printf 'STATE_DIR=%s\n' "$dir"
printf 'CAPTURE_DIR=%s\n' "${dir}/captures"
printf 'BULMA_HOME=%s\n' "$BULMA_HOME"
