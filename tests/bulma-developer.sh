#!/usr/bin/env bash
# Developer P0+P1: risk axis, split review verdicts, resume invariants,
# gated plan_critic, Walk line. Text fixtures only. No network.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FD="$ROOT/skills/bulma-feature-delivery"
DEV="$ROOT/skills/bulma-developer"

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
need "$FD/scripts/status-walk.sh"
need "$FD/IMPLEMENTATION.md"
need "$FD/nodes/evidence.md"
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
has 'Expert gap' "$FD/nodes/plan_critic.md"
has 'Proof oracle' "$FD/nodes/plan_critic.md"
has 'spawn' "$FD/nodes/plan_critic.md"
# The critic sees artifact + contract, never the conclusion, and every row is
# reconciled against the text before it counts.
has 'never the conclusion' "$FD/nodes/plan_critic.md"
has '## Reconcile' "$FD/nodes/plan_critic.md"
for class in contract fix trade-off noise; do
  has "**$class**" "$FD/nodes/plan_critic.md"
done
# Second opinion: opt-in, another vendor, stdin, read-only, never a silent skip.
has 'second_opinion: off | ran | failed' "$FD/nodes/plan_critic.md"
has 'second_opinion` | off \| ran \| failed' "$FD/STATE.schema.md"
has 'second_opinion:' "$FD/templates/STATE.md"
has 'second_opinion:' "$ROOT/skills/bulma-memory/SKILL.md"
has '## Second opinion' "$ROOT/skills/bulma-host/SKILL.md"
has 'SECOND_OPINION.md' "$ROOT/skills/bulma-host/SKILL.md"
has 'different vendor' "$ROOT/skills/bulma-host/references/SECOND_OPINION.md"
has 'Read-only mode is required' "$ROOT/skills/bulma-host/references/SECOND_OPINION.md"
has 'Never skip it silently' "$FD/nodes/plan_critic.md"
# Floor guard: first tester command, exit 2 is never a pass, reviewer runs it too.
has 'floor-guard.py' "$FD/nodes/tester.md"
has 'never as a pass' "$FD/nodes/tester.md"
has 'Floor guard:' "$FD/templates/STATE.md"
has 'floor-guard.py' "$ROOT/skills/bulma-code-review/references/EVIDENCE.md"
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

# --- status-walk.sh projection ---

WALK="$FD/scripts/status-walk.sh"
TMP="$(mktemp "${TMPDIR:-/tmp}/bulma-walk.XXXXXX")"
trap 'rm -f "$TMP"' EXIT
cat >"$TMP" <<'EOF'
---
status: ticketing
path: full_feature
risk: elevated
branch: feature/dev-1
current_ticket: "1"
---
# body
EOF
out="$(bash "$WALK" "$TMP")"
echo "$out" | grep -F -q 'path     full_feature' || fail "walk missing path ($out)"
echo "$out" | grep -F -q 'risk     elevated' || fail "walk missing risk ($out)"
echo "$out" | grep -F -q '●tickets' || fail "walk should mark tickets current ($out)"
echo "$out" | grep -F -q '○plan_critic' || fail "elevated full_feature walk must include plan_critic ($out)"
echo "$out" | grep -F -q '✓grill' || fail "walk should mark grill done ($out)"

cat >"$TMP" <<'EOF'
---
status: implementing
path: full_feature
risk: low
branch: feature/dev-1
---
EOF
out="$(bash "$WALK" "$TMP")"
if echo "$out" | grep -F -q 'plan_critic'; then
  fail "low-risk full_feature walk must skip plan_critic ($out)"
fi
echo "$out" | grep -F -q '●implement' || fail "walk should mark implement current ($out)"

cat >"$TMP" <<'EOF'
---
status: testing
path: light_change
risk: elevated
branch: feature/dev-1
---
EOF
out="$(bash "$WALK" "$TMP")"
echo "$out" | grep -F -q '✓blast' || fail "elevated light_change walk must include prior blast ($out)"
if echo "$out" | grep -F -q 'plan_critic'; then
  fail "light_change walk must skip plan_critic ($out)"
fi
ok status-walk

# --- ticket After + last-loop fresh coder ---

has 'Ticket After' "$FD/nodes/evidence.md"
has 'after-ticket-' "$FD/nodes/evidence.md"
has 'risk=elevated' "$FD/IMPLEMENTATION.md"
grep -F -q 'fresh** coder' "$FD/IMPLEMENTATION.md" \
  || grep -F -q '**fresh** coder' "$FD/IMPLEMENTATION.md" \
  || fail "IMPLEMENTATION.md must fresh-coder the last review_fix_loops slot"
has 'status-walk.sh' "$ROOT/install.sh"
ok ticket-after-and-fresh-coder

# --- recurring lessons reach the coder and the fd reviewer ---
FDX="$ROOT/skills/bulma-feature-delivery"
grep -F -q 'lessons.py --repo' "$FDX/IMPLEMENTATION.md" || fail "IMPLEMENTATION.md must inject lessons.py output"
grep -F -q 'LESSONS.md' "$FDX/nodes/coder.md" || fail "coder.md must load LESSONS.md"
grep -F -q 'LESSONS.md' "$FDX/nodes/reviewer.md" || fail "fd reviewer must check LESSONS.md"
grep -F -q 'LESSONS.md' "$ROOT/agents/bulma-fd-coder.md" || fail "bulma-fd-coder agent must load LESSONS.md"
grep -c '^### ' "$FDX/LESSONS.md" | grep -q -v '^0$' || fail "LESSONS.md has no rules"
ok coder-lessons

grep -F -q '## Gotchas' "$FDX/IMPLEMENTATION.md" || fail "IMPLEMENTATION.md must inject project gotchas"
grep -F -q '## Checks' "$FDX/nodes/tester.md" || fail "tester must run project checks"
grep -F -q '## Rollout' "$FDX/templates/PR_BODY.md" || fail "PR body must have Rollout"
grep -F -q '## How to test' "$FDX/templates/PR_BODY.md" || fail "PR body must have How to test"
[[ "$(grep '^## ' "$FDX/templates/PR_BODY.md" | tail -1)" == '## Agent run' ]] || fail "PR body must end with Agent run"
grep -F -q 'session_usage' "$ROOT/skills/bulma-host/SKILL.md" || fail "bulma-host must define session_usage"
for rule in 'untested branch' 'null / empty / boundary' 'silent catch / no error report' 'reuse before adding' 'test wired into CI'; do
  grep -F -q "### $rule" "$FDX/LESSONS.md" || fail "LESSONS.md missing $rule"
done
ok project-gotchas-and-checks

# project memory is shared by every worktree of a repo
MEM="$ROOT/skills/bulma-memory/SKILL.md"
snippet="$(awk '/^main=\$\(git worktree list/{p=1} p{print} /^BULMA_REPO=/{exit}' "$MEM")"
[[ -n "$snippet" ]] || fail "bulma-memory must define BULMA_REPO from the main worktree"
MW="$(mktemp -d "${TMPDIR:-/tmp}/bulma-mem.XXXXXX")"
git init -q -b main "$MW/repo"
git -C "$MW/repo" -c user.name=t -c user.email=t@t commit -q --allow-empty -m init
git -C "$MW/repo" worktree add -q "$MW/task" -b task
repo_of() { (cd "$1" && export BULMA_HOME=/h && eval "$snippet" && printf '%s' "$BULMA_REPO"); }
[[ "$(repo_of "$MW/repo")" == "$(repo_of "$MW/task")" ]] || fail "worktree resolves a different BULMA_REPO"
[[ "$(repo_of "$MW/task")" == /h/*repo ]] || fail "BULMA_REPO must be the main clone's slug: $(repo_of "$MW/task")"
rm -rf "$MW"
ok memory-shared-across-worktrees

echo "all passed"

PYTHONDONTWRITEBYTECODE=1 python3 "$ROOT/tests/lib/test_feature_flow.py"
