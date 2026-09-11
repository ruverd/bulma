#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
INSTALL="$ROOT/install.sh"
export RUVER_SKIP_DEPS=1

fail() { echo "FAIL: $*" >&2; exit 1; }
ok() { echo "ok  $*"; }

assert_eq() {
  local got="$1" want="$2" msg="$3"
  [[ "$got" == "$want" ]] || fail "$msg (got '$got' want '$want')"
}

assert_file() { [[ -e "$1" ]] || fail "missing $1"; }
assert_link() { [[ -L "$1" ]] || fail "not a symlink: $1"; }
assert_dir() { [[ -d "$1" ]] || fail "not a directory: $1"; }
assert_not() { [[ ! -e "$1" ]] || fail "should not exist: $1"; }
# -e follows symlinks, so a dangling link satisfies assert_not. This one does not.
assert_gone() { [[ ! -e "$1" && ! -L "$1" ]] || fail "should be gone: $1"; }

run_install() {
  HOME="$TEST_HOME" XDG_CONFIG_HOME="$TEST_HOME/.config" \
    XDG_DATA_HOME="$TEST_HOME/.local/share" \
    RUVER_SKIP_DEPS=1 \
    "$INSTALL" "$@"
}

# --- help ---
out="$(HOME=/tmp "$INSTALL" --help)"
echo "$out" | grep -q 'Examples:' || fail "help missing Examples:"
echo "$out" | grep -q 'ruver setup' || fail "help missing ruver setup"
echo "$out" | grep -q 'curl -fsSL' || fail "help missing curl one-liner"
ok help

# --- version ---
want="$(sed -n 's/.*"version": "\([^"]*\)".*/\1/p' "$ROOT/plugin.json" | head -1)"
[[ -n "$want" ]] || fail "could not read version from plugin.json"
for flag in --version -V; do
  set +e
  out="$(HOME=/tmp "$INSTALL" "$flag" 2>&1)"
  got=$?
  set -e
  assert_eq "$got" "0" "$flag exit"
  assert_eq "$out" "ruver $want" "$flag output"
done
ok version

set +e
HOME=/tmp "$INSTALL" not-a-command >/dev/null 2>&1
got=$?
set -e
assert_eq "$got" "1" "unknown command exit"
ok unknown-command

TEST_HOME="$(mktemp -d "${TMPDIR:-/tmp}/ruver-cli.XXXXXX")"
trap 'rm -rf "$TEST_HOME"' EXIT

run_install setup >/tmp/ruver-setup.out
assert_file "$TEST_HOME/.config/ruver/config"
grep -qx "repo=$ROOT" "$TEST_HOME/.config/ruver/config" || fail "repo= should be $ROOT"
assert_link "$TEST_HOME/.agents/skills/unslop"
assert_link "$TEST_HOME/.local/bin/ruver"
readlink "$TEST_HOME/.local/bin/ruver" | grep -q 'install.sh' || fail "bin not install.sh"
assert_file "$TEST_HOME/.ruver"
assert_not "$TEST_HOME/.ruver/memory.md"
grep -q 'agent-browser' /tmp/ruver-setup.out || fail "setup should mention agent-browser"
ok setup

# PATH snippet once. TEST_HOME/.local/bin is not on PATH, so setup must write the block.
case ":$PATH:" in
  *":$TEST_HOME/.local/bin:"*) fail "test assumption: $TEST_HOME/.local/bin must not be on PATH" ;;
esac
grep -q '# ruver PATH' "$TEST_HOME/.zshrc" || fail "missing zshrc PATH block"
run_install setup >/dev/null
count="$(grep -c '# ruver PATH' "$TEST_HOME/.zshrc" || true)"
assert_eq "$count" "1" "PATH block duplicated"
ok setup-path-once

# PATH snippet skipped when BIN_DIR is already on PATH
SKIP_HOME="$(mktemp -d "${TMPDIR:-/tmp}/ruver-cli.XXXXXX")"
trap 'rm -rf "$TEST_HOME" "$SKIP_HOME"' EXIT
PATH="$SKIP_HOME/.local/bin:$PATH" \
  HOME="$SKIP_HOME" XDG_CONFIG_HOME="$SKIP_HOME/.config" \
  XDG_DATA_HOME="$SKIP_HOME/.local/share" \
  "$INSTALL" setup >/dev/null
if [[ -f "$SKIP_HOME/.zshrc" ]] && grep -q '# ruver PATH' "$SKIP_HOME/.zshrc"; then
  fail "PATH block should not be written when BIN_DIR is already on PATH"
fi
ok setup-path-skip-when-present

# --- rc files: opt out, and say so when opting in ---
NP_HOME="$(mktemp -d "${TMPDIR:-/tmp}/ruver-nopath.XXXXXX")"
set +e
out="$(HOME="$NP_HOME" XDG_CONFIG_HOME="$NP_HOME/.config" \
  XDG_DATA_HOME="$NP_HOME/.local/share" "$INSTALL" setup --no-path 2>&1)"
got=$?
set -e
assert_eq "$got" "0" "setup --no-path exit"
if [[ -f "$NP_HOME/.zshrc" ]] && grep -q '# ruver PATH' "$NP_HOME/.zshrc"; then
  fail "--no-path must not write a PATH block"
fi
grep -q 'export PATH' <<< "$out" || fail "--no-path should still print the export line"
ok setup-no-path

AN_HOME="$(mktemp -d "${TMPDIR:-/tmp}/ruver-announce.XXXXXX")"
out="$(HOME="$AN_HOME" XDG_CONFIG_HOME="$AN_HOME/.config" \
  XDG_DATA_HOME="$AN_HOME/.local/share" "$INSTALL" setup 2>&1)"
grep -q "$AN_HOME/.zshrc" <<< "$out" || fail "setup must name the rc file it edits"
grep -q '# ruver PATH' "$AN_HOME/.zshrc" || fail "default setup should write the PATH block"
ok setup-announces-rc-edit

# --- Windows: symlinks are the whole design, so prove we notice when they fail ---
WIN_HOME="$(mktemp -d "${TMPDIR:-/tmp}/ruver-win.XXXXXX")"
set +e
out="$(MSYSTEM=MINGW64 HOME="$WIN_HOME" XDG_CONFIG_HOME="$WIN_HOME/.config" \
  XDG_DATA_HOME="$WIN_HOME/.local/share" "$INSTALL" setup 2>&1)"
got=$?
set -e
assert_eq "$got" "0" "Git Bash with working symlinks should still install"
grep -qi 'symlink' <<< "$out" || fail "Git Bash run should mention symlinks"
grep -qi 'wsl' <<< "$out" || fail "Git Bash run should point at WSL"
ok setup-warns-on-git-bash

NOSYM_HOME="$(mktemp -d "${TMPDIR:-/tmp}/ruver-nosym.XXXXXX")"
set +e
out="$(RUVER_FORCE_NO_SYMLINK=1 HOME="$NOSYM_HOME" \
  XDG_CONFIG_HOME="$NOSYM_HOME/.config" \
  XDG_DATA_HOME="$NOSYM_HOME/.local/share" "$INSTALL" setup 2>&1)"
got=$?
set -e
assert_eq "$got" "1" "setup must refuse when symlinks do not work"
grep -qi 'symlink' <<< "$out" || fail "refusal should explain symlinks"
assert_not "$NOSYM_HOME/.agents/skills/unslop"
ok setup-refuses-without-symlinks

rm -rf "$WIN_HOME" "$NOSYM_HOME"

rm -rf "$NP_HOME" "$AN_HOME"

DRY_HOME="$(mktemp -d "${TMPDIR:-/tmp}/ruver-dry.XXXXXX")"
set +e
out="$(HOME="$DRY_HOME" XDG_CONFIG_HOME="$DRY_HOME/.config" \
  XDG_DATA_HOME="$DRY_HOME/.local/share" \
  "$INSTALL" setup --dry-run 2>&1)"
got=$?
set -e
[[ "$got" -eq 0 ]] || fail "dry-run setup exit $got"
grep -q 'dry-run:' <<< "$out" || fail "dry-run silent"
assert_not "$DRY_HOME/.config/ruver/config"
assert_not "$DRY_HOME/.agents/skills/unslop"
assert_not "$DRY_HOME/.local/bin/ruver"
rm -rf "$DRY_HOME"
ok dry-run-setup

run_install setup >/tmp/ruver-setup2.out
grep -q '^ok ' /tmp/ruver-setup2.out || fail "second setup has no ok lines"
assert_link "$TEST_HOME/.agents/skills/unslop"
ok setup-idempotent

# --- host homes: only the ones that already exist, unless told otherwise ---
SEL_HOME="$(mktemp -d "${TMPDIR:-/tmp}/ruver-sel.XXXXXX")"
mkdir -p "$SEL_HOME/.claude"
HOME="$SEL_HOME" XDG_CONFIG_HOME="$SEL_HOME/.config" \
  XDG_DATA_HOME="$SEL_HOME/.local/share" "$INSTALL" setup >/dev/null
assert_link "$SEL_HOME/.claude/skills/unslop"
assert_link "$SEL_HOME/.agents/skills/unslop"
assert_not "$SEL_HOME/.codex/skills"
assert_not "$SEL_HOME/.cursor/skills"
assert_not "$SEL_HOME/.grok/skills"
ok setup-only-existing-homes

ALL_HOME="$(mktemp -d "${TMPDIR:-/tmp}/ruver-all.XXXXXX")"
HOME="$ALL_HOME" XDG_CONFIG_HOME="$ALL_HOME/.config" \
  XDG_DATA_HOME="$ALL_HOME/.local/share" "$INSTALL" setup --all >/dev/null
for h in claude grok cursor; do
  assert_link "$ALL_HOME/.$h/skills/unslop"
done
assert_not "$ALL_HOME/.codex/skills/unslop"
assert_dir "$ALL_HOME/.agents/skills/unslop"
[[ ! -L "$ALL_HOME/.agents/skills/unslop" ]] \
  || fail "Shared skills must be copies when Codex is installed"
grep -qx 'managed-by=ruver' \
  "$ALL_HOME/.agents/skills/unslop/.ruver-installed-copy" \
  || fail "shared Codex skill copy missing ownership marker"
assert_file "$ALL_HOME/.agents/skills/ruver-developer/SKILL.md"
assert_file "$ALL_HOME/.agents/skills/ruver-fd/SKILL.md"
ok setup-all-hosts

ONE_HOME="$(mktemp -d "${TMPDIR:-/tmp}/ruver-one.XXXXXX")"
HOME="$ONE_HOME" XDG_CONFIG_HOME="$ONE_HOME/.config" \
  XDG_DATA_HOME="$ONE_HOME/.local/share" "$INSTALL" setup --only cursor >/dev/null
assert_link "$ONE_HOME/.cursor/skills/unslop"
assert_not "$ONE_HOME/.claude/skills"
assert_not "$ONE_HOME/.grok/skills"
ok setup-only-flag

set +e
out="$(HOME="$ONE_HOME" "$INSTALL" setup --only nope 2>&1)"
got=$?
set -e
assert_eq "$got" "1" "--only with an unknown host exits 1"
grep -qi 'nope' <<< "$out" || fail "--only error should name the bad host"
ok setup-only-unknown-host

rm -rf "$SEL_HOME" "$ALL_HOME" "$ONE_HOME"

# --- update: dirty abort, then clean fast-forward ---
mini="$(mktemp -d "${TMPDIR:-/tmp}/ruver-mini.XXXXXX")"
mkdir -p "$mini/skills/unslop" "$mini/agents" "$mini/commands"
printf '%s\n' '{"name": "ruver", "version": "0.0.1"}' >"$mini/plugin.json"
echo '# unslop' >"$mini/skills/unslop/SKILL.md"
cp "$INSTALL" "$mini/install.sh"
chmod +x "$mini/install.sh"
git -C "$mini" init -q
git -C "$mini" add .
git -C "$mini" -c user.email=t@t -c user.name=t commit -qm init
git -C "$mini" branch -M main
git -C "$mini" clone --bare "$mini" "${mini}.git"
git -C "$mini" remote add origin "${mini}.git"
git -C "$mini" fetch origin
git -C "$mini" branch --set-upstream-to=origin/main main 2>/dev/null || true

MINI_HOME="$(mktemp -d "${TMPDIR:-/tmp}/ruver-mini-home.XXXXXX")"
trap 'rm -rf "$TEST_HOME" "$SKIP_HOME" "$mini" "${mini}.git" "$MINI_HOME"' EXIT
HOME="$MINI_HOME" XDG_CONFIG_HOME="$MINI_HOME/.config" \
  XDG_DATA_HOME="$MINI_HOME/.local/share" \
  "$mini/install.sh" setup >/dev/null

echo dirty >>"$mini/skills/unslop/SKILL.md"
set +e
HOME="$MINI_HOME" XDG_CONFIG_HOME="$MINI_HOME/.config" \
  XDG_DATA_HOME="$MINI_HOME/.local/share" \
  "$mini/install.sh" update >/tmp/ruver-dirty.out 2>/tmp/ruver-dirty.err
got=$?
set -e
assert_eq "$got" "1" "dirty update should fail"
grep -qi 'stash\|commit' /tmp/ruver-dirty.err /tmp/ruver-dirty.out \
  || fail "dirty update message"
ok update-dirty

git -C "$mini" checkout -q -- skills/unslop/SKILL.md

ahead="$(mktemp -d "${TMPDIR:-/tmp}/ruver-ahead.XXXXXX")"
trap 'rm -rf "$TEST_HOME" "$SKIP_HOME" "$mini" "${mini}.git" "$MINI_HOME" "$ahead"' EXIT
git clone -q "${mini}.git" "$ahead"
# After pull, setup is re-exec'd from the new install.sh so CLI changes take effect.
awk '
  /^cmd_setup\(\) \{/ {
    print
    print "  echo NEW_SETUP_RAN"
    next
  }
  { print }
' "$ahead/install.sh" >"$ahead/install.sh.new"
mv "$ahead/install.sh.new" "$ahead/install.sh"
chmod +x "$ahead/install.sh"
git -C "$ahead" add install.sh
git -C "$ahead" -c user.email=t@t -c user.name=t commit -qm second
git -C "$ahead" push -q origin main

set +e
HOME="$MINI_HOME" XDG_CONFIG_HOME="$MINI_HOME/.config" \
  XDG_DATA_HOME="$MINI_HOME/.local/share" \
  "$mini/install.sh" update >/tmp/ruver-ff.out 2>/tmp/ruver-ff.err
got=$?
set -e
[[ "$got" -eq 0 ]] || fail "clean update exit $got $(cat /tmp/ruver-ff.err)"
grep -q 'version:' /tmp/ruver-ff.out || fail "update missing version:"
ver="$(grep '^version:' /tmp/ruver-ff.out | head -1)"
old_sha="$(grep -oE '[0-9a-f]{7,}' <<< "$ver" | head -1)"
new_sha="$(grep -oE '[0-9a-f]{7,}' <<< "$ver" | tail -1)"
[[ -n "$old_sha" && -n "$new_sha" && "$old_sha" != "$new_sha" ]] \
  || fail "update did not advance SHA ($ver)"
grep -q NEW_SETUP_RAN /tmp/ruver-ff.out \
  || fail "update did not re-exec new install.sh setup"
ok update-clean

# cmd_update must exec the pulled install.sh (DRY=1 returns before this exec).
update_fn="$(sed -n '/^cmd_update()/,/^cmd_status()/p' "$INSTALL")"
echo "$update_fn" | grep -q 'exec ' \
  || fail "cmd_update must exec setup after pull"
ok update-exec-setup

# Linked worktree: .git is a file, so [[ -d repo/.git ]] is the wrong check.
mini_wt="${mini}-wt"
git -C "$mini" worktree add "$mini_wt" -b wt-test >/dev/null
[[ -f "$mini_wt/.git" ]] || fail "worktree .git should be a file"
[[ ! -d "$mini_wt/.git" ]] || fail "worktree .git should not be a directory"
WT_HOME="$(mktemp -d "${TMPDIR:-/tmp}/ruver-wt-home.XXXXXX")"
trap 'rm -rf "$TEST_HOME" "$SKIP_HOME" "$mini" "${mini}.git" "$MINI_HOME" "$ahead" "$mini_wt" "$WT_HOME"' EXIT

HOME="$WT_HOME" XDG_CONFIG_HOME="$WT_HOME/.config" \
  XDG_DATA_HOME="$WT_HOME/.local/share" \
  "$mini_wt/install.sh" setup >/dev/null

# MINI_HOME repo= is $mini, so this grep cannot pass on the repo line.
# git may canonicalize /var to /private/var, so accept pwd -P too.
HOME="$MINI_HOME" XDG_CONFIG_HOME="$MINI_HOME/.config" \
  XDG_DATA_HOME="$MINI_HOME/.local/share" \
  "$mini/install.sh" status >/tmp/ruver-wt-status.out
wt_real="$(cd "$mini_wt" && pwd -P)"
wt_line="$(grep -F -e "$mini_wt" -e "$wt_real" /tmp/ruver-wt-status.out | head -n 1 || true)"
[[ -n "$wt_line" ]] || fail "status missing extra worktree path $mini_wt"
echo "$wt_line" | grep -q 'wt-test' \
  || fail "status extra worktree line missing branch wt-test ($wt_line)"
echo "$wt_line" | grep -Eq '[0-9a-f]{7}' \
  || fail "status extra worktree line missing 7-char SHA ($wt_line)"
ok status-worktrees

set +e
HOME="$WT_HOME" XDG_CONFIG_HOME="$WT_HOME/.config" \
  XDG_DATA_HOME="$WT_HOME/.local/share" \
  "$mini_wt/install.sh" update >/tmp/ruver-wt.out 2>/tmp/ruver-wt.err
got=$?
set -e
[[ "$got" -eq 0 ]] || fail "worktree update exit $got $(cat /tmp/ruver-wt.err)"
if grep -qi 'not a git clone' /tmp/ruver-wt.err /tmp/ruver-wt.out; then
  fail "worktree treated as not a git clone"
fi
ok update-worktree

# --- a deleted skill or command must not leave a dead link behind ---
PR_HOME="$(mktemp -d "${TMPDIR:-/tmp}/ruver-prune.XXXXXX")"
mkdir -p "$mini/skills/gone" "$mini/commands"
echo '# gone' >"$mini/skills/gone/SKILL.md"
printf -- '---\ndescription: gone\n---\n' >"$mini/commands/gone.md"
HOME="$PR_HOME" XDG_CONFIG_HOME="$PR_HOME/.config" \
  XDG_DATA_HOME="$PR_HOME/.local/share" "$mini/install.sh" setup --all >/dev/null
assert_dir "$PR_HOME/.agents/skills/gone"
assert_link "$PR_HOME/.claude/commands/gone.md"
assert_not "$PR_HOME/.codex/skills/gone"
rm -rf "$mini/skills/gone" "$mini/commands/gone.md"
HOME="$PR_HOME" XDG_CONFIG_HOME="$PR_HOME/.config" \
  XDG_DATA_HOME="$PR_HOME/.local/share" "$mini/install.sh" setup --all >/dev/null
assert_gone "$PR_HOME/.agents/skills/gone"
assert_gone "$PR_HOME/.claude/commands/gone.md"
assert_dir "$PR_HOME/.agents/skills/unslop"
ok setup-prunes-removed-links

rm -rf "$PR_HOME"

mkdir -p "$TEST_HOME/.ruver"
echo '# Memory' >"$TEST_HOME/.ruver/memory.md"
mkdir -p "$TEST_HOME/.agents/skills"
echo mine >"$TEST_HOME/.agents/skills/foreign-file"
run_install uninstall >/tmp/ruver-un.out
assert_not "$TEST_HOME/.agents/skills/unslop"
assert_file "$TEST_HOME/.ruver/memory.md"
assert_file "$TEST_HOME/.agents/skills/foreign-file"
ok uninstall-keeps-memory

set +e
HOME="$TEST_HOME" XDG_CONFIG_HOME="$TEST_HOME/.config" \
  XDG_DATA_HOME="$TEST_HOME/.local/share" \
  "$INSTALL" uninstall --purge --yes >/tmp/ruver-purge.out 2>/tmp/ruver-purge.err
got=$?
set -e
assert_eq "$got" "1" "purge of checkout clone must fail"
assert_file "$TEST_HOME/.ruver/memory.md"
ok purge-refuses-checkout

man="$TEST_HOME/.local/share/ruver/repo"
mkdir -p "$man"
git -C "$man" init -q
printf 'repo=%s\norigin=%s\n' "$man" "https://github.com/ruverd/skills.git" \
  >"$TEST_HOME/.config/ruver/config"
set +e
HOME="$TEST_HOME" XDG_CONFIG_HOME="$TEST_HOME/.config" \
  XDG_DATA_HOME="$TEST_HOME/.local/share" \
  "$INSTALL" uninstall --purge </dev/null >/tmp/ruver-purge-notty.out 2>/tmp/ruver-purge-notty.err
got=$?
set -e
assert_eq "$got" "1" "purge without --yes on non-TTY must fail"
[[ -d "$man" ]] || fail "purge without --yes deleted managed repo"
grep -qi -- '--yes' /tmp/ruver-purge-notty.err /tmp/ruver-purge-notty.out \
  || fail "purge without --yes should say --yes is required"
ok purge-requires-yes-without-tty

HOME="$TEST_HOME" XDG_CONFIG_HOME="$TEST_HOME/.config" \
  XDG_DATA_HOME="$TEST_HOME/.local/share" \
  "$INSTALL" uninstall --purge --yes
assert_not "$man"
assert_file "$TEST_HOME/.ruver/memory.md"
ok purge-managed

# After purge, TEST_HOME may have uninstalled links and config pointing at a
# managed clone that was deleted. Restore setup first.
run_install setup >/dev/null
out="$(run_install status)"
echo "$out" | grep -q 'repo' || fail "status missing repo"
echo "$out" | grep -q 'version' || fail "status missing version"
echo "$out" | grep -q 'ok' || fail "status missing ok homes"
ok status

# PATH symlink must resolve to the repo (not treat ~/.local/bin as bootstrap).
run_install setup >/dev/null
bin="$TEST_HOME/.local/bin/ruver"
assert_link "$bin"
out="$(HOME="$TEST_HOME" XDG_CONFIG_HOME="$TEST_HOME/.config" \
  XDG_DATA_HOME="$TEST_HOME/.local/share" "$bin" status)"
echo "$out" | grep -q 'repo' || fail "status via PATH symlink failed"
ok status-via-symlink

set +e
HOME="$TEST_HOME" "$INSTALL" --plugin >/tmp/ruver-plugin.out 2>/tmp/ruver-plugin.err
got=$?
set -e
assert_eq "$got" "1" "--plugin exit"
grep -q 'grok plugin install ruver' /tmp/ruver-plugin.err || fail "--plugin message"
ok plugin-refused

out="$(HOME="$TEST_HOME" XDG_CONFIG_HOME="$TEST_HOME/.config" \
  XDG_DATA_HOME="$TEST_HOME/.local/share" \
  "$INSTALL" </dev/null)"
grep -q 'ruver setup' <<< "$out" || fail "no-tty list missing setup"
grep -q 'ruver update' <<< "$out" || fail "no-tty list missing update"
ok no-tty-list

# --- report: read the run ledger, surface laps and a dead QA lease ---
REP_HOME="$(mktemp -d "${TMPDIR:-/tmp}/ruver-report.XXXXXX")"
BUS="$REP_HOME/.ruver/some-repo/.ruver-bus"
mkdir -p "$BUS"
now=$(date -u +%s)
{
  printf 'ts_iso\tepoch\tgraph\tnode\tevent\tlap\tsha\tresult\tdetail\n'
  printf 'x\t%s\tdeveloper\tdeliver\tenter\t1\tabc\t\t\n' "$((now - 900))"
  printf 'x\t%s\tdeveloper\tdeliver\texit\t1\tabc\tdone\t\n' "$((now - 300))"
  for lap in 1 2 3; do
    printf 'x\t%s\tqa\texecute\tenter\t%s\tabc\t\t\n' "$((now - 280 + lap))" "$lap"
    printf 'x\t%s\tqa\texecute\texit\t%s\tabc\tFAIL\t\n' "$((now - 200 + lap))" "$lap"
  done
} >"$BUS/RUN_LOG.tsv"
# A claim from four hours ago is past any sane lease.
claimed="$(date -u -r $((now - 14400)) +%Y-%m-%dT%H:%M:%SZ 2>/dev/null \
  || date -u -d "@$((now - 14400))" +%Y-%m-%dT%H:%M:%SZ)"
cat >"$BUS/JOBS.md" <<EOF
---
schema: 2
qa_active: "qa-pr-42"
qa_claimed_at: "$claimed"
qa_waiting: "dev-ABC-1"
updated_at: ""
---
EOF

set +e
out="$(HOME="$REP_HOME" XDG_CONFIG_HOME="$REP_HOME/.config" \
  XDG_DATA_HOME="$REP_HOME/.local/share" "$INSTALL" report 2>&1)"
got=$?
set -e
assert_eq "$got" "0" "report exit"
echo "$out" | grep -q 'some-repo' || fail "report missing the repo slug: $out"
echo "$out" | grep -q 'developer/deliver' || fail "report missing developer/deliver"
echo "$out" | grep -qE 'qa/execute.*3' || fail "report should show 3 laps of qa/execute: $out"
echo "$out" | grep -q '10m00s' || fail "report should total developer/deliver at 10m00s: $out"
echo "$out" | grep -qi 'lease' || fail "report should flag the dead QA lease: $out"
echo "$out" | grep -q 'qa-pr-42' || fail "report should name the stuck claim: $out"
rm -rf "$REP_HOME"
ok report

# --- report: nothing recorded yet is not an error ---
EMPTY_HOME="$(mktemp -d "${TMPDIR:-/tmp}/ruver-report-empty.XXXXXX")"
set +e
out="$(HOME="$EMPTY_HOME" XDG_CONFIG_HOME="$EMPTY_HOME/.config" \
  XDG_DATA_HOME="$EMPTY_HOME/.local/share" "$INSTALL" report 2>&1)"
got=$?
set -e
assert_eq "$got" "0" "report on an empty home exit"
echo "$out" | grep -qi 'no run' || fail "report should say nothing is recorded: $out"
rm -rf "$EMPTY_HOME"
ok report-empty

# --- report: a repo with an idle JOBS.md and no ledger says nothing at all ---
QUIET_HOME="$(mktemp -d "${TMPDIR:-/tmp}/ruver-report-quiet.XXXXXX")"
mkdir -p "$QUIET_HOME/.ruver/old-repo/.ruver-bus"
cat >"$QUIET_HOME/.ruver/old-repo/.ruver-bus/JOBS.md" <<'EOF'
---
schema: 2
qa_active: ""
qa_claimed_at: ""
qa_waiting: ""
updated_at: ""
---
EOF
set +e
out="$(HOME="$QUIET_HOME" XDG_CONFIG_HOME="$QUIET_HOME/.config" \
  XDG_DATA_HOME="$QUIET_HOME/.local/share" "$INSTALL" report 2>&1)"
got=$?
set -e
assert_eq "$got" "0" "report on an idle repo exit"
echo "$out" | grep -q 'old-repo' && fail "report printed an empty header: $out"
echo "$out" | grep -qi 'no run' || fail "report should say nothing is recorded: $out"
rm -rf "$QUIET_HOME"
ok report-quiet

# --- report: host transcript tokens, classified by session cwd ---
TOK_HOME="$(mktemp -d "${TMPDIR:-/tmp}/ruver-report-tok.XXXXXX")"
python3 - "$TOK_HOME" <<'PY'
import json, os, sys, urllib.parse
from pathlib import Path
home = Path(sys.argv[1])
log_dir = home / ".grok" / "logs"
log_dir.mkdir(parents=True)
sessions = home / ".grok" / "sessions"
lstm_cwd = "/tmp/orca/empath-ui/pr-empath-ui-2583-lstm"
rev_cwd = "/tmp/orca/empath-api-v2/pr-1546-review"
fd_cwd = "/tmp/orca/empath-ui/feature-dev-4409"
for cwd, sid in (
    (lstm_cwd, "01aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"),
    (rev_cwd, "01bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"),
    (fd_cwd, "01cccccccccccccccccccccccccccccccc"),
):
    (sessions / urllib.parse.quote(cwd, safe="")).mkdir(parents=True)
    (sessions / urllib.parse.quote(cwd, safe="") / sid).mkdir()
rows = [
    ("01aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", 1000, 100),
    ("01aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", 2000, 1500),
    ("01bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb", 400, 0),
    ("01cccccccccccccccccccccccccccccccc", 800, 200),
]
with (log_dir / "unified.jsonl").open("w", encoding="utf-8") as handle:
    for sid, prompt, cached in rows:
        json.dump({
            "ts": "2026-09-03T12:00:00.000Z",
            "msg": "shell.turn.inference_done",
            "sid": sid,
            "ctx": {
                "prompt_tokens": prompt,
                "cached_prompt_tokens": cached,
                "completion_tokens": 10,
            },
        }, handle)
        handle.write("\n")
PY
set +e
out="$(HOME="$TOK_HOME" XDG_CONFIG_HOME="$TOK_HOME/.config" \
  XDG_DATA_HOME="$TOK_HOME/.local/share" "$INSTALL" report 2>&1)"
got=$?
set -e
assert_eq "$got" "0" "report tokens exit"
echo "$out" | grep -q 'tokens (host transcript)' || fail "report missing tokens heading: $out"
echo "$out" | grep -qE 'lstm' || fail "report missing lstm class: $out"
echo "$out" | grep -qE 'reviewer' || fail "report missing reviewer class: $out"
echo "$out" | grep -qE 'fd' || fail "report missing fd class: $out"
echo "$out" | grep -qE 'calls[[:space:]]+4' || fail "report should total 4 calls: $out"
echo "$out" | grep -qi 'uncached' || fail "report should name uncached: $out"
echo "$out" | grep -qi 'no run' && fail "tokens-only report should not say no runs: $out"
rm -rf "$TOK_HOME"
ok report-tokens

echo "all passed"
