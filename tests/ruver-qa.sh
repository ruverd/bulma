#!/usr/bin/env bash
# Per-surface clips, not qa:login. Text fixtures only. No network.
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

# 6. Per-surface clips, not one whole-plan tape
VIDEO="$ROOT/skills/ruver-qa/references/VIDEO.md"
CONCAT="$ROOT/skills/ruver-qa/scripts/concat-clips.sh"
PLAN="$ROOT/skills/ruver-qa/references/PLAN.md"
TPL="$ROOT/skills/ruver-qa/templates/PLAN.md"
CMD="$ROOT/docs/commands/ruver-qa.md"

[[ -f "$VIDEO" ]] || fail "missing $VIDEO (clip recipe)"
[[ -f "$PLAN" ]] || fail "missing $PLAN"
[[ -f "$TPL" ]] || fail "missing $TPL"
[[ -f "$CMD" ]] || fail "missing $CMD"

if grep -F -q 'whole plan walk' "$EXEC"; then
  fail "EXECUTION.md still records the whole plan walk as one tape"
fi
if grep -F -q 'Record the plan walk (happy' "$BAA"; then
  fail "before-and-after still tells QA to record one plan-walk tape"
fi

grep -F -q 'record restart' "$VIDEO" || fail "VIDEO.md missing record restart"
grep -qi 'per-surface' "$VIDEO" || fail "VIDEO.md missing per-surface clips"
# type during record, fill only off-tape
if ! grep -Eqi 'type.{0,40}not fill|not fill.{0,40}type' "$VIDEO"; then
  fail "VIDEO.md must require type (not fill) while recording"
fi
grep -qi 'pass_if' "$VIDEO" || fail "VIDEO.md missing pass_if still"
grep -qi 'annotate' "$VIDEO" || fail "VIDEO.md missing annotated pass_if still"
grep -qi 'hydrat' "$VIDEO" || fail "VIDEO.md missing hydrate-then-record"
grep -qiE 'login[- ]wall' "$VIDEO" || fail "VIDEO.md missing login-wall"
ok clip-recipe

[[ -f "$CONCAT" ]] || fail "concat-clips.sh missing"
[[ -x "$CONCAT" ]] || fail "concat-clips.sh not executable"
"$CONCAT" -h >/dev/null 2>&1 || "$CONCAT" --help >/dev/null 2>&1 \
  || fail "concat-clips.sh --help should exit 0"
ok concat-helper-exists

# 7. Blast radius in the plan (before any browser step)
grep -qi 'blast radius' "$PLAN" || fail "PLAN.md missing blast radius"
grep -F -q 'UNKNOWN' "$PLAN" || fail "PLAN.md missing UNKNOWN (zero callers is not skip)"
if ! grep -qiE 'zero callers|not skip|do not skip' "$PLAN"; then
  fail "PLAN.md must say zero callers is UNKNOWN, not skip"
fi
grep -qi 'blast radius' "$TPL" || fail "templates/PLAN.md missing blast radius"
grep -F -q 'UNKNOWN' "$TPL" || fail "templates/PLAN.md missing UNKNOWN"
ok blast-radius

# 8. AC coverage table, console/network, visual still, exploratory
if ! grep -qiE 'AC coverage|coverage table' "$COMMENT"; then
  fail "COMMENT.md missing AC coverage table"
fi
grep -qi 'Criterion' "$COMMENT" || fail "COMMENT.md AC table missing Criterion column"
grep -qi 'Evidence' "$COMMENT" || fail "COMMENT.md AC table missing Evidence column"
grep -qi 'console' "$EXEC" || fail "EXECUTION.md missing console check"
grep -qi 'errors' "$EXEC" || fail "EXECUTION.md missing errors check"
grep -qi 'network' "$EXEC" || fail "EXECUTION.md missing network check"
grep -qi 'explorat' "$EXEC" || fail "EXECUTION.md missing exploratory pass"
grep -F -q 'dogfood' "$EXEC" || fail "EXECUTION.md must load agent-browser dogfood for exploratory"
if ! grep -qiE 'do not follow|off-script|not follow' "$EXEC"; then
  fail "EXECUTION.md exploratory must not follow the scripted how"
fi
grep -qiE 'app-level|running app' "$VERDICTS" || fail "VERDICTS.md missing app-level proof on PASS"
ok ac-evidence-exploratory

grep -qi 'clip' "$CMD" || fail "docs/commands/ruver-qa.md should mention clips, not one walk tape"
ok command-page-clips

# concat-clips: missing args fail; with ffmpeg, concat two tiny webms
"$CONCAT" >/dev/null 2>&1 && CONCAT_EXIT=0 || CONCAT_EXIT=$?
[[ "$CONCAT_EXIT" -ne 0 ]] || fail "concat-clips.sh with no args should fail"
ok concat-missing-args

if command -v ffmpeg >/dev/null; then
  CLIPDIR="$TMP/clips"
  mkdir -p "$CLIPDIR"
  ffmpeg -v error -y -f lavfi -i color=c=red:s=32x32:d=0.2 \
    -c:v libvpx -b:v 50k "$CLIPDIR/a.webm" </dev/null \
    || fail "could not make fixture clip a.webm"
  ffmpeg -v error -y -f lavfi -i color=c=blue:s=32x32:d=0.2 \
    -c:v libvpx -b:v 50k "$CLIPDIR/b.webm" </dev/null \
    || fail "could not make fixture clip b.webm"
  "$CONCAT" --out "$CLIPDIR/reel.webm" "$CLIPDIR/a.webm" "$CLIPDIR/b.webm" \
    || fail "concat-clips.sh failed on two fixtures"
  [[ -s "$CLIPDIR/reel.webm" ]] || fail "concat-clips.sh wrote empty reel"
  ok concat-ffmpeg-reel
else
  ok concat-ffmpeg-skipped
fi

# 9. Backend / endpoint PRs still execute. Proof is an HTTP still or FE screens.
SKILL="$ROOT/skills/ruver-qa/SKILL.md"
GRAPH="$ROOT/skills/ruver-qa/GRAPH.md"
PRODUCT="$ROOT/skills/ruver-feature-delivery/PRODUCT.md"
REQ_QA="$ROOT/skills/ruver-developer/nodes/request_qa.md"
README="$ROOT/README.md"
PROOF="$ROOT/skills/ruver-qa/scripts/http-proof.sh"

[[ -f "$SKILL" ]] || fail "missing $SKILL"
[[ -f "$GRAPH" ]] || fail "missing $GRAPH"
[[ -f "$PRODUCT" ]] || fail "missing $PRODUCT"
[[ -f "$REQ_QA" ]] || fail "missing $REQ_QA"

if grep -F -q '| plan | no surface |' "$GRAPH"; then
  fail "GRAPH.md still stops on no surface (endpoints are a plan)"
fi
grep -F -q 'no route and no endpoint' "$GRAPH" \
  || fail "GRAPH.md must stop only when there is no route and no endpoint"

grep -F -q 'A backend PR still runs' "$SKILL" \
  || fail "SKILL.md must say a backend PR still runs"
if ! grep -qiE 'missing UI is not a skip|not a skip' "$PLAN"; then
  fail "PLAN.md must say missing UI is not a skip"
fi
grep -F -q 'no route and no endpoint' "$PLAN" \
  || fail "PLAN.md empty-plan gate must be no route and no endpoint"

grep -F -q 'http-proof.sh' "$EXEC" \
  || fail "EXECUTION.md missing http-proof.sh"
grep -F -q 'Exploratory is UI surfaces only' "$EXEC" \
  || fail "EXECUTION.md must skip browser exploratory on endpoint-only"
grep -F -q 'Missing agent-browser on endpoint-only is not BLOCKED' "$EXEC" \
  || fail "EXECUTION.md must not BLOCKED API-only when agent-browser is missing"

echo "$pass_row" | grep -qi 'HTTP still' \
  || fail "PASS row missing HTTP still for API/backend"
echo "$pass_row" | grep -F -q 'kind: endpoint' \
  || fail "PASS row must say .webm is not required for kind: endpoint"

echo "$hard" | grep -qi 'HTTP still' \
  || fail "Hard rules missing HTTP still"
grep -qi 'HTTP still' "$COMMENT" || fail "COMMENT.md missing HTTP still"

grep -qi 'HTTP still' "$PRODUCT" \
  || fail "PRODUCT.md qa_tool=http must name HTTP still"

if grep -F -q 'QA must still comment + video before' "$REQ_QA"; then
  fail "request_qa.md still requires video on every QA including backend"
fi
grep -qi 'HTTP still' "$REQ_QA" \
  || fail "request_qa.md must accept HTTP still as QA evidence"

if grep -F -q 'API-only PRs skip stills and video' "$README"; then
  fail "README still tells API QA to skip stills"
fi

[[ -f "$PROOF" ]] || fail "http-proof.sh missing"
[[ -x "$PROOF" ]] || fail "http-proof.sh not executable"
"$PROOF" -h >/dev/null 2>&1 || "$PROOF" --help >/dev/null 2>&1 \
  || fail "http-proof.sh --help should exit 0"
"$PROOF" >/dev/null 2>&1 && PROOF_EXIT=0 || PROOF_EXIT=$?
[[ "$PROOF_EXIT" -ne 0 ]] || fail "http-proof.sh with no args should fail"
"$PROOF" --out "$TMP/http-proof.png" --method GET \
  --url 'http://example.test/v1/items' --status 200 \
  --body '{"ok":true}' \
  || fail "http-proof.sh failed on a fixture"
python3 - "$TMP/http-proof.png" <<'PY' || fail "http-proof.sh did not write a PNG"
import sys
path = sys.argv[1]
data = open(path, "rb").read()
if not data.startswith(b"\x89PNG\r\n\x1a\n"):
    raise SystemExit("not a PNG")
if len(data) < 200:
    raise SystemExit("PNG too small")
PY
ok backend-endpoint-proof

echo "all passed"
