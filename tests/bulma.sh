#!/usr/bin/env bash
# Bulma: catalog vs graph enums, threshold math, ledger, inventory. Text and
# replay fixtures only. No network.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SKILL="$ROOT/skills/bulma"
BULMA="$SKILL/scripts/bulma.py"
FIX="$ROOT/tests/fixtures/bulma"

fail() { echo "FAIL: $*" >&2; exit 1; }
ok() { echo "ok $*"; }
need() { [[ -f "$1" ]] || fail "missing $1"; }
jget() { python3 -c 'import json,sys; d=json.load(open(sys.argv[1]))
for k in sys.argv[2].split("."):
    d = d[int(k)] if isinstance(d, list) else d[k]
print(d if not isinstance(d, bool) else str(d).lower())' "$1" "$2"; }

TMP="$(mktemp -d "${TMPDIR:-/tmp}/bulma-test.XXXXXX")"
trap 'rm -rf "$TMP"' EXIT
export RUVER_HOME="$TMP/home"
RR="$TMP/root"
mkdir -p "$RUVER_HOME" "$RR"
unset BULMA_POWER TYPESAFE_API_KEY || true

need "$SKILL/decisions.json"
need "$SKILL/HOOKS.md"
need "$BULMA"

# --- catalog and checker ---
python3 "$BULMA" catalog >/dev/null || fail "bulma.py catalog rejects decisions.json"
python3 "$ROOT/tests/lib/check_bulma.py" "$ROOT" || fail "check_bulma.py"
ok catalog

# --- power precedence: default < config < power_by_hook < env < flag ---
out="$(python3 "$BULMA" power)"
[[ "$out" == "balanced (default)" ]] || fail "default power: $out"
python3 "$BULMA" power set cautious >/dev/null
out="$(python3 "$BULMA" power)"
[[ "$out" == "cautious (config)" ]] || fail "config power: $out"
python3 - "$RUVER_HOME/bulma.json" <<'PY'
import json, sys
p = sys.argv[1]; cfg = json.load(open(p)); cfg["power_by_hook"] = {"fd.triage": "bold"}; json.dump(cfg, open(p, "w"))
PY
out="$(python3 "$BULMA" power --hook fd.triage)"
[[ "$out" == "bold (hook)" ]] || fail "hook power: $out"
out="$(BULMA_POWER=shadow python3 "$BULMA" power --hook fd.triage)"
[[ "$out" == "shadow (env)" ]] || fail "env power: $out"
out="$(BULMA_POWER=shadow python3 "$BULMA" power --hook fd.triage --power balanced)"
[[ "$out" == "balanced (flag)" ]] || fail "flag power: $out"
if python3 "$BULMA" power set loud >/dev/null 2>&1; then fail "power set accepted an unknown level"; fi
rm -f "$RUVER_HOME/bulma.json"
ok power-precedence

# --- ask --replay: balanced acts on .88, falls back on .61 ---
J="$TMP/ask.json"
python3 "$BULMA" ask fd.triage --state "$FIX/state-fd-triage.json" --replay "$FIX/replay-fd-triage.json" \
  --graph-answer path=debug_fix --graph-answer risk=normal --context repo=o/r --context ticket=DEV-4772 \
  --ruver-root "$RR" --json >"$J" || fail "ask fd.triage exit"
[[ "$(jget "$J" answers.path.act)" == "true" ]] || fail "balanced should act on path .88"
[[ "$(jget "$J" answers.path.choice)" == "debug_fix" ]] || fail "path choice"
[[ "$(jget "$J" answers.risk.act)" == "false" ]] || fail "balanced must not act on risk .61"
[[ "$(jget "$J" answers.risk.fallback)" == "ROUTING.md heuristic" ]] || fail "risk fallback text"
[[ "$(jget "$J" power)" == "balanced" ]] || fail "power in output"
[[ "$(jget "$J" model)" == "jev-1.13.0" ]] || fail "model from response"
[[ "$(jget "$J" truncated)" == "false" ]] || fail "truncated flag"
ok ask-balanced

# --- cautious flips .78 on a .75 question; bold acts on .68 for a .80 question ---
python3 "$BULMA" ask fd.triage --state "$FIX/state-fd-triage.json" --replay "$FIX/replay-fd-triage-078.json" \
  --power cautious --ruver-root "$RR" --json >"$J" || fail "ask cautious exit"
[[ "$(jget "$J" answers.path.act)" == "false" ]] || fail "cautious must not act on .78 (act_at .85)"
[[ "$(jget "$J" answers.path.act_at)" == "0.85" ]] || fail "cautious act_at: $(jget "$J" answers.path.act_at)"
python3 "$BULMA" ask fd.triage --state "$FIX/state-fd-triage.json" --replay "$FIX/replay-fd-triage-078.json" \
  --power bold --ruver-root "$RR" --json >"$J" || fail "ask bold exit"
[[ "$(jget "$J" answers.risk.act)" == "false" ]] || fail "bold: risk .68 < act_at .70 must not act"
[[ "$(jget "$J" answers.risk.act_at)" == "0.7" ]] || fail "bold act_at for risk: $(jget "$J" answers.risk.act_at)"
[[ "$(jget "$J" answers.path.act)" == "true" ]] || fail "bold: path .78 >= .65 must act"
ok ask-power-offsets

# --- shadow never acts, records graph answers ---
python3 "$BULMA" ask fd.triage --state "$FIX/state-fd-triage.json" --replay "$FIX/replay-fd-triage.json" \
  --power shadow --graph-answer path=debug_fix --ruver-root "$RR" --json >"$J" || fail "ask shadow exit"
[[ "$(jget "$J" answers.path.act)" == "false" ]] || fail "shadow acted"
[[ "$(jget "$J" answers.work_kind.act)" == "false" ]] || fail "shadow acted on work_kind"
ok ask-shadow

# --- policy.ask: direction ask; important .72 decisive-yes at .65, uncertain .40 undecided ---
python3 "$BULMA" ask policy.ask --state "$FIX/state-policy-ask.json" --replay "$FIX/replay-policy-ask.json" \
  --ruver-root "$RR" --json >"$J" || fail "ask policy exit"
[[ "$(jget "$J" answers.important.decisive)" == "yes" ]] || fail "important decisive"
[[ "$(jget "$J" answers.uncertain.decisive)" == "undecided" ]] || fail "uncertain undecided: $(jget "$J" answers.uncertain.decisive)"
python3 "$BULMA" ask policy.ask --state "$FIX/state-policy-ask.json" --replay "$FIX/replay-policy-ask.json" \
  --power cautious --ruver-root "$RR" --json >"$J" || fail "ask policy cautious exit"
[[ "$(jget "$J" answers.important.act_at)" == "0.55" ]] || fail "ask direction: cautious must lower act_at to .55, got $(jget "$J" answers.important.act_at)"
[[ "$(jget "$J" answers.uncertain.decisive)" == "no" ]] || fail "uncertain .40 <= 1-.55 is decisive-no under cautious"
ok ask-policy-direction

# --- dynamic criteria ---
if python3 "$BULMA" ask entry.next_step --state "$FIX/state-fd-triage.json" --replay "$FIX/replay-next-step.json" --ruver-root "$RR" --json >/dev/null 2>&1; then
  fail "dynamic hook without --criteria must exit 4"
fi
python3 "$BULMA" ask entry.next_step --state "$FIX/state-fd-triage.json" --replay "$FIX/replay-next-step.json" \
  --criteria "$FIX/criteria-next-step.json" --ruver-root "$RR" --json >"$J" || fail "dynamic ask exit"
[[ "$(jget "$J" answers.candidate.choice)" == "resume:dev-4772" ]] || fail "dynamic choice"
[[ "$(jget "$J" answers.user_blocked.decisive)" == "yes" ]] || fail "user_blocked decisive"
python3 "$BULMA" ask entry.next_step --state "$FIX/state-fd-triage.json" --criteria "$FIX/criteria-next-step.json" --dry-run --ruver-root "$RR" >"$J" || fail "dry-run exit"
grep -F -q '"resume:dev-4772"' "$J" || fail "dry-run request lacks dynamic criteria"
grep -F -q '"model"' "$J" || fail "dry-run request lacks model"
ok ask-dynamic

# --- redaction and truncation ---
python3 "$BULMA" ask fd.triage --state "$FIX/state-secret.json" --dry-run --ruver-root "$RR" >"$J" || fail "dry-run secret exit"
grep -F -q '[redacted]' "$J" || fail "redaction marker missing"
if grep -F -q 'ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ0123' "$J"; then fail "token leaked into request"; fi
if grep -F -q 'hunter22' "$J"; then fail "password leaked into request"; fi
python3 - "$TMP/big.json" <<'PY'
import json, sys
json.dump({"goal": "x" * 20000, "ticket_title": "t", "ticket_body": "b", "acceptance_criteria": [], "topology": {}, "files_mentioned": [], "labels": []}, open(sys.argv[1], "w"))
PY
python3 "$BULMA" ask fd.triage --state "$TMP/big.json" --replay "$FIX/replay-fd-triage.json" --ruver-root "$RR" --json >"$J" || fail "big state exit"
[[ "$(jget "$J" truncated)" == "true" ]] || fail "truncated flag not set on 20k string"
ok redact-truncate

# --- ledger: header once, one row per question, 17 columns, no tabs in values ---
TSV="$RR/.ruver-bulma/DECISIONS.tsv"
need "$TSV"
python3 - "$TSV" <<'PY'
import sys
lines = open(sys.argv[1], encoding="utf-8").read().rstrip("\n").split("\n")
header = lines[0].split("\t")
assert header == ["ts_iso","decision_id","hook","question","power","model","answer","confidence","act_at","acted","graph_answer","outcome","repo","pr","sha","ticket","note"], header
assert lines.count(lines[0]) == 1, "header repeated"
rows = [l.split("\t") for l in lines[1:]]
assert all(len(r) == 17 for r in rows), [len(r) for r in rows]
# runs so far: fd.triage x5 (4 rows each) + policy.ask x2 (2 rows) + next_step x1 (2 rows) = 26
assert len(rows) == 26, len(rows)
first = rows[0]
assert first[2] == "fd.triage" and first[12] == "o/r" and first[15] == "DEV-4772", first
path_rows = [r for r in rows if r[2] == "fd.triage" and r[3] == "path"]
assert path_rows[0][10] == "debug_fix" and path_rows[0][9] == "true", path_rows[0]
shadow = [r for r in rows if r[4] == "shadow"]
assert shadow and all(r[9] == "false" for r in shadow), shadow
big = [r for r in rows if r[16] == "truncated"]
assert len(big) == 4, len(big)
PY
ok ledger

# --- doctor without key: exit 2, names the variable, never leaks a key ---
set +e
out="$(env -u TYPESAFE_API_KEY python3 "$BULMA" doctor 2>&1)"; code=$?
set -e
[[ "$code" -eq 2 ]] || fail "doctor without key must exit 2, got $code"
grep -F -q 'TYPESAFE_API_KEY' <<<"$out" || fail "doctor must name TYPESAFE_API_KEY"
grep -F -q '/developer, /qa, /reviewer, /lstm, /ruver-triage' <<<"$out" || fail "doctor must point at the plain graphs"
set +e
out="$(TYPESAFE_API_KEY=apikey_testtesttesttesttest python3 "$BULMA" doctor --offline 2>&1)"; code=$?
set -e
[[ "$code" -eq 0 ]] || fail "doctor --offline with a key must exit 0, got $code: $out"
if grep -F -q 'apikey_testtesttesttesttest' <<<"$out"; then fail "doctor printed the key"; fi
grep -F -q 'catalog  ok (9 hooks)' <<<"$out" || fail "doctor catalog line: $out"
ok doctor

# --- tune and model write config; ask reads the override ---
python3 "$BULMA" tune fd.triage.path 0.60 >/dev/null || fail "tune exit"
if python3 "$BULMA" tune fd.triage.path 0.30 >/dev/null 2>&1; then fail "tune accepted 0.30"; fi
if python3 "$BULMA" tune nope.path 0.60 >/dev/null 2>&1; then fail "tune accepted an unknown question"; fi
python3 "$BULMA" model set jev-1.13.0 >/dev/null || fail "model set exit"
out="$(python3 "$BULMA" model)"
[[ "$out" == "jev-1.13.0 (config)" ]] || fail "model read: $out"
python3 "$BULMA" ask fd.triage --state "$FIX/state-fd-triage.json" --replay "$FIX/replay-fd-triage.json" \
  --power cautious --ruver-root "$RR" --json >"$J" || fail "ask with tune exit"
[[ "$(jget "$J" answers.path.act_at)" == "0.7" ]] || fail "tuned .60 + cautious .10 must be .70, got $(jget "$J" answers.path.act_at)"
python3 "$BULMA" ask fd.triage --state "$FIX/state-fd-triage.json" --replay "$FIX/replay-fd-triage.json" \
  --ruver-root "$RR" --dry-run >"$J" || fail "dry-run model exit"
grep -F -q '"jev-1.13.0"' "$J" || fail "pinned model not in request"
rm -f "$RUVER_HOME/bulma.json"
ok tune-model

# --- outcome rewrites one row ---
DID="$(python3 - "$TSV" <<'PY'
import sys
rows = [l.split("\t") for l in open(sys.argv[1], encoding="utf-8").read().splitlines()[1:]]
print(rows[0][1])
PY
)"
python3 "$BULMA" outcome "$DID" work_kind reversed --note "was a feature" --ruver-root "$RR" >/dev/null || fail "outcome exit"
if python3 "$BULMA" outcome "$DID" nope reversed --ruver-root "$RR" >/dev/null 2>&1; then fail "outcome accepted an unknown question"; fi
python3 - "$TSV" "$DID" <<'PY'
import sys
rows = [l.split("\t") for l in open(sys.argv[1], encoding="utf-8").read().splitlines()[1:]]
hit = [r for r in rows if r[1] == sys.argv[2] and r[3] == "work_kind"]
assert len(hit) == 1 and hit[0][11] == "reversed" and "was a feature" in hit[0][16], hit
assert sum(1 for r in rows if r[11] == "reversed") == 1
PY
ok outcome

# --- report: agree%, suggest, need >=20 ---
REP="$TMP/rep"
mkdir -p "$REP/.ruver-bulma"
python3 - "$REP/.ruver-bulma/DECISIONS.tsv" <<'PY'
import sys
cols = "ts_iso decision_id hook question power model answer confidence act_at acted graph_answer outcome repo pr sha ticket note".split()
rows = []
for i in range(24):
    conf = 0.55 + i * 0.018
    agree = i not in (0, 1)
    rows.append(["2026-09-%02dT10:00:00Z" % (1 + i % 28), "id%02d" % i, "fd.triage", "path", "balanced", "jev-1.13.0",
                 "debug_fix", "%.3f" % conf, "0.75", "true" if conf >= 0.75 else "false",
                 "debug_fix" if agree else "full_feature", "", "o/r", "", "", "", ""])
for i in range(5):
    rows.append(["2026-09-10T10:00:00Z", "q%d" % i, "qa.gate", "violates_pr_ac", "balanced", "jev-1.13.0", "0.9", "0.9", "0.85", "true", "", "", "o/r", "", "", "", ""])
open(sys.argv[1], "w").write("\t".join(cols) + "\n" + "".join("\t".join(r) + "\n" for r in rows))
PY
out="$(python3 "$BULMA" report --repo-only --ruver-root "$REP")"
grep -E -q '^\| fd\.triage\.path +\| 24 ' <<<"$out" || fail "report row for fd.triage.path: $out"
grep -E -q 'fd\.triage\.path .* 92% ' <<<"$out" || fail "agree% should be 92% (22/24): $out"
grep -E -q 'fd\.triage\.path .* 0\.6[05] ' <<<"$out" || fail "suggest should land at 0.60 or 0.65: $out"
grep -E -q 'qa\.gate\.violates_pr_ac .* need >=20' <<<"$out" || fail "short sample must say need >=20: $out"
ok report

# --- world.sh: candidates in rule order, gh stubbed on PATH ---
WORLD="$SKILL/scripts/world.sh"
need "$WORLD"
W="$TMP/world.json"
PATH="$FIX/bin:$PATH" bash "$WORLD" --ruver-root "$FIX/world" --out "$W" >/dev/null || fail "world.sh exit"
[[ "$(jget "$W" stack_top)" == "qa" ]] || fail "stack_top"
[[ "$(jget "$W" jobs.qa_active)" == "qa-pr-812" ]] || fail "qa_active"
[[ "$(jget "$W" user)" == "ruverd" ]] || fail "user login"
[[ "$(jget "$W" prs.0.unresolved_threads)" == "3" ]] || fail "unresolved threads for 805"
[[ "$(jget "$W" prs.1.qa_marker_on_head)" == "false" ]] || fail "qa marker for 812"
[[ "$(jget "$W" prs.2.ci)" == "red" ]] || fail "ci red for 799"
ids="$(python3 -c 'import json,sys; print(" ".join(c["id"] for c in json.load(open(sys.argv[1]))["candidates"]))' "$W")"
[[ "$ids" == "resume:dev-4772 lstm:pr-805 reviewer:pr-799 qa:pr-812 qa:qa-pr-790 nothing" ]] || fail "candidates order: $ids"
grep -F -q 'per user or per tenant' "$W" || fail "waiting_user question missing from candidate why"
need "$(dirname "$W")/candidates.json"
[[ "$(jget "$(dirname "$W")/candidates.json" candidate.nothing)" == "no open item, or start new work" ]] || fail "candidates.json shape"
PATH="$FIX/bin:$PATH" bash "$WORLD" --ruver-root "$FIX/world" --pr https://github.com/o/r/pull/805 --out "$W" >/dev/null || fail "world.sh --pr exit"
[[ "$(jget "$W" pr.author_is_user)" == "true" ]] || fail "pr.author_is_user"
[[ "$(jget "$W" pr.review_decision)" == "CHANGES_REQUESTED" ]] || fail "pr.review_decision"
PATH="$FIX/bin-broken:$(dirname "$(command -v python3)"):/usr/bin:/bin" bash "$WORLD" --ruver-root "$FIX/world" --out "$W" >/dev/null || fail "world.sh without gh must still exit 0"
[[ "$(jget "$W" prs)" == "None" ]] || fail "prs must be null without gh"
grep -F -q 'gh not found' "$W" || fail "warning about gh missing"
ids="$(python3 -c 'import json,sys; print(" ".join(c["id"] for c in json.load(open(sys.argv[1]))["candidates"]))' "$W")"
[[ "$ids" == "resume:dev-4772 qa:qa-pr-790 nothing" ]] || fail "state-only candidates: $ids"
[[ ! -e "$FIX/world/.ruver-bulma/world.json" ]] || fail "world.sh wrote into the fixture root despite --out"
ok world

# --- graph files and text invariants ---
for f in SKILL.md GRAPH.md STATE.schema.md ARGS.md POWER.md REQUIREMENTS.md templates/STATE.md \
         nodes/admit.md nodes/inventory.md nodes/route.md nodes/overlay.md nodes/done.md nodes/power.md nodes/report.md; do
  need "$SKILL/$f"
done
need "$ROOT/commands/bulma.md"
grep -F -q 'description: Jev-gated router and overlay for ruver graphs. Use when /bulma.' "$SKILL/SKILL.md" || fail "SKILL.md description must match the budgeted text"
grep -F -q 'category: graph' "$SKILL/SKILL.md" || fail "SKILL.md category"
grep -F -q 'doctor' "$SKILL/nodes/admit.md" || fail "admit must run doctor"
grep -F -q 'status: blocked' "$SKILL/nodes/admit.md" || fail "admit must block on doctor failure"
grep -F -q 'entry.route' "$SKILL/nodes/route.md" || fail "route must name entry.route"
grep -F -q 'entry.next_step' "$SKILL/nodes/route.md" || fail "route must name entry.next_step"
grep -F -q 'candidates.json' "$SKILL/nodes/route.md" || fail "route must pass candidates.json as --criteria"
grep -F -q -- '--graph-answer' "$SKILL/nodes/overlay.md" || fail "overlay must pass graph answers"
grep -F -q 'J:' "$SKILL/nodes/overlay.md" || fail "overlay must define the J: chat line"
grep -F -q 'never appears on the stack' "$SKILL/nodes/overlay.md" || fail "overlay must state bulma is not a bus frame"
grep -F -q 'shadow | cautious | balanced | bold' "$SKILL/POWER.md" || fail "POWER.md levels"
grep -F -q 'TYPESAFE_API_KEY' "$SKILL/REQUIREMENTS.md" || fail "REQUIREMENTS.md must name the key"
grep -F -q 'leaves the machine' "$SKILL/REQUIREMENTS.md" || fail "REQUIREMENTS.md must state data handling"
# shellcheck disable=SC2016  # literal $ARGUMENTS must not appear in the alias
if grep -F -q '$ARGUMENTS' "$ROOT/commands/bulma.md"; then fail "commands/bulma.md must not use \$ARGUMENTS"; fi
python3 "$ROOT/tests/lib/check_graphs.py" "$ROOT" || fail "check_graphs (bulma Need)"
ok graph-files

# --- entry.* under cautious/shadow never auto-routes, even above act_at ---
# 0.95 beats cautious act_at 0.85 (base 0.75 + 0.10). Without the entry.*
# judge gate this would act. Replay only.
python3 "$BULMA" ask entry.next_step --state "$FIX/state-fd-triage.json" --replay "$FIX/replay-next-step-095.json" \
  --criteria "$FIX/criteria-next-step.json" --power cautious --ruver-root "$RR" --json >"$J" || fail "ask entry cautious exit"
[[ "$(jget "$J" answers.candidate.act)" == "false" ]] || fail "cautious must not auto-route entry.next_step at .95"
[[ "$(jget "$J" answers.candidate.act_at)" == "0.85" ]] || fail "cautious entry act_at: $(jget "$J" answers.candidate.act_at)"
[[ "$(jget "$J" answers.user_blocked.decisive)" == "yes" ]] || fail "user_blocked decisive must stay yes under cautious"
python3 "$BULMA" ask entry.next_step --state "$FIX/state-fd-triage.json" --replay "$FIX/replay-next-step-095.json" \
  --criteria "$FIX/criteria-next-step.json" --power shadow --ruver-root "$RR" --json >"$J" || fail "ask entry shadow exit"
[[ "$(jget "$J" answers.candidate.act)" == "false" ]] || fail "shadow must not auto-route entry.next_step"
ok ask-entry-no-autoroute

echo "bulma gate: all green"
