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

echo "bulma gate: all green"
