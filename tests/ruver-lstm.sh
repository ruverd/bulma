#!/usr/bin/env bash
# LSTM P0: hard verify + prove before reply. Text fixtures only. No network.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LSTM="$ROOT/skills/ruver-lstm"

fail() { echo "FAIL: $*" >&2; exit 1; }
ok() { echo "ok  $*"; }

need() {
  local file="$1"
  [[ -f "$file" ]] || fail "missing $file"
}

need "$LSTM/GRAPH.md"
need "$LSTM/nodes/verify.md"
need "$LSTM/nodes/prove.md"
need "$LSTM/nodes/patch.md"
need "$LSTM/nodes/reply.md"
need "$LSTM/STATE.schema.md"
need "$LSTM/templates/STATE.md"

has() {
  grep -F -q "$1" "$2" || fail "$2 missing '$1'"
}

# --- verify binds and splits the two questions ---

has 'claim_true' "$LSTM/nodes/verify.md"
has 'fix_ok_here' "$LSTM/nodes/verify.md"
has 'path:line' "$LSTM/nodes/verify.md"
has 'risk' "$LSTM/nodes/verify.md"
grep -Fi -q 'cite' "$LSTM/nodes/verify.md" || fail "verify.md skip must require a cite"
has 'claim_true' "$LSTM/STATE.schema.md"
has 'fix_ok_here' "$LSTM/templates/STATE.md"
ok verify-bind

# --- prove sits between patch and reply ---

has 'prove' "$LSTM/GRAPH.md"
has 'spec_verdict' "$LSTM/nodes/prove.md"
has 'quality_verdict' "$LSTM/nodes/prove.md"
has 'tester' "$LSTM/nodes/prove.md"
has 'prove_fix_loops' "$LSTM/GRAPH.md"
has 'prove_fix_loops' "$LSTM/STATE.schema.md"
has 'proving' "$LSTM/STATE.schema.md"

if grep -F -q 'Then **reply**' "$LSTM/nodes/patch.md"; then
  fail "patch.md still jumps to reply; prove must run first"
fi
has 'prove' "$LSTM/nodes/patch.md"

# Fail must not dismiss.
if ! tr '\n' ' ' < "$LSTM/nodes/prove.md" | grep -E -q 'Do not \*\*reply\*\*|Do not reply'; then
  fail "prove.md must forbid reply on fail"
fi
has 'CHANGES_REQUESTED' "$LSTM/nodes/prove.md"
ok prove-before-reply

# --- last loop is a fresh coder ---

grep -F -q 'fresh' "$LSTM/nodes/prove.md" || fail "prove.md must fresh-coder the last loop"
ok prove-fresh-coder

# --- observations: both writers wire in, script validates and dedups ---

OBSERVE="$ROOT/skills/ruver-bus/scripts/observe.py"
need "$OBSERVE"
need "$ROOT/skills/ruver-bus/INSIGHTS.md"
has 'observe.py --source lstm' "$LSTM/nodes/verify.md"
has 'observe.py --source reviewer' "$ROOT/skills/ruver-reviewer/nodes/code_review.md"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
OBS="$TMP/obs.jsonl"
observe() {
  python3 "$OBSERVE" --file "$OBS" --pr-ref acme/app#7 --sha abc1234 \
    --source lstm --axis correctness --severity important --claim-true yes \
    --pattern "Guard added on manual save is missing on autosave" \
    --path src/save.ts --line 40 "$@"
}

out="$(observe --comment-id 1 --reviewer alice --ours-open 'src/save.ts:45:missing-guard|src/b.ts:1:x')"
[[ "$out" == "written gh-1 caught_by_ours=yes" ]] || fail "observe near line: $out"
out="$(observe --comment-id 2 --reviewer alice --ours-open 'src/save.ts:90:far')"
[[ "$out" == "written gh-2 caught_by_ours=no" ]] || fail "observe far line: $out"
out="$(observe --comment-id 3 --reviewer alice)"
[[ "$out" == "written gh-3 caught_by_ours=unknown" ]] || fail "observe no marker: $out"
out="$(observe --comment-id 1 --reviewer alice)"
[[ "$out" == duplicate* ]] || fail "observe must skip a known id: $out"
[[ "$(wc -l < "$OBS" | tr -d ' ')" == "3" ]] || fail "observe wrote a duplicate line"

rc=0; observe --comment-id 4 --reviewer 'coderabbitai[bot]' 2>/dev/null || rc=$?
[[ "$rc" == "4" ]] || fail "observe must refuse bot reviewers (rc=$rc)"
rc=0; observe --comment-id 5 --reviewer alice --pattern "$(printf 'x%.0s' {1..301})" 2>/dev/null || rc=$?
[[ "$rc" == "4" ]] || fail "observe must cap the pattern (rc=$rc)"
rc=0; observe --comment-id 6 --reviewer alice --pr-ref not-a-ref 2>/dev/null || rc=$?
[[ "$rc" == "4" ]] || fail "observe must validate pr-ref (rc=$rc)"
grep -F -q '"would_existing_agent_catch_it": "yes"' "$OBS" || fail "observe must keep the legacy field"
ok observations

fd() {
  python3 "$OBSERVE" --file "$OBS" --source fd --axis tests --severity important --claim-true yes \
    --pattern "Test sets up its spy inside the try it tests" --path src/a.test.ts --line 3 "$@"
}
out="$(fd --reviewer ruver-fd-reviewer --job dev-abc-1 --finding-id spy-in-try)"
[[ "$out" == "written fd-dev-abc-1-spy-in-try caught_by_ours=self" ]] || fail "observe fd: $out"
out="$(fd --reviewer ruver-fd-quality --job dev-abc-1 --finding-id spy-in-try)"
[[ "$out" == duplicate* ]] || fail "observe fd must dedup a finding across laps: $out"
rc=0; fd --reviewer alice --job dev-abc-1 --finding-id x 2>/dev/null || rc=$?
[[ "$rc" == "4" ]] || fail "observe fd must refuse a non-gate reviewer (rc=$rc)"
rc=0; fd --reviewer ruver-fd-reviewer --job dev-abc-1 --finding-id "Not A Slug" 2>/dev/null || rc=$?
[[ "$rc" == "4" ]] || fail "observe fd must require a kebab finding id (rc=$rc)"
rc=0; python3 "$OBSERVE" --file "$OBS" --source lstm --reviewer alice --pr-ref acme/app#7 --axis tests \
  --severity important --claim-true yes --pattern "x" 2>/dev/null || rc=$?
[[ "$rc" == "4" ]] || fail "observe lstm must still require comment id and sha (rc=$rc)"
has 'observe.py --source fd --reviewer ruver-fd-reviewer' "$ROOT/skills/ruver-feature-delivery/nodes/reviewer.md"
has 'observe.py --source fd --reviewer ruver-fd-quality' "$ROOT/skills/ruver-feature-delivery/nodes/quality.md"
ok observations-fd

echo "all passed"
