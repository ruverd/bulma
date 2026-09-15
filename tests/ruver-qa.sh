#!/usr/bin/env bash
# Walk video is the plan, not qa:login. Text fixtures only. No network.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
EXEC="$ROOT/skills/ruver-qa/references/EXECUTION.md"
COMMENT="$ROOT/skills/ruver-qa/references/COMMENT.md"
VERDICTS="$ROOT/skills/ruver-qa/references/VERDICTS.md"
BAA="$ROOT/skills/before-and-after/SKILL.md"
GATE="$ROOT/skills/ruver-qa/scripts/walk-video-gate.sh"

fail() { echo "FAIL: $*" >&2; exit 1; }
ok() { echo "ok  $*"; }

[[ -f "$EXEC" ]] || fail "missing $EXEC"
[[ -f "$COMMENT" ]] || fail "missing $COMMENT"
[[ -f "$VERDICTS" ]] || fail "missing $VERDICTS"
[[ -f "$BAA" ]] || fail "missing $BAA"

# 1. Forbidden recipe gone
if grep -F -q 'Restore state inside it' "$EXEC"; then
  fail "EXECUTION.md still has 'Restore state inside it'"
fi
# shellcheck disable=SC2016  # markdown backticks in the forbidden phrase
if grep -F -q 'Load `--restore` / `state load` inside it' "$BAA" \
  || grep -F -q 'Load --restore / state load inside it' "$BAA"; then
  fail "before-and-after/SKILL.md still has 'Load --restore / state load inside it'"
fi
ok forbidden-recipe-gone

# 2. Copy-paste sequence in EXECUTION.md (Auth)
grep -F -q 'gated app route' "$EXEC" || fail "EXECUTION.md missing 'gated app route'"
grep -F -q 'Never record before login' "$EXEC" || fail "EXECUTION.md missing 'Never record before login'"
# shellcheck disable=SC2016  # markdown backticks are literal
grep -F -q 'does not accept `--state`' "$EXEC" || fail "EXECUTION.md missing 'does not accept --state'"
grep -F -q 'walk-video-gate.sh' "$EXEC" || fail "EXECUTION.md missing walk-video-gate.sh"
grep -F -q -- "--session-name \"\$SESSION\"" "$EXEC" || fail "EXECUTION.md missing supported session restore"
grep -F -q -- '--headed false' "$EXEC" || fail "EXECUTION.md must force headless agent-browser"
grep -F -q 'Do not switch tools' "$EXEC" || fail "EXECUTION.md must forbid browser fallback"
grep -F -q "agent-browser --session \"\$SESSION\" close" "$EXEC" || fail "EXECUTION.md must close its browser session"
if grep -F -q -- '--restore' "$EXEC" || grep -F -q -- '--restore' "$BAA"; then
  fail "QA docs use unsupported agent-browser --restore"
fi

if ! awk '
  /^[[:space:]]*```/ { fence = !fence; next }
  !fence { next }
  /--session/ && /record start/ && $0 !~ /--state/ && $0 !~ /https?:\/\// && $0 !~ /\$URL/ {
    found = 1
  }
  END { exit found ? 0 : 1 }
' "$EXEC"; then
  fail "EXECUTION.md missing fenced record start with --session and no --state/--restore/URL"
fi

grep -F -q 'qa:login' "$EXEC" || fail "EXECUTION.md missing qa:login"
if ! tr '\n' ' ' < "$EXEC" | grep -E -q 'qa:login.*--session|different --session than record start|same --session'; then
  fail "EXECUTION.md must require qa:login and record start to share the same --session"
fi
ok execution-auth-sequence

# 3. Verdict gate
hard="$(awk '/^## Hard rules/,0' "$COMMENT" | tr '\n' ' ' | tr -s ' ')"
[[ -n "$hard" ]] || fail "COMMENT.md missing Hard rules"
echo "$hard" | grep -qi 'login wall' || fail "Hard rules missing login wall"
echo "$hard" | grep -F -q 'Check your email' || fail "Hard rules missing 'Check your email'"
echo "$hard" | grep -qi 'walk evidence' || fail "Hard rules missing 'walk evidence'"
echo "$hard" | grep -qi 'never PASS' || fail "Hard rules must say login-wall tape is never PASS"
echo "$hard" | grep -qi 're-record' || fail "Hard rules missing re-record"
echo "$hard" | grep -q 'BLOCKED' || fail "Hard rules missing BLOCKED"

# shellcheck disable=SC2016  # VERDICTS table cell is | `PASS`
pass_row="$(grep -F '| `PASS`' "$VERDICTS" || true)"
[[ -n "$pass_row" ]] || fail "VERDICTS.md missing PASS row"
echo "$pass_row" | grep -qiE 'login[- ]wall' || fail "PASS row missing login-wall"
echo "$pass_row" | grep -qiE 'Check[- ]your[- ]email' || fail "PASS row missing Check-your-email"
echo "$pass_row" | grep -F -q '.webm' || fail "PASS row missing .webm"
echo "$pass_row" | grep -qiE 'not PASS|never PASS' || fail "PASS row must say login-wall .webm is not PASS"
ok verdict-gate

# 4. Helper exists and is executable
[[ -f "$GATE" ]] || fail "walk-video-gate.sh missing"
[[ -x "$GATE" ]] || fail "walk-video-gate.sh not executable"
ok helper-executable

# 5. Helper behavior (text fixtures, not a real .webm)
TMP="$(mktemp -d "${TMPDIR:-/tmp}/ruver-qa.XXXXXX")"
trap 'rm -rf "$TMP"' EXIT

printf '%s\n' 'Sign in' 'Email field' >"$TMP/sign-in.txt"
printf '%s\n' 'Check your email' 'We sent a link' >"$TMP/check-email.txt"
printf '%s\n' 'Live streams' 'Grow' >"$TMP/gated.txt"
printf '%s\n' 'Sign in' >"$TMP/s10-stop.txt"
printf '%s\n' 'Sign in' >"$TMP/wall-start.txt"
printf '%s\n' 'Check your email' >"$TMP/wall-middle.txt"
printf '%s\n' 'https://app.example.com/login' >"$TMP/wall-stop.txt"

gate_exit() {
  "$GATE" "$@" >/dev/null 2>&1 && GATE_EXIT=0 || GATE_EXIT=$?
}

gate_exit --start "$TMP/sign-in.txt"
[[ "$GATE_EXIT" -ne 0 ]] || fail "sign-in start should fail (exit=$GATE_EXIT)"
ok helper-sign-in-start

gate_exit --start "$TMP/check-email.txt"
[[ "$GATE_EXIT" -ne 0 ]] || fail "check-your-email start should fail (exit=$GATE_EXIT)"
ok helper-check-email-start

gate_exit --start "$TMP/gated.txt" --stop "$TMP/s10-stop.txt"
[[ "$GATE_EXIT" -eq 0 ]] || fail "gated start + Sign in stop (S10) should pass (exit=$GATE_EXIT)"
ok helper-s10-signed-out-stop

gate_exit --start "$TMP/wall-start.txt" --middle "$TMP/wall-middle.txt" --stop "$TMP/wall-stop.txt"
[[ "$GATE_EXIT" -ne 0 ]] || fail "all login-wall samples should fail (exit=$GATE_EXIT)"
ok helper-all-login-wall

gate_exit --stop "$TMP/gated.txt"
[[ "$GATE_EXIT" -ne 0 ]] || fail "missing --start should fail (exit=$GATE_EXIT)"
ok helper-missing-start

echo "all passed"
