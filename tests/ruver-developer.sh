#!/usr/bin/env bash
# Developer P0+P1: risk axis, split review verdicts, resume invariants,
# gated plan_critic, Walk line. Text fixtures only. No network.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FD="$ROOT/skills/ruver-feature-delivery"
DEV="$ROOT/skills/ruver-developer"

fail() { echo "FAIL: $*" >&2; exit 1; }
ok() { echo "ok  $*"; }

need() {
  local file="$1"
  [[ -f "$file" ]] || fail "missing $file"
}

need "$FD/ROUTING.md"
need "$FD/GRAPH.md"
need "$FD/STATE.schema.md"
need "$FD/templates/STATE.md"
need "$FD/nodes/triage.md"
need "$FD/nodes/blast.md"
need "$FD/nodes/reviewer.md"
need "$FD/nodes/plan_critic.md"
need "$FD/VOICE.md"
need "$FD/HANDOFF.md"
need "$DEV/ARGS.md"
need "$DEV/nodes/resume.md"
need "$DEV/GRAPH.md"

has() {
  grep -F -q "$1" "$2" || fail "$2 missing '$1'"
}

has_re() {
  grep -E -q "$1" "$2" || fail "$2 missing /$1/"
}

# --- risk enum (ROUTING is the home; schema + template must match) ---

has_re 'risk: low \| normal \| elevated' "$FD/ROUTING.md"
# shellcheck disable=SC2016  # markdown backticks in the schema table cell
grep -F -q '`risk` | low \| normal \| elevated' "$FD/STATE.schema.md" \
  || fail "$FD/STATE.schema.md missing risk enum"
has_re '\*\*risk:\*\* low \| normal \| elevated' "$FD/templates/STATE.md"
has 'risk_reason' "$FD/nodes/triage.md"
has 'risk:' "$FD/nodes/triage.md"

if grep -E -q 'full_feature even if it .+looks like a bug' "$FD/ROUTING.md"; then
  fail "ROUTING.md still upgrades auth bugs to full_feature"
fi
has 'debug_fix' "$FD/ROUTING.md"
has 'elevated' "$FD/ROUTING.md"
# Auth bug stays a bug. Feature stays a feature. Risk is the extra gate.
if ! tr '\n' ' ' < "$FD/ROUTING.md" | grep -E -q 'debug_fix.{0,80}elevated'; then
  fail "ROUTING.md must route an auth/billing bug as debug_fix + elevated"
fi
ok risk-enum

# --- blast on elevated light_change ---

if ! tr '\n' ' ' < "$FD/ROUTING.md" | grep -E -q 'light_change.{0,200}elevated|elevated.{0,200}light_change'; then
  fail "ROUTING.md must mention blast/light_change together with elevated"
fi
has 'elevated' "$FD/nodes/blast.md"
has 'elevated' "$FD/GRAPH.md"

# GRAPH must not send every light_change straight to quality.
if grep -F -q '| evidence | done + light_change | **quality**' "$FD/GRAPH.md"; then
  fail "GRAPH.md still skips blast on all light_change"
fi
has 'risk=elevated' "$FD/GRAPH.md"
ok blast-elevated-light

# --- split review verdicts ---

has 'spec_verdict' "$FD/nodes/reviewer.md"
has 'quality_verdict' "$FD/nodes/reviewer.md"
has 'spec_verdict' "$FD/STATE.schema.md"
has 'quality_verdict' "$FD/STATE.schema.md"
has 'spec_verdict' "$FD/templates/STATE.md"
has 'quality_verdict' "$FD/templates/STATE.md"
has 'spec_verdict' "$FD/GRAPH.md"
has 'quality_verdict' "$FD/GRAPH.md"

if ! tr '\n' ' ' < "$FD/nodes/reviewer.md" | grep -E -q 'both pass|spec_verdict=pass.{0,40}quality_verdict=pass'; then
  fail "reviewer.md must pass only when both verdicts pass"
fi
# Old fail line treated spec as optional.
if grep -E -q 'fail — missing tests, off design' "$FD/nodes/reviewer.md"; then
  fail "reviewer.md still uses the old single fail line (spec can rubber-stamp)"
fi
ok split-verdicts

# --- resume invariants (world vs STATE) ---

has 'STATE.sha' "$DEV/ARGS.md"
has 'qa_verdict_log' "$DEV/ARGS.md"
grep -Fi -q 'invariants' "$DEV/ARGS.md" || fail "$DEV/ARGS.md missing invariants"
grep -Fi -q 'drift' "$DEV/nodes/resume.md" || fail "$DEV/nodes/resume.md missing drift"
has '# expect:' "$FD/HANDOFF.md"
grep -Fi -q 'invariants' "$FD/HANDOFF.md" || fail "$FD/HANDOFF.md missing invariants"

# Must not skip a node only because the file exists.
if grep -F -q 'Skip nodes whose outputs already exist and match STATE' "$DEV/nodes/resume.md"; then
  fail "resume.md still skips when files match STATE (must replay world)"
fi
has 'skip finished when invariants match' "$DEV/GRAPH.md"
has 'invariants match' "$FD/GRAPH.md"
ok resume-invariants

# --- gated plan_critic ---

has 'plan_critic' "$FD/GRAPH.md"
has 'plan_critic' "$FD/ROUTING.md"
has 'plan_critic' "$FD/nodes/plan_critic.md"
has 'plan_critic_verdict' "$FD/STATE.schema.md"
has 'plan_critic_verdict' "$FD/templates/STATE.md"
has 'critiquing' "$FD/STATE.schema.md"
has 'risk=elevated' "$FD/nodes/plan_critic.md"
has 'spawn' "$FD/nodes/plan_critic.md"
# Must not run on bugs.
if ! tr '\n' ' ' < "$FD/nodes/plan_critic.md" | grep -E -q 'Skip.{0,80}debug_fix'; then
  fail "plan_critic.md must skip debug_fix"
fi
# Normal is main thread, not a spawn.
has 'main-thread too' "$FD/GRAPH.md"
if ! grep -F -q 'Spawning plan_critic on every full_feature' "$FD/GRAPH.md"; then
  fail "GRAPH.md must forbid spawning plan_critic on every full_feature"
fi
ok plan-critic-gated

# --- Walk line in chat ---

has 'Walk:' "$FD/VOICE.md"
grep -F -q '✓' "$FD/VOICE.md" || fail "$FD/VOICE.md missing done mark"
grep -F -q '●' "$FD/VOICE.md" || fail "$FD/VOICE.md missing current mark"
grep -F -q '○' "$FD/VOICE.md" || fail "$FD/VOICE.md missing later mark"
has 'Walk:' "$FD/TOKEN_ECONOMY.md"
ok walk-line

echo "all passed"
