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

echo "all passed"
