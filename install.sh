#!/usr/bin/env bash
# Install and update Bulma skills (flatten into agent homes).
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/ruverd/bulma/main/install.sh | bash
#   ./install.sh setup
#   bulma update
#   bulma status
#   bulma uninstall
#
# Options: --dry-run  --yes / -y  --help
# Compat:  --uninstall  (same as uninstall)

set -euo pipefail

usage() {
  cat <<'EOF'
Install and update Bulma skills.

Usage:
  bulma                 Menu (TTY) or command list (no TTY)
  bulma setup           Flatten skills into agent homes
  bulma update          git pull --ff-only main, then setup
  bulma status          Repo, version, SHA, homes, worktrees, cwd job Walk
  bulma report          Wall time and laps per graph node; host token totals when a transcript exists
  bulma uninstall       Remove our symlinks
  bulma uninstall --purge
                        Also delete the managed clone
  bulma version         Print the version

Options:
  --dry-run       Print actions, write nothing
  --yes, -y       Skip confirmations
  --only <hosts>  Comma-separated: claude, grok, cursor, codex
  --all           Every host, even ones not installed here
  --no-path       Do not touch ~/.zshrc or ~/.bashrc
  -h, --help      Show this help
  -V, --version   Print the version

Examples:
  curl -fsSL https://raw.githubusercontent.com/ruverd/bulma/main/install.sh | bash
  bulma setup
  bulma update
  bulma status
  bulma report
  bulma uninstall
EOF
}

CMD=""
DRY=0
YES=0
PURGE=0
UNINSTALL=0
ONLY=""
ALL=0
NO_PATH=0
ALL_HOSTS="claude grok cursor codex"

while [[ $# -gt 0 ]]; do
  case "$1" in
    setup|update|status|report|uninstall|menu|help|version)
      if [[ -n "$CMD" && "$CMD" != "$1" ]]; then
        echo "unknown arg: $1" >&2
        usage
        exit 1
      fi
      CMD="$1"
      shift
      ;;
    --dry-run) DRY=1; shift ;;
    --yes|-y) YES=1; shift ;;
    --all) ALL=1; shift ;;
    --no-path) NO_PATH=1; shift ;;
    --only)
      shift
      if [[ $# -eq 0 ]]; then
        echo "--only needs a host: $ALL_HOSTS" >&2
        exit 1
      fi
      for h in ${1//,/ }; do
        case " $ALL_HOSTS " in
          *" $h "*) ;;
          *) echo "unknown host: $h (known: $ALL_HOSTS)" >&2; exit 1 ;;
        esac
      done
      ONLY="$1"
      shift
      ;;
    --purge) PURGE=1; shift ;;
    --uninstall) CMD="uninstall"; UNINSTALL=1; shift ;;
    --plugin|--grok-plugin)
      echo "Plugin install is not part of bulma. Add the marketplace first:" >&2
      echo "  claude plugin marketplace add ruverd/bulma" >&2
      echo "  claude plugin install bulma@bulma" >&2
      echo "  grok plugin marketplace add ruverd/bulma" >&2
      echo "  grok plugin install bulma --trust" >&2
      exit 1
      ;;
    -h|--help)
      if [[ -n "$CMD" && "$CMD" != "help" ]]; then
        usage
        exit 0
      fi
      usage
      exit 0
      ;;
    --version|-V)
      CMD="version"
      shift
      ;;
    *)
      echo "unknown arg: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ "$CMD" == "help" ]]; then
  usage
  exit 0
fi

if [[ "$CMD" == "uninstall" ]]; then
  UNINSTALL=1
fi

resolve_file() {
  local target="$1"
  local dir dest
  while [[ -L "$target" ]]; do
    dir="$(cd "$(dirname "$target")" && pwd)"
    dest="$(readlink "$target")"
    case "$dest" in
      /*) target="$dest" ;;
      *) target="$dir/$dest" ;;
    esac
  done
  dir="$(cd "$(dirname "$target")" && pwd)"
  echo "$dir/$(basename "$target")"
}

SELF="$(resolve_file "${BASH_SOURCE[0]:-$0}")"
REPO="$(cd "$(dirname "$SELF")" && pwd)"
BACKUP_ROOT="${SKILLS_BACKUP_ROOT:-${AI_SKILLS_BACKUP_ROOT:-$HOME/.skills-backups}}"
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/bulma"
CONFIG_FILE="$CONFIG_DIR/config"
DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
MANAGED_REPO="$DATA_HOME/bulma/repo"
DEFAULT_ORIGIN="https://github.com/ruverd/bulma.git"
BIN_DIR="$HOME/.local/bin"
BIN_LINK="$BIN_DIR/bulma"

config_get() {
  local key="$1"
  [[ -f "$CONFIG_FILE" ]] || return 0
  sed -n "s/^${key}=//p" "$CONFIG_FILE" | head -1
}

config_set_repo() {
  run mkdir -p "$CONFIG_DIR"
  if [[ "$DRY" -eq 1 ]]; then
    echo "dry-run: write $CONFIG_FILE repo=$1"
    return 0
  fi
  printf 'repo=%s\norigin=%s\n' "$1" "${2:-$DEFAULT_ORIGIN}" >"$CONFIG_FILE"
}

plugin_version() {
  sed -n 's/.*"version": "\([^"]*\)".*/\1/p' "$REPO/plugin.json" | head -1
}

ensure_bulma_home() {
  run mkdir -p "${BULMA_HOME:-$HOME/.bulma}"
}

# --- legacy layout migration (begin) -----------------------------------------
# One-time move from the layout used before the project was renamed to Bulma.
# Idempotent: every step checks before it acts, and never overwrites a target
# that already exists. tests/repo.sh allows the old name only inside this block.
LEGACY="ruver"

legacy_state_dir() {  # .<legacy>-<graph> -> .bulma-<graph>; the router's own dir -> .bulma-core
  local base="$1" graph
  graph="${base#."$LEGACY"-}"
  if [[ "$graph" == "bulma" ]]; then
    echo ".bulma-core"
  else
    echo ".bulma-$graph"
  fi
}

legacy_rewrite() {  # file python-expr: rewrite a text file in place
  local file="$1" expr="$2"
  [[ -f "$file" ]] || return 0
  if [[ "$DRY" -eq 1 ]]; then
    echo "dry-run: rewrite $file"
    return 0
  fi
  LEGACY="$LEGACY" python3 - "$file" "$expr" <<'PY'
import os, sys
path, expr = sys.argv[1], sys.argv[2]
old = os.environ["LEGACY"]
text = open(path, encoding="utf-8").read()
new = eval(expr, {"text": text, "old": old})
if new != text:
    open(path, "w", encoding="utf-8").write(new)
PY
}

migrate_legacy() {
  local new_home="${BULMA_HOME:-$HOME/.bulma}"
  local old_home="$HOME/.$LEGACY"
  if [[ ! -e "$old_home" && -d "$HOME/.grok/$LEGACY" ]]; then
    old_home="$HOME/.grok/$LEGACY"
  fi
  if [[ -e "$old_home" && ! -e "$new_home" ]]; then
    echo "move   $old_home -> $new_home"
    run mv "$old_home" "$new_home"
  fi
  local d base target
  if [[ -d "$new_home" ]]; then
    for d in "$new_home"/*/."$LEGACY"-*; do
      [[ -d "$d" ]] || continue
      base="$(basename "$d")"
      target="$(dirname "$d")/$(legacy_state_dir "$base")"
      [[ -e "$target" ]] && continue
      run mv "$d" "$target"
    done
    for d in "$new_home/agent-browser/$LEGACY"-*; do
      [[ -d "$d" ]] || continue
      target="$new_home/agent-browser/bulma-${d##*/"$LEGACY"-}"
      [[ -e "$target" ]] || run mv "$d" "$target"
    done
    legacy_rewrite "$new_home/insights/observations.jsonl" \
      'text.replace("\"reviewer\": \"%s-" % old, "\"reviewer\": \"bulma-").replace("\"reviewer\":\"%s-" % old, "\"reviewer\":\"bulma-")'
  fi
  local old_config="${XDG_CONFIG_HOME:-$HOME/.config}/$LEGACY"
  if [[ -d "$old_config" && ! -e "$CONFIG_DIR" ]]; then
    echo "move   $old_config -> $CONFIG_DIR"
    run mv "$old_config" "$CONFIG_DIR"
  fi
  local old_data="$DATA_HOME/$LEGACY" new_data="$DATA_HOME/bulma"
  if [[ -d "$old_data" && ! -e "$new_data" ]]; then
    # A managed install runs from inside that directory. Compare physical
    # paths (//, /var -> /private/var) so REPO follows the move.
    local old_real repo_real
    old_real="$(cd "$old_data" && pwd -P)"
    repo_real="$(cd "$REPO" && pwd -P)"
    echo "move   $old_data -> $new_data"
    run mv "$old_data" "$new_data"
    if [[ "$repo_real" == "$old_real"/* && "$DRY" -ne 1 ]]; then
      REPO="$(cd "$new_data" && pwd -P)${repo_real#"$old_real"}"
      SELF="$REPO/install.sh"
      config_set_repo "$REPO"
    fi
  fi
  legacy_rewrite "$CONFIG_FILE" 'text.replace("/%s/repo" % old, "/bulma/repo")'
  if [[ -L "$BIN_DIR/$LEGACY" ]]; then
    echo "rm     $BIN_DIR/$LEGACY (the command is now: bulma)"
    run rm "$BIN_DIR/$LEGACY"
  fi
  local dir link
  for dir in "$HOME"/.{agents,claude,grok,cursor,codex}/{skills,agents,commands}; do
    [[ -d "$dir" ]] || continue
    for link in "$dir"/*; do
      base="$(basename "$link")"
      if [[ -L "$link" ]]; then
        [[ "$base" == *"$LEGACY"* ]] || continue
        target="$(readlink "$link")"
        # Ours: into this checkout, or into the managed clone before it moved.
        if [[ "$target" == "$REPO/"* || "$target" == *"/$LEGACY/repo/"* ]]; then
          echo "prune  $link"
          run rm "$link"
        fi
      elif [[ -f "$link/.$LEGACY-installed-copy" ]] && grep -qx "managed-by=$LEGACY" "$link/.$LEGACY-installed-copy"; then
        if [[ "$base" == *"$LEGACY"* ]]; then
          echo "prune  $link"
          run rm -rf "$link"
        else
          echo "adopt  $link"
          run rm "$link/.$LEGACY-installed-copy"
          [[ "$DRY" -eq 1 ]] || printf 'managed-by=bulma\n' >"$link/$CODEX_COPY_MARKER"
        fi
      fi
    done
  done
  local rc
  for rc in "$HOME/.zshrc" "$HOME/.bashrc"; do
    [[ -f "$rc" ]] && grep -q "^# $LEGACY PATH$" "$rc" && legacy_rewrite "$rc" 'text.replace("# %s PATH\n" % old, "# bulma PATH\n")'
  done
  return 0
}
# --- legacy layout migration (end) -------------------------------------------

ensure_bin() {
  run mkdir -p "$BIN_DIR"
  run ln -sfn "$SELF" "$BIN_LINK"
  echo "link   $BIN_LINK -> $SELF"
}

gh_attach_ok() {
  command -v gh >/dev/null 2>&1 || return 1
  local ver major rest minor
  ver="$(gh --version 2>/dev/null | head -1 | grep -oE '[0-9]+\.[0-9]+' | head -1 || true)"
  [[ -n "$ver" ]] || return 1
  major="${ver%%.*}"
  rest="${ver#*.}"
  minor="${rest%%.*}"
  if (( major > 2 )); then return 0; fi
  if (( major == 2 && minor >= 99 )); then return 0; fi
  return 1
}

install_agent_browser_bin() {
  if command -v brew >/dev/null 2>&1; then
    brew install agent-browser
    return
  fi
  if command -v npm >/dev/null 2>&1; then
    npm install -g agent-browser
    return
  fi
  echo "warn   install agent-browser from https://agent-browser.dev/" >&2
  return 1
}

ensure_agent_browser() {
  if [[ "${BULMA_SKIP_DEPS:-0}" = "1" ]]; then
    echo "skip   agent-browser (BULMA_SKIP_DEPS)"
    return 0
  fi
  if [[ "$DRY" -eq 1 ]]; then
    echo "dry-run: install agent-browser + Chrome if missing"
    return 0
  fi
  if ! command -v agent-browser >/dev/null 2>&1; then
    echo "need   agent-browser"
    install_agent_browser_bin || true
  fi
  if command -v agent-browser >/dev/null 2>&1; then
    echo "ok     agent-browser $(agent-browser --version 2>/dev/null | head -1)"
    agent-browser install >/dev/null || echo "warn   agent-browser install (Chrome) failed" >&2
  else
    echo "warn   agent-browser missing. UI /qa is BLOCKED until it is installed." >&2
    echo "       brew install agent-browser && agent-browser install" >&2
  fi
  if command -v gh >/dev/null 2>&1; then
    if gh_attach_ok; then
      echo "ok     gh $(gh --version 2>/dev/null | head -1)"
    else
      echo "warn   gh is older than 2.99; --attach will fail. brew upgrade gh" >&2
    fi
  else
    echo "warn   gh missing; PR attach needs GitHub CLI ≥ 2.99" >&2
  fi
}

hint_jev() {
  if [[ -n "${TYPESAFE_API_KEY:-}" ]]; then
    echo "ok     jev (TYPESAFE_API_KEY set; /bulma available)"
  else
    echo "skip   jev (optional; /bulma needs TYPESAFE_API_KEY from https://console.typesafe.ai)"
  fi
}

ensure_path_snippet() {
  local line='# bulma PATH'
  local block rc
  case ":$PATH:" in
    *":$BIN_DIR:"*) return 0 ;;
  esac
  if [[ "$NO_PATH" -eq 1 ]]; then
    echo "skip   shell rc files (--no-path). Add this yourself:"
    return 0
  fi
  # shellcheck disable=SC2016  # $PATH must reach the rc file unexpanded
  block=$(printf '%s\nexport PATH="%s:$PATH"\n' "$line" "$BIN_DIR")
  for rc in "$HOME/.zshrc" "$HOME/.bashrc"; do
    if [[ -f "$rc" ]] && grep -q "$line" "$rc"; then
      continue
    fi
    if [[ "$DRY" -eq 1 ]]; then
      echo "dry-run: append PATH to $rc"
      continue
    fi
    # Say which file is being edited. This runs under curl | bash, where a
    # silent write to a shell rc is not something to spring on anyone.
    echo "rc     append PATH block to $rc"
    mkdir -p "$(dirname "$rc")"
    touch "$rc"
    printf '\n%s\n' "$block" >>"$rc"
  done
}

# Which hosts to touch. Default is the ones already on this machine, so we do
# not create ~/.codex for someone who has never installed Codex. --only and
# --all are explicit overrides; uninstall always sweeps every host so it can
# clean up an install made under a different selection.
selected_hosts() {
  local h out=""
  if [[ -n "$ONLY" ]]; then
    echo "${ONLY//,/ }"
    return 0
  fi
  if [[ "$ALL" -eq 1 || "$UNINSTALL" -eq 1 ]]; then
    echo "$ALL_HOSTS"
    return 0
  fi
  for h in $ALL_HOSTS; do
    [[ -d "$HOME/.$h" ]] && out="$out $h"
  done
  echo "$out"
}

# Grok and Claude read agents/ and commands/. Cursor and Codex use skills.
host_has_agents() {
  case "$1" in
    claude|grok) return 0 ;;
    *) return 1 ;;
  esac
}

install_for_hosts() {
  local hosts h
  hosts="$(selected_hosts)"
  local shared_skills_dir="$HOME/.agents/skills"
  local skills_dirs=()
  local agents_dirs=()
  local commands_dirs=()
  local codex_skills_dir=""
  for h in $hosts; do
    if [[ "$h" == "codex" ]]; then
      codex_skills_dir="$HOME/.codex/skills"
    else
      skills_dirs+=("$HOME/.$h/skills")
    fi
    if host_has_agents "$h"; then
      agents_dirs+=("$HOME/.$h/agents")
      commands_dirs+=("$HOME/.$h/commands")
    fi
  done
  if [[ -z "$codex_skills_dir" ]]; then
    skills_dirs+=("$shared_skills_dir")
  fi
  echo "hosts  ${hosts:-(none detected; ~/.agents/skills only)}"
  if [[ "${#skills_dirs[@]}" -gt 0 ]]; then
    install_skills "${skills_dirs[@]}"
  fi
  if [[ -n "$codex_skills_dir" ]]; then
    install_codex_skills "$shared_skills_dir"
    remove_legacy_codex_skills "$codex_skills_dir"
  fi
  if [[ "${#agents_dirs[@]}" -gt 0 ]]; then
    install_tree "$REPO/agents" "${agents_dirs[@]}"
    install_tree "$REPO/commands" "${commands_dirs[@]}"
  fi
  if [[ "$UNINSTALL" -ne 1 ]]; then
    if [[ "${#skills_dirs[@]}" -gt 0 ]]; then
      prune_stale "${skills_dirs[@]}"
    fi
    if [[ -n "$codex_skills_dir" ]]; then
      prune_codex_copies "$shared_skills_dir"
    fi
    if [[ "${#agents_dirs[@]}" -gt 0 ]]; then
      prune_stale "${agents_dirs[@]}" "${commands_dirs[@]}"
    fi
  fi
}

cmd_setup() {
  if [[ ! -d "$REPO/skills" ]]; then
    echo "missing $REPO/skills" >&2
    exit 1
  fi
  echo "repo    $REPO"
  echo
  check_symlinks
  migrate_legacy
  config_set_repo "$REPO"
  ensure_bulma_home
  install_for_hosts
  ensure_bin
  ensure_path_snippet
  ensure_agent_browser
  hint_jev
  echo
  echo "done. restart the agent session"
  echo "  Codex: \$bulma-developer or /skills"
  echo "  Claude/Grok: /developer or /bulma-developer"
  echo "  export PATH=\"$BIN_DIR:\$PATH\""
}

cmd_update() {
  local repo
  repo="$(config_get repo)"
  repo="${repo:-$REPO}"
  if ! git -C "$repo" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "not a git clone: $repo" >&2
    echo "  bulma setup" >&2
    exit 1
  fi
  REPO="$repo"
  SELF="$repo/install.sh"
  if [[ -n "$(git -C "$repo" status --porcelain)" ]]; then
    echo "working tree is dirty. commit or stash, then bulma update" >&2
    git -C "$repo" status -sb >&2
    exit 1
  fi
  local old new oldv newv
  old="$(git -C "$repo" rev-parse --short HEAD)"
  oldv="$(plugin_version)"
  if [[ "$DRY" -eq 1 ]]; then
    echo "dry-run: git -C $repo fetch origin"
    echo "dry-run: git -C $repo pull --ff-only origin main"
    echo "version: $oldv $old -> (dry-run)"
    return 0
  fi
  git -C "$repo" fetch origin
  if ! git -C "$repo" pull --ff-only origin main; then
    echo "clone diverged from main. bulma status" >&2
    exit 1
  fi
  new="$(git -C "$repo" rev-parse --short HEAD)"
  newv="$(plugin_version)"
  echo "version: $oldv $old -> $newv $new"
  echo "sha: $old -> $new"
  exec "$SELF" setup
}

# Porcelain records: path, HEAD, branch. First is the main checkout.
# Later paths are extra. This prints them; it never deletes a worktree.
# A trailing blank line is the record separator, including after the last one.
status_worktrees() {
  echo "worktrees"
  local path="" sha="" branch="detached" extra="" line
  while IFS= read -r line; do
    case "$line" in
      worktree\ *)
        path="${line#worktree }"
        sha=""
        branch="detached"
        ;;
      HEAD\ *)
        sha="${line#HEAD }"
        sha="${sha:0:7}"
        ;;
      branch\ *)
        branch="${line#branch }"
        branch="${branch#refs/heads/}"
        ;;
      "")
        [[ -z "$path" ]] && continue
        echo "  $path  $branch  $sha$extra"
        extra="  extra"
        path=""
        ;;
    esac
  done < <(git -C "$1" worktree list --porcelain 2>/dev/null || true; echo)
}

# Product-repo job, if cwd has STATE. Plugin health is the block above.
status_job() {
  local top home slug root state walk
  top="$(git rev-parse --show-toplevel 2>/dev/null)" || return 0
  home="${BULMA_HOME:-$HOME/.bulma}"
  slug="$(printf '%s' "$top" | sed 's|^/||; s|/|-|g')"
  root="$home/$slug"
  state="$root/.bulma-feature-delivery/STATE.md"
  walk="$REPO/skills/bulma-feature-delivery/scripts/status-walk.sh"
  if [[ -f "$state" && -f "$walk" ]]; then
    echo "cwd      $top"
    bash "$walk" "$state"
  elif [[ -f "$root/.bulma-developer/STATE.md" ]]; then
    echo "cwd      $top"
    echo "job      developer (no fd STATE)"
  fi
}

cmd_status() {
  local repo sha behind dest
  repo="$(config_get repo)"
  repo="${repo:-$REPO}"
  REPO="$repo"
  echo "repo     $repo"
  echo "version  $(plugin_version)"
  if git -C "$repo" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    sha="$(git -C "$repo" rev-parse --short HEAD)"
    echo "sha      $sha"
    git -C "$repo" fetch origin >/dev/null 2>&1 || true
    behind="$(git -C "$repo" rev-list --count HEAD..origin/main 2>/dev/null || echo "?")"
    echo "behind   $behind"
    status_worktrees "$repo"
  fi
  status_job
  if command -v bulma >/dev/null 2>&1; then
    echo "path     $(command -v bulma)"
  else
    echo "path     bulma not on PATH (export PATH=\"$BIN_DIR:\$PATH\")"
  fi
  if command -v agent-browser >/dev/null 2>&1; then
    echo "browser  $(command -v agent-browser)"
  else
    echo "browser  agent-browser missing (bulma setup)"
  fi
  if [[ -n "${TYPESAFE_API_KEY:-}" ]]; then
    echo "jev      ok (TYPESAFE_API_KEY set; /bulma available)"
  else
    echo "jev      missing (optional; /bulma needs TYPESAFE_API_KEY)"
  fi
  for dest in \
    "$HOME/.agents/skills/unslop" \
    "$HOME/.grok/skills/unslop" \
    "$HOME/.claude/skills/unslop" \
    "$HOME/.cursor/skills/unslop"
  do
    if [[ -L "$dest" ]]; then
      if is_ours "$dest"; then
        echo "ok       $dest"
      else
        echo "not ours $dest"
      fi
    elif codex_copy_is_ours "$dest"; then
      echo "ok       $dest"
    elif [[ -e "$dest" ]]; then
      echo "not ours $dest"
    else
      echo "missing  $dest"
    fi
  done
  if command -v grok >/dev/null 2>&1 && grok plugin list 2>/dev/null | grep -qi bulma; then
    echo "warn     grok plugin bulma is also installed (duplicate skills)"
  fi
  if command -v claude >/dev/null 2>&1 && claude plugins list 2>/dev/null | grep -qi bulma; then
    echo "warn     claude plugin bulma is also installed (duplicate skills)"
  fi
}

# ISO 8601 UTC to epoch seconds. GNU date and BSD date disagree on the flag,
# so try both rather than depend on either.
iso_epoch() {
  local iso="$1"
  date -u -d "$iso" +%s 2>/dev/null && return 0
  date -u -j -f "%Y-%m-%dT%H:%M:%SZ" "$iso" +%s 2>/dev/null && return 0
  return 1
}

hms() {
  local total="$1"
  printf '%dm%02ds' "$((total / 60))" "$((total % 60))"
}

# Where a stuck QA slot shows up. The graphs treat a claim past the lease as
# free, but a human wants to see that it happened.
report_lease() {
  local jobs="$1"
  local active claimed now age cap=90
  active="$(sed -n 's/^qa_active: *"\{0,1\}\([^"]*\)"\{0,1\} *$/\1/p' "$jobs" | head -1)"
  [[ -n "$active" ]] || return 0
  claimed="$(sed -n 's/^qa_claimed_at: *"\{0,1\}\([^"]*\)"\{0,1\} *$/\1/p' "$jobs" | head -1)"
  if [[ -z "$claimed" ]]; then
    echo "  QA lease: $active holds the slot with no qa_claimed_at - age unknown"
    return 0
  fi
  now="$(date -u +%s)"
  if ! claimed="$(iso_epoch "$claimed")"; then
    echo "  QA lease: $active claimed at an unparseable time"
    return 0
  fi
  age=$(((now - claimed) / 60))
  if ((age > cap)); then
    echo "  QA lease: $active held ${age}m, cap ${cap}m - dead claim, the queue is stuck"
  else
    echo "  QA lease: $active held ${age}m of ${cap}m"
  fi
}

report_ledger() {
  local ledger="$1"
  awk -F'\t' '
    NR == 1 && $1 == "ts_iso" { next }
    NF < 5 { next }
    {
      key = $3 "/" $4
      if ($5 == "enter") { open[key] = $2; if (!($4 in seen) || $6 + 0 > laps[key]) laps[key] = $6 + 0 }
      else if ($5 == "exit" && key in open) {
        span = $2 - open[key]
        total[key] += span
        if (span > longest[key]) longest[key] = span
        runs[key]++
        delete open[key]
      }
    }
    END {
      for (key in total) printf "%s\t%d\t%d\t%d\n", key, runs[key], total[key], longest[key]
    }
  ' "$ledger" | sort -t"$(printf '\t')" -k3 -rn | while IFS="$(printf '\t')" read -r key runs total longest; do
    local flag=""
    ((runs > 1)) && flag="   <- $runs laps"
    printf '  %-34s %3s  %8s  %8s%s\n' \
      "$key" "$runs" "$(hms "$total")" "$(hms "$longest")" "$flag"
  done
}

# Host transcript (Grok unified.jsonl). Graphs never write token counts;
# this is the only honest source. Missing python3 or missing log: skip.
report_tokens() {
  command -v python3 >/dev/null 2>&1 || return 0
  local log="${HOME}/.grok/logs/unified.jsonl"
  local sessions="${HOME}/.grok/sessions"
  [[ -f "$log" ]] || return 0
  python3 - "$log" "$sessions" <<'PY' || true
import collections
import json
import re
import sys
import urllib.parse
from pathlib import Path

log_path, sess_root = sys.argv[1], sys.argv[2]
sid_ws = {}
root = Path(sess_root)
if root.is_dir():
    for folder in root.iterdir():
        if not folder.is_dir():
            continue
        ws = urllib.parse.unquote(folder.name)
        for child in folder.iterdir():
            if child.is_dir():
                sid_ws[child.name] = ws


def classify(ws):
    w = (ws or "").lower()
    if "lstm" in w:
        return "lstm"
    if "review" in w or "rev-pr-" in w:
        return "reviewer"
    if "featuredev" in w or "feature-dev" in w:
        return "fd"
    if re.search(r"/dev-\d+", w):
        return "fd"
    return "other"


def fmt(n):
    n = int(n)
    sign = "-" if n < 0 else ""
    n = abs(n)
    if n >= 1_000_000:
        return f"{sign}{n / 1_000_000:.1f}M"
    if n >= 10_000:
        return f"{sign}{n / 1000:.0f}k"
    if n >= 1000:
        return f"{sign}{n / 1000:.1f}k"
    return f"{sign}{n}"


by = collections.defaultdict(
    lambda: {"prompt": 0, "cached": 0, "n": 0, "sids": set(), "uncached": 0}
)
total = {"prompt": 0, "cached": 0, "n": 0, "uncached": 0}
days = set()

with open(log_path, encoding="utf-8", errors="replace") as handle:
    for line in handle:
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if rec.get("msg") != "shell.turn.inference_done":
            continue
        ctx = rec.get("ctx") or {}
        sid = rec.get("sid") or "nosid"
        prompt = int(ctx.get("prompt_tokens") or 0)
        cached = int(ctx.get("cached_prompt_tokens") or 0)
        uncached = max(prompt - cached, 0)
        ts = (rec.get("ts") or "")[:10]
        if ts:
            days.add(ts)
        bucket = by[classify(sid_ws.get(sid, ""))]
        bucket["prompt"] += prompt
        bucket["cached"] += cached
        bucket["n"] += 1
        bucket["sids"].add(sid)
        bucket["uncached"] += uncached
        total["prompt"] += prompt
        total["cached"] += cached
        total["n"] += 1
        total["uncached"] += uncached

if total["n"] == 0:
    raise SystemExit(0)

window = ",".join(sorted(days)) if days else "unknown"
cache_pct = 100 * total["cached"] / total["prompt"] if total["prompt"] else 0
print("tokens (host transcript)")
print(
    f"  window {window}   calls {total['n']}   "
    f"prompt {fmt(total['prompt'])}   uncached {fmt(total['uncached'])}   "
    f"cache {cache_pct:.0f}%"
)
print(f"  {'class':12} {'sids':>4} {'calls':>5} {'prompt':>8} {'uncached':>8} {'cache':>5}")
for cls, bucket in sorted(by.items(), key=lambda item: -item[1]["uncached"]):
    pct = 100 * bucket["cached"] / bucket["prompt"] if bucket["prompt"] else 0
    print(
        f"  {cls:12} {len(bucket['sids']):4d} {bucket['n']:5d} "
        f"{fmt(bucket['prompt']):>8} {fmt(bucket['uncached']):>8} {pct:4.0f}%"
    )
print("  uncached = prompt tokens that missed the prefix cache. Not written by the graphs.")
PY
}

# Read-only. Aggregates what the graphs already append to the run ledger, so
# a bottleneck is a number instead of a hunch. Token totals come from the
# host transcript when present, never from the ledger.
cmd_report() {
  local home="${BULMA_HOME:-$HOME/.bulma}"
  local found=0 dir slug ledger jobs body tokens
  if [[ -d "$home" ]]; then
    for dir in "$home"/*; do
      [[ -d "$dir" ]] || continue
      slug="$(basename "$dir")"
      ledger="$dir/.bulma-bus/RUN_LOG.tsv"
      jobs="$dir/.bulma-bus/JOBS.md"
      # A repo keeps its bus dir long after the last run. Build the body first
      # and print the heading only if there is something under it, or every
      # repo you ever touched shows up as an empty section.
      body=""
      if [[ -f "$ledger" ]]; then
        body="$(report_ledger "$ledger")"
        [[ -n "$body" ]] && body="$(printf '  %-34s %3s  %8s  %8s\n%s' \
          "graph/node" "run" "total" "longest" "$body")"
      fi
      if [[ -f "$jobs" ]]; then
        local lease
        lease="$(report_lease "$jobs")"
        [[ -n "$lease" ]] && body="${body:+$body$'\n'}$lease"
      fi
      [[ -n "$body" ]] || continue
      found=1
      echo "repo $slug"
      echo "$body"
      echo
    done
  fi
  tokens="$(report_tokens)"
  if [[ -n "$tokens" ]]; then
    found=1
    echo "$tokens"
  fi
  if [[ "$found" -eq 0 ]]; then
    echo "no runs recorded under $home"
    echo "The graphs append to .bulma-bus/RUN_LOG.tsv as they walk. Run one."
  fi
}

cmd_uninstall() {
  UNINSTALL=1
  install_for_hosts
  if [[ -L "$BIN_LINK" ]]; then
    local t
    t="$(readlink "$BIN_LINK")"
    if [[ "$t" == "$SELF" || "$t" == "$REPO/install.sh" ]]; then
      echo "rm     $BIN_LINK"
      run rm "$BIN_LINK"
    fi
  fi
  echo "unlinked this repo from local agent homes."
  if [[ "$PURGE" -ne 1 ]]; then
    return 0
  fi
  local repo
  repo="$(config_get repo)"
  if [[ "$repo" != "$MANAGED_REPO" ]]; then
    echo "this is your development clone: $repo" >&2
    echo "refusing --purge" >&2
    exit 1
  fi
  if [[ "$YES" -ne 1 ]]; then
    if [[ ! -t 0 ]]; then
      echo "--yes is required to --purge when stdin is not a TTY" >&2
      exit 1
    fi
    printf 'Delete %s ? [y/N] ' "$MANAGED_REPO"
    read -r ans
    case "$ans" in y|Y|yes) ;; *) echo "aborted."; return 0 ;; esac
  fi
  echo "rm     $MANAGED_REPO"
  run rm -rf "$MANAGED_REPO"
  echo "rm     $CONFIG_FILE"
  run rm -f "$CONFIG_FILE"
}

print_banner() {
  echo
  echo "  BULMA"
  echo "  Agent graphs. Flattened into your homes."
  echo
}

print_home() {
  print_banner
  printf '  $ bulma setup      Flatten skills into agent homes\n'
  printf '  $ bulma update     git pull --ff-only main\n'
  printf '  $ bulma status     Repo, version, homes, worktrees, cwd job Walk\n'
  printf '  $ bulma uninstall  Remove our symlinks\n'
  echo
  echo "  try: bulma setup"
  echo
}

is_bootstrap() {
  [[ -f "$REPO/plugin.json" && -d "$REPO/skills" ]] && return 1
  return 0
}

# The whole install is symlinks: bulma update pulls the clone and every agent
# home follows through the link. On Windows Git Bash without Developer Mode or
# MSYS=winsymlinks:nativestrict, ln -s silently copies instead, so updates stop
# propagating and nothing tells you. Test the capability rather than guessing
# from the OS name.
symlinks_work() {
  if [[ "${BULMA_FORCE_NO_SYMLINK:-0}" = "1" ]]; then
    return 1
  fi
  local probe target
  probe="$(mktemp -d "${TMPDIR:-/tmp}/bulma-symprobe.XXXXXX")" || return 1
  target="$probe/target"
  : >"$target"
  if ln -s "$target" "$probe/link" 2>/dev/null && [[ -L "$probe/link" ]]; then
    rm -rf "$probe"
    return 0
  fi
  rm -rf "$probe"
  return 1
}

check_symlinks() {
  if symlinks_work; then
    if [[ -n "${MSYSTEM:-}" ]] || case "${OSTYPE:-}" in msys*|cygwin*) true ;; *) false ;; esac; then
      echo "note   Git Bash detected. Symlinks work here, but they break without"
      echo "       Developer Mode. WSL is the supported path on Windows."
    fi
    return 0
  fi
  echo "error  this filesystem cannot create symlinks." >&2
  echo "       bulma installs by symlinking skills into your agent homes, and" >&2
  echo "       bulma update relies on those links to pick up new commits." >&2
  echo "       On Windows: use WSL, or enable Developer Mode and set" >&2
  echo "       MSYS=winsymlinks:nativestrict in Git Bash." >&2
  exit 1
}

need_bin() {
  command -v "$1" >/dev/null 2>&1 && return 0
  echo "missing $1" >&2
  echo "  curl -fsSL https://raw.githubusercontent.com/ruverd/bulma/main/install.sh | bash" >&2
  exit 1
}

cmd_bootstrap() {
  need_bin git
  need_bin curl
  local repo
  repo="$(config_get repo)"
  if [[ -n "$repo" && -f "$repo/plugin.json" ]] && grep -q '"name": "bulma"' "$repo/plugin.json"; then
    exec "$repo/install.sh" update --yes
  fi
  run mkdir -p "$(dirname "$MANAGED_REPO")"
  if ! git -C "$MANAGED_REPO" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    git clone --branch main "$DEFAULT_ORIGIN" "$MANAGED_REPO"
  fi
  config_set_repo "$MANAGED_REPO" "$DEFAULT_ORIGIN"
  exec "$MANAGED_REPO/install.sh" setup --yes
}

cmd_menu() {
  if [[ ! -t 0 || ! -t 1 ]]; then
    print_home
    return 0
  fi
  print_banner
  echo "  ↑/↓ navigate · enter run · q quit"
  echo
  local labels="setup update status uninstall"
  local descs="Flatten skills into agent homes|git pull --ff-only main|Repo, version, homes|Remove our symlinks"
  local n=4 sel=1
  local i label desc key rest
  # Saved globally so the INT trap can restore cooked mode after Ctrl-C.
  _BULMA_STTY="$(stty -g 2>/dev/null || true)"
  restore() {
    if [[ -n "${_BULMA_STTY:-}" ]]; then
      stty "$_BULMA_STTY" 2>/dev/null || true
    else
      stty echo 2>/dev/null || true
    fi
    printf '\033[?25h'
    trap - INT TERM
    unset _BULMA_STTY
  }
  trap 'restore; exit 130' INT TERM
  printf '\033[?25l'
  stty -echo
  draw() {
    i=1
    while [[ $i -le $n ]]; do
      label="$(echo "$labels" | awk -v n="$i" '{print $n}')"
      desc="$(echo "$descs" | awk -F'|' -v n="$i" '{print $n}')"
      printf '\033[2K'
      if [[ $i -eq $sel ]]; then
        printf '  > %-12s  %s\n' "$label" "$desc"
      else
        printf '    %-12s  %s\n' "$label" "$desc"
      fi
      i=$((i + 1))
    done
  }
  draw
  while true; do
    IFS= read -r -n 1 key || true
    if [[ "$key" == $'\x03' ]]; then
      restore
      echo
      echo "  Cancelled."
      exit 130
    fi
    if [[ "$key" == "q" ]]; then
      restore
      echo
      echo "  Cancelled."
      return 0
    fi
    if [[ "$key" == "" ]]; then
      restore
      label="$(echo "$labels" | awk -v n="$sel" '{print $n}')"
      echo
      CMD="$label"
      case "$CMD" in
        setup) cmd_setup ;;
        update) cmd_update ;;
        status) cmd_status ;;
        uninstall) cmd_uninstall ;;
      esac
      return 0
    fi
    if [[ "$key" == $'\x1b' ]]; then
      read -r -n 2 rest || true
      key="$key$rest"
    fi
    case "$key" in
      $'\x1b[A'|k) sel=$((sel - 1)); [[ $sel -lt 1 ]] && sel=$n ;;
      $'\x1b[B'|j) sel=$((sel + 1)); [[ $sel -gt $n ]] && sel=1 ;;
    esac
    printf '\033[%sA' "$n"
    draw
  done
}

main() {
  if [[ "$CMD" == "version" ]]; then
    if [[ -f "$REPO/plugin.json" ]]; then
      echo "bulma $(plugin_version)"
    else
      echo "bulma (no checkout here; run: bulma status)" >&2
      exit 1
    fi
    return
  fi
  if is_bootstrap; then
    cmd_bootstrap
    return
  fi
  case "${CMD}" in
    ""|menu) cmd_menu ;;
    setup) cmd_setup ;;
    update) cmd_update ;;
    status) cmd_status ;;
    report) cmd_report ;;
    uninstall) cmd_uninstall ;;
    help) usage ;;
    version) echo "bulma $(plugin_version)" ;;
    *) usage; exit 1 ;;
  esac
}

ts() { date +%Y%m%d%H%M%S; }

is_ours() {
  local dest="$1"
  [[ -L "$dest" ]] || return 1
  local target
  target="$(readlink "$dest")"
  [[ "$target" == "$REPO/"* ]]
}

run() {
  if [[ "$DRY" -eq 1 ]]; then
    echo "dry-run: $*"
    return 0
  fi
  "$@"
}

link_one() {
  local src="$1"
  local dest="$2"
  run mkdir -p "$(dirname "$dest")"
  if [[ -L "$dest" ]]; then
    local cur
    cur="$(readlink "$dest")"
    if [[ "$cur" == "$src" ]]; then
      echo "ok     $dest"
      return 0
    fi
    echo "relink $dest"
    run ln -sfn "$src" "$dest"
    return 0
  fi
  if [[ -e "$dest" ]]; then
    local bak_dir bak
    bak_dir="$BACKUP_ROOT/$(ts)"
    bak="$bak_dir/$(basename "$dest")"
    echo "backup $dest -> $bak"
    run mkdir -p "$bak_dir"
    run mv "$dest" "$bak"
  fi
  echo "link   $dest -> $src"
  run ln -sfn "$src" "$dest"
}

CODEX_COPY_MARKER=".bulma-installed-copy"

codex_copy_is_ours() {
  local dest="$1"
  [[ -f "$dest/$CODEX_COPY_MARKER" ]] || return 1
  grep -qx 'managed-by=bulma' "$dest/$CODEX_COPY_MARKER"
}

copy_codex_skill() {
  local src="$1"
  local dest="$2"
  local tmp="${dest}.bulma-tmp-$$"
  run mkdir -p "$(dirname "$dest")"

  if [[ -L "$dest" ]] && is_ours "$dest"; then
    echo "replace $dest symlink with Codex copy"
    run rm "$dest"
  elif codex_copy_is_ours "$dest"; then
    echo "update  $dest"
    run rm -rf "$dest"
  elif [[ -e "$dest" || -L "$dest" ]]; then
    local bak_dir bak
    bak_dir="$BACKUP_ROOT/$(ts)"
    bak="$bak_dir/$(basename "$dest")"
    echo "backup $dest -> $bak"
    run mkdir -p "$bak_dir"
    run mv "$dest" "$bak"
  else
    echo "copy   $dest <- $src"
  fi

  if [[ "$DRY" -eq 1 ]]; then
    echo "dry-run: copy $src to $dest"
    return 0
  fi
  rm -rf "$tmp"
  cp -R "$src" "$tmp"
  printf 'managed-by=bulma\n' >"$tmp/$CODEX_COPY_MARKER"
  mv "$tmp" "$dest"
}

remove_codex_skill() {
  local dest="$1"
  if [[ -L "$dest" ]]; then
    unlink_one "$dest"
  elif codex_copy_is_ours "$dest"; then
    echo "rm     $dest"
    run rm -rf "$dest"
  elif [[ -e "$dest" ]]; then
    echo "keep   $dest (not a Bulma-managed Codex copy)"
  fi
}

remove_legacy_codex_skills() {
  local dest_dir="$1"
  local src name
  for src in "$REPO/skills"/*; do
    [[ -d "$src" ]] || continue
    [[ -f "$src/SKILL.md" ]] || continue
    name="$(basename "$src")"
    remove_codex_skill "$dest_dir/$name"
  done
}

prune_codex_copies() {
  local dest_dir="$1"
  local dest name
  [[ -d "$dest_dir" ]] || return 0
  for dest in "$dest_dir"/*; do
    [[ -d "$dest" ]] || continue
    codex_copy_is_ours "$dest" || continue
    name="$(basename "$dest")"
    [[ -f "$REPO/skills/$name/SKILL.md" ]] && continue
    echo "prune  $dest"
    run rm -rf "$dest"
  done
}

# Drop links we own whose target no longer exists. Without this, renaming or
# deleting a skill or command leaves a dead entry in every agent home forever,
# and the host still offers it in the picker.
prune_stale() {
  local dest_dir dest
  for dest_dir in "$@"; do
    [[ -d "$dest_dir" ]] || continue
    for dest in "$dest_dir"/*; do
      [[ -L "$dest" ]] || continue
      is_ours "$dest" || continue
      [[ -e "$dest" ]] && continue
      echo "prune  $dest"
      run rm "$dest"
    done
  done
}

unlink_one() {
  local dest="$1"
  if is_ours "$dest"; then
    echo "rm     $dest"
    run rm "$dest"
  elif [[ -e "$dest" ]]; then
    echo "keep   $dest (not a symlink to this repo)"
  fi
}

# Flat kinds (agents, commands): dest gets the same basename.
install_tree() {
  local src_dir="$1"
  shift
  local dest_dirs=("$@")
  [[ -d "$src_dir" ]] || return 0
  local src dest dest_dir name
  for src in "$src_dir"/*; do
    [[ -e "$src" ]] || continue
    name="$(basename "$src")"
    for dest_dir in "${dest_dirs[@]}"; do
      dest="$dest_dir/$name"
      if [[ "$UNINSTALL" -eq 1 ]]; then
        unlink_one "$dest"
      else
        link_one "$src" "$dest"
      fi
    done
  done
}

# skills/<name> → dest/<name>. The layout in git already matches the layout
# after install, which is why a link like ../other-skill/FILE.md resolves the
# same in both places.
install_skills() {
  local dest_dirs=("$@")
  local src dest dest_dir name
  for src in "$REPO/skills"/*; do
    [[ -d "$src" ]] || continue
    [[ -f "$src/SKILL.md" ]] || continue
    name="$(basename "$src")"
    for dest_dir in "${dest_dirs[@]}"; do
      dest="$dest_dir/$name"
      if [[ "$UNINSTALL" -eq 1 ]]; then
        unlink_one "$dest"
      else
        link_one "$src" "$dest"
      fi
    done
  done
}

# Codex canonicalizes symlink targets and namespaces any skill below a plugin
# manifest (`bulma:bulma-developer`). Managed copies in the shared skill home
# keep standalone ids such as `$bulma-developer` without duplicate discovery.
install_codex_skills() {
  local dest_dir="$1"
  local src dest name
  for src in "$REPO/skills"/*; do
    [[ -d "$src" ]] || continue
    [[ -f "$src/SKILL.md" ]] || continue
    name="$(basename "$src")"
    dest="$dest_dir/$name"
    if [[ "$UNINSTALL" -eq 1 ]]; then
      remove_codex_skill "$dest"
    else
      copy_codex_skill "$src" "$dest"
    fi
  done
}

if [[ ! -d "$REPO/skills" && "$CMD" != "" && "$CMD" != "help" \
   && "$CMD" != "version" && "$CMD" != "report" ]]; then
  echo "missing $REPO/skills" >&2
  exit 1
fi

main
