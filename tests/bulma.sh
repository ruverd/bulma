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

# --- ledger: header once, one row per question, 19 columns, no tabs in values ---
TSV="$RR/.ruver-bulma/DECISIONS.tsv"
need "$TSV"
python3 - "$TSV" <<'PY'
import sys
lines = open(sys.argv[1], encoding="utf-8").read().rstrip("\n").split("\n")
header = lines[0].split("\t")
assert header == ["ts_iso","decision_id","hook","question","power","model","answer","confidence","act_at","acted","graph_answer","outcome","repo","pr","sha","ticket","note","input_tokens","latency_ms"], header
assert lines.count(lines[0]) == 1, "header repeated"
rows = [l.split("\t") for l in lines[1:]]
assert all(len(r) == 19 for r in rows), [len(r) for r in rows]
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
assert first[17] == "1412", first  # usage.input_tokens from the replay
assert all(r[18] == "" for r in rows), "replays carry no latency"
PY
ok ledger

# --- older 17-column ledger: report reads it, next ask migrates it ---
OLD="$TMP/old"
mkdir -p "$OLD/.ruver-bulma"
printf 'ts_iso\tdecision_id\thook\tquestion\tpower\tmodel\tanswer\tconfidence\tact_at\tacted\tgraph_answer\toutcome\trepo\tpr\tsha\tticket\tnote\n2026-09-01T10:00:00Z\told1\tfd.triage\tpath\tbalanced\tjev-1.13.0\tdebug_fix\t0.9\t0.75\ttrue\t\t\to/r\t\t\t\t\n' >"$OLD/.ruver-bulma/DECISIONS.tsv"
out="$(python3 "$BULMA" report --repo-only --ruver-root "$OLD")"
grep -E -q '^\| fd\.triage\.path +\| 1 ' <<<"$out" || fail "report must read a 17-column ledger: $out"
python3 "$BULMA" ask fd.triage --state "$FIX/state-fd-triage.json" --replay "$FIX/replay-fd-triage.json" --ruver-root "$OLD" --json >/dev/null || fail "ask on old ledger"
python3 - "$OLD/.ruver-bulma/DECISIONS.tsv" <<'PY'
import sys
lines = open(sys.argv[1], encoding="utf-8").read().splitlines()
assert lines[0].endswith("\tinput_tokens\tlatency_ms"), lines[0]
assert len(lines) == 6 and all(len(l.split("\t")) == 19 for l in lines), [len(l.split("\t")) for l in lines]
assert lines[1].split("\t")[1] == "old1"
PY
out="$(python3 "$BULMA" report --repo-only --ruver-root "$OLD")"
grep -F -q 'calls: 2 · input_tokens: 1412' <<<"$out" || fail "report cost line: $out"
ok ledger-migrate

# --- --line prints the overlay J: line ---
out="$(python3 "$BULMA" ask fd.triage --state "$FIX/state-fd-triage.json" --replay "$FIX/replay-fd-triage.json" --ruver-root "$RR" --line)"
grep -E -q '^J: fd\.triage work_kind=bug \.91 ok · path=debug_fix \.88 ok · risk=elevated \.61 -> fallback · scope=backend_only \.79 ok \[[0-9TZ]+-fd\.triage-[0-9a-f]{4}\]$' <<<"$out" || fail "J line: $out"
out="$(python3 "$BULMA" ask policy.ask --state "$FIX/state-policy-ask.json" --replay "$FIX/replay-policy-ask.json" --power shadow --ruver-root "$RR" --line)"
grep -E -q '^J\(shadow\): policy\.ask important=yes \.72 -> fallback · uncertain=\? \.40 -> fallback' <<<"$out" || fail "shadow J line: $out"
ok ask-line

# --- ask-many: validates first, runs in parallel, one line per item, one ledger append ---
MR="$TMP/mroot"
python3 - "$TMP/batch.json" "$FIX" <<'PY'
import json, sys
fix = sys.argv[2]
json.dump({"context": {"repo": "o/r", "pr": "805"}, "items": [
    {"id": "c1", "hook": "fd.triage", "state": fix + "/state-fd-triage.json", "replay": fix + "/replay-fd-triage.json", "graph_answer": {"path": "debug_fix"}},
    {"id": "c2", "hook": "policy.ask", "state": json.load(open(fix + "/state-policy-ask.json")), "replay": fix + "/replay-policy-ask.json"},
    {"id": "c3", "hook": "entry.next_step", "state": fix + "/state-fd-triage.json", "criteria": fix + "/criteria-next-step.json", "replay": fix + "/replay-next-step.json"},
]}, open(sys.argv[1], "w"))
PY
out="$(python3 "$BULMA" ask-many --batch "$TMP/batch.json" --ruver-root "$MR")"
[[ "$(wc -l <<<"$out" | tr -d ' ')" == "3" ]] || fail "ask-many lines: $out"
grep -E -q '^c1 J: fd\.triage .*path=debug_fix \.88 ok' <<<"$out" || fail "ask-many c1: $out"
grep -E -q '^c2 J: policy\.ask important=yes \.72 ok' <<<"$out" || fail "ask-many c2: $out"
grep -E -q '^c3 J: entry\.next_step candidate=resume:dev-4772' <<<"$out" || fail "ask-many c3: $out"
python3 - "$MR/.ruver-bulma/DECISIONS.tsv" <<'PY'
import sys
rows = [l.split("\t") for l in open(sys.argv[1], encoding="utf-8").read().splitlines()[1:]]
assert len(rows) == 4 + 2 + 2, len(rows)
assert all(r[12] == "o/r" and r[13] == "805" for r in rows), "shared context"
assert [r[10] for r in rows if r[3] == "path"] == ["debug_fix"], "per-item graph_answer"
assert len({r[1] for r in rows}) == 3, "one decision id per item"
PY
python3 "$BULMA" ask-many --batch "$TMP/batch.json" --ruver-root "$MR" --json >"$J" || fail "ask-many --json"
[[ "$(jget "$J" 1.id)" == "c2" ]] || fail "ask-many --json keeps item order and ids"
python3 - "$TMP/bad.json" "$FIX" <<'PY'
import json, sys
fix = sys.argv[2]
json.dump([{"hook": "fd.triage", "state": fix + "/state-fd-triage.json", "replay": fix + "/replay-fd-triage.json"},
           {"hook": "entry.next_step", "state": fix + "/state-fd-triage.json"}], open(sys.argv[1], "w"))
PY
before="$(wc -l <"$MR/.ruver-bulma/DECISIONS.tsv")"
set +e; python3 "$BULMA" ask-many --batch "$TMP/bad.json" --ruver-root "$MR" >/dev/null 2>&1; code=$?; set -e
[[ "$code" -eq 4 ]] || fail "bad batch item must exit 4 before any ask, got $code"
[[ "$(wc -l <"$MR/.ruver-bulma/DECISIONS.tsv")" == "$before" ]] || fail "bad batch must not log anything"
ok ask-many

# --- dispatch.tier: shadow default, clamp, unmapped, escalate, reverse, gate ---
DR="$TMP/droot"
DT="$FIX/TICKETS-dispatch.md"
out="$(python3 "$BULMA" power --hook dispatch.tier)"
[[ "$out" == "shadow (hook default)" ]] || fail "dispatch.tier must default to shadow: $out"
python3 "$BULMA" power set cautious --hook dispatch.tier >/dev/null || fail "power set --hook exit"
[[ "$(python3 "$BULMA" power --hook dispatch.tier)" == "cautious (hook)" ]] || fail "power set --hook must write power_by_hook"
[[ "$(python3 "$BULMA" power)" == "balanced (default)" ]] || fail "power set --hook must not touch global power"
if python3 "$BULMA" power set cautious --hook nope.hook >/dev/null 2>&1; then fail "power set accepted unknown hook"; fi
python3 "$BULMA" power set shadow --hook dispatch.tier >/dev/null
python3 "$BULMA" dispatch plan --tickets "$DT" --risk normal --path full_feature --host claude \
  --replay "$FIX/replay-dispatch-light.json" --context repo=o/r --context pr=9 --ruver-root "$DR" --json >"$J" || fail "dispatch plan shadow exit"
[[ "$(jget "$J" 0.tier)" == "heavy" && "$(jget "$J" 0.clamp)" == "shadow" ]] || fail "shadow must run heavy"
[[ "$(jget "$J" 0.spawn)" == "inherit" ]] || fail "shadow spawn must inherit"
python3 "$BULMA" dispatch plan --tickets "$DT" --ticket 1 --risk normal --host claude --power balanced \
  --replay "$FIX/replay-dispatch-light.json" --ruver-root "$DR" --json >"$J" || fail "dispatch plan unmapped exit"
[[ "$(jget "$J" 0.tier)" == "heavy" && "$(jget "$J" 0.clamp)" == "unmapped" ]] || fail "unmapped tier must log heavy"
python3 "$BULMA" dispatch map claude light model=haiku >/dev/null
python3 "$BULMA" dispatch map claude standard model=sonnet >/dev/null
if python3 "$BULMA" dispatch map claude heavy model=opus >/dev/null 2>&1; then fail "heavy must not be mappable"; fi
if python3 "$BULMA" dispatch map claude light effort=low >/dev/null 2>&1; then fail "claude has no per-spawn effort"; fi
if python3 "$BULMA" dispatch map grok light model=grok-4.5 >/dev/null 2>&1; then fail "grok has no per-spawn model"; fi
python3 "$BULMA" dispatch map codex light model=gpt-6-luna effort=low >/dev/null || fail "codex takes model and effort per spawn"
out="$(python3 "$BULMA" dispatch map codex)"
grep -F -q 'codex light: effort=low model=gpt-6-luna' <<<"$out" || fail "codex map print: $out"
python3 "$BULMA" dispatch plan --tickets "$DT" --risk normal --path full_feature --host claude --power balanced \
  --files src/inbox/Empty.tsx --replay "$FIX/replay-dispatch-light.json" --context pr=9 --ruver-root "$DR" --json >"$J" || fail "dispatch plan live exit"
[[ "$(jget "$J" 0.tier)" == "light" && "$(jget "$J" 0.spawn)" == "model=haiku" ]] || fail "ticket 1 light on haiku"
[[ "$(jget "$J" 1.tier)" == "standard" && "$(jget "$J" 1.clamp)" == "risk" ]] || fail "auth/session path must clamp light to standard"
[[ "$(jget "$J" 2.tier)" == "light" ]] || fail "ticket 3 light with --files fallback"
U1="$(jget "$J" 0.unit_id)"
python3 "$BULMA" dispatch plan --tickets "$DT" --ticket 3 --risk elevated --host claude --power balanced \
  --replay "$FIX/replay-dispatch-light.json" --ruver-root "$DR" --json >"$TMP/elev.json" || fail "dispatch plan elevated exit"
[[ "$(jget "$TMP/elev.json" 0.tier)" == "standard" ]] || fail "risk=elevated must clamp light"
python3 "$BULMA" dispatch plan --tickets "$DT" --ticket 3 --host claude --power balanced \
  --replay "$FIX/replay-dispatch-unsure.json" --ruver-root "$DR" --json >"$TMP/unsure.json" || fail "dispatch plan unsure exit"
[[ "$(jget "$TMP/unsure.json" 0.tier)" == "heavy" && "$(jget "$TMP/unsure.json" 0.clamp)" == "undecided" ]] || fail ".62 < .80 must run heavy"
if python3 "$BULMA" dispatch plan --tickets "$DT" --ticket 9 --ruver-root "$DR" >/dev/null 2>&1; then fail "unknown ticket id accepted"; fi
out="$(python3 "$BULMA" dispatch role tester --host claude)"
[[ "$out" == "role tester tier=heavy spawn=inherit" ]] || fail "role under shadow: $out"
out="$(python3 "$BULMA" dispatch role tester --host claude --power balanced)"
[[ "$out" == "role tester tier=light spawn=model=haiku" ]] || fail "tester light: $out"
out="$(python3 "$BULMA" dispatch role reviewer --host claude --power bold)"
[[ "$out" == "role reviewer tier=heavy spawn=inherit" ]] || fail "gates stay heavy: $out"
out="$(python3 "$BULMA" dispatch result "$U1" fail --stage test --tokens 12000 --host claude --ruver-root "$DR")"
grep -F -q 'tier=standard spawn=model=sonnet loops=1' <<<"$out" || fail "fail must escalate light->standard: $out"
out="$(python3 "$BULMA" dispatch result "$U1" fail --stage review --host claude --ruver-root "$DR")"
grep -F -q 'tier=heavy spawn=inherit loops=2' <<<"$out" || fail "second fail must escalate to heavy: $out"
python3 "$BULMA" dispatch result "$U1" pass --tokens 3000 --ruver-root "$DR" >/dev/null || fail "dispatch result pass"
python3 "$BULMA" dispatch reverse --file src/auth/session.ts --pr 9 --source qa --ruver-root "$DR" >"$TMP/rev.out" || fail "dispatch reverse"
grep -F -q 'reversed 2 unit(s) from qa' "$TMP/rev.out" || fail "reverse by file+pr: $(cat "$TMP/rev.out")"
python3 - "$DR/.ruver-bulma/DISPATCH.tsv" "$DR/.ruver-bulma/DECISIONS.tsv" "$U1" <<'PY'
import sys
units = [dict(zip(open(sys.argv[1]).readline().rstrip("\n").split("\t"), l.split("\t"))) for l in open(sys.argv[1]).read().splitlines()[1:]]
u = [r for r in units if r["unit_id"] == sys.argv[3]][0]
assert u["first_pass"] == "no" and u["loops_used"] == "2" and u["escalated_to"] == "heavy", u
assert u["worker_tokens"] == "15000" and u["outcome"] == "reversed", u
assert u["criteria_version"] == "1" and u["state"].endswith(".json"), u
shadow_auth = [r for r in units if r["power"] == "shadow" and r["ticket"] == "2"]
assert shadow_auth and shadow_auth[0]["outcome"] == "reversed", shadow_auth
decisions = [l.split("\t") for l in open(sys.argv[2]).read().splitlines()[1:]]
rev = [r for r in decisions if r[11] == "reversed"]
# U1 escalation + live ticket 2 late reverse; the shadow unit never touches DECISIONS outcome
assert len(rev) == 2 and all(r[2] == "dispatch.tier" and r[10] == "heavy" for r in rev), rev
PY
out="$(python3 "$BULMA" dispatch report --repo-only --ruver-root "$DR")"
grep -E -q '^\| 1 \| live \| light \| ' <<<"$out" || fail "report light row: $out"
grep -F -q 'clamped light->standard on risk: 2' <<<"$out" || fail "report clamp count: $out"
grep -F -q 'gate: live, 2/30 light units; keep collecting' <<<"$out" || fail "report gate: $out"
out="$(python3 "$BULMA" dispatch review --repo-only --ruver-root "$DR")"
grep -F -q "$U1" <<<"$out" || fail "review must list the escalated unit"
# gate math on a synthetic shadow ledger: 30 labelled, light passes as often as heavy
GR="$TMP/groot"; mkdir -p "$GR/.ruver-bulma"
PYTHONDONTWRITEBYTECODE=1 python3 - "$GR/.ruver-bulma/DISPATCH.tsv" "$SKILL/scripts" <<'PY'
import sys
sys.path.insert(0, sys.argv[2]); import dispatch
rows = []
for i in range(40):
    tier = "light" if i < 30 else "heavy"
    rows.append({"ts_iso": "2026-09-20T10:00:00Z", "unit_id": "g%d" % i, "tier_jev": tier, "tier_run": "heavy",
                 "power": "shadow", "first_pass": "yes" if i % 10 else "no", "loops_used": "0", "criteria_version": "1"})
import bulma
bulma.write_rows(sys.argv[1], rows, dispatch.COLUMNS)
PY
out="$(python3 "$BULMA" dispatch report --repo-only --ruver-root "$GR")"
grep -F -q 'gate: ready for cautious (Jev-light first pass 90% >= heavy 90%)' <<<"$out" || fail "shadow gate ready: $out"
rm -f "$RUVER_HOME/bulma.json"
ok dispatch-tier

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
grep -F -q 'catalog  ok (10 hooks)' <<<"$out" || fail "doctor catalog line: $out"
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

# --- watch.py: every workspace, terminal dropped, gh reconcile, orphan ---
WATCH="$SKILL/scripts/watch.py"
WH="$TMP/watch-home"
WTREE="$TMP/wt/live"
mkdir -p "$WTREE"
mkstate() {  # workspace graph age_hours body
  mkdir -p "$WH/$1/.ruver-$2"
  printf '%s\n' "$4" >"$WH/$1/.ruver-$2/STATE.md"
  touch -t "$(python3 -c 'import sys,time; print(time.strftime("%Y%m%d%H%M", time.localtime(time.time()-float(sys.argv[1])*3600)))' "$3")" "$WH/$1/.ruver-$2/STATE.md"
}
mkstate ws-merged feature-delivery 72 $'---\nstatus: ci_watching\npr_url: https://github.com/o/r/pull/1\n---'
mkstate ws-stuck lstm 72 $'# LSTM STATE\n\nstatus: patching\npr_url: https://github.com/o/r/pull/2\nworktree: '"$WTREE"$'\n\n## Dispositions'
mkstate ws-done reviewer 72 $'# Reviewer STATE\n\nstatus: done\npr_url: https://github.com/o/r/pull/3'
mkstate ws-mirror developer 72 $'---\nstatus: done\npr_url: https://github.com/o/r/pull/4\n---'
mkstate ws-mirror feature-delivery 72 $'---\nstatus: shipping\n---'
mkstate ws-fresh lstm 1 $'---\nstatus: patching\npr_url: https://github.com/o/r/pull/5\n---'
mkstate ws-ask developer 1 $'---\nstatus: waiting_user\nwaiting_user: Which tenant?\nworktree: '"$WTREE"$'\n---'
mkstate ws-gone qa 72 $'---\nstatus: qa_execute\npr_url: https://github.com/o/r/pull/6\nworktree: /nonexistent/wt\n---'
mkdir -p "$TMP/watch-bin"
cat >"$TMP/watch-bin/gh" <<'SH'
#!/usr/bin/env bash
echo "$3" >>"$(dirname "$0")/calls"
case "$3" in
  */pull/1) echo '{"state":"MERGED","isDraft":false,"mergeable":"UNKNOWN","statusCheckRollup":[]}' ;;
  *) echo '{"state":"OPEN","isDraft":true,"mergeable":"MERGEABLE","statusCheckRollup":[{"conclusion":"FAILURE"}]}' ;;
esac
SH
chmod +x "$TMP/watch-bin/gh"
out="$(PATH="$TMP/watch-bin:$PATH" python3 "$WATCH" --home "$WH" --json)"
bucket() { python3 -c 'import json,sys; d=json.loads(sys.argv[1]); print({w["workspace"]: w["bucket"] for w in d["workspaces"]}.get(sys.argv[2], "absent"))' "$out" "$1"; }
[[ "$(bucket ws-merged)" == "closed" ]] || fail "watch: merged PR must reconcile to closed"
[[ "$(bucket ws-stuck)" == "stalled" ]] || fail "watch: old live job must be stalled"
[[ "$(bucket ws-done)" == "absent" ]] || fail "watch: terminal STATE without frontmatter must drop"
[[ "$(bucket ws-mirror)" == "absent" ]] || fail "watch: fd mirror after developer done must drop"
[[ "$(bucket ws-fresh)" == "absent" ]] || fail "watch: recent write is not stalled"
[[ "$(bucket ws-ask)" == "needs_you" ]] || fail "watch: waiting_user is needs_you at any age"
[[ "$(bucket ws-gone)" == "orphaned" ]] || fail "watch: missing worktree is orphaned"
grep -F -q "CI red: cd $WTREE && /bulma https://github.com/o/r/pull/2" <<<"$out" || fail "watch: next step for red CI: $out"
grep -F -q '"https://github.com/o/r/pull/1": "MERGED"' "$WH/bulma-watch.json" || fail "watch: closed PR must be cached"
: >"$TMP/watch-bin/calls"
PATH="$TMP/watch-bin:$PATH" python3 "$WATCH" --home "$WH" >/dev/null
! grep -F -q '/pull/1' "$TMP/watch-bin/calls" || fail "watch: cached closed PR must skip gh"
out="$(PATH="/nonexistent:$PATH" python3 "$WATCH" --home "$WH" --summary)"
[[ "$out" == "watch: 1 need you, 1 stalled, 1 orphaned elsewhere (/bulma watch)" ]] || fail "watch summary: $out"
ok watch

# --- world.sh: frontmatter-less STATE, closed PRs from the watch cache ---
WL="$TMP/wl-home/slug"
mkdir -p "$WL/.ruver-reviewer" "$WL/.ruver-lstm" "$WL/.ruver-developer"
printf '# Reviewer STATE\n\nstatus: escalated\npr_url: https://github.com/o/r/pull/9\njob_id: rev-pr-9\n\n## Notes\nstatus: waiting_user\n' >"$WL/.ruver-reviewer/STATE.md"
printf '# LSTM STATE\n\nstatus: done\njob_id: lstm-pr-8\n' >"$WL/.ruver-lstm/STATE.md"
printf -- '---\nstatus: waiting_user\npr_url: https://github.com/o/r/pull/7\njob_id: dev-7\n---\n' >"$WL/.ruver-developer/STATE.md"
printf '{"closed": {"https://github.com/o/r/pull/7": "MERGED"}}' >"$TMP/wl-home/bulma-watch.json"
W2="$TMP/wl.json"
PATH="$FIX/bin-broken:$(dirname "$(command -v python3)"):/usr/bin:/bin" bash "$WORLD" --ruver-root "$WL" --out "$W2" >/dev/null || fail "world.sh legacy exit"
python3 - "$W2" <<'PY' || fail "world.sh legacy STATE / closed cache"
import json, sys
w = json.load(open(sys.argv[1]))
st = {s["graph"]: s["status"] for s in w["states"]}
assert st["reviewer"] == "escalated", st   # first key wins, section text ignored
assert st["lstm"] == "done", st
ids = [c["id"] for c in w["candidates"]]
assert ids == ["resume:rev-pr-9", "nothing"], ids   # dev-7's PR merged upstream
PY
ok world-legacy

# --- lookback.py: windows, per-PR trend, human filter, claim_true drop ---
LB="$SKILL/scripts/lookback.py"
LO="$TMP/obs.jsonl"
python3 - "$LO" <<'PY'
import json, sys
rows = []
def add(i, day, pattern, reviewer="alice", **kw):
    row = dict(id="gh-%d" % i, pr_ref="o/r#%d" % i, reviewer=reviewer, timestamp=day + "T10:00:00Z",
               generalized_pattern=pattern, caught_by_ours="no", severity_inferred="important",
               context_keywords=["kw"])
    row.update(kw)
    rows.append(row)
for i in range(20):   # previous window: 20 PRs, 2 sibling misses
    add(100 + i, "2026-08-10", "Guard added on one path, sibling path lacks it" if i < 2 else "Unrelated naming nit")
for i in range(10):   # current window: 10 PRs, 5 sibling misses
    add(200 + i, "2026-09-10", "Guard added on one path, sibling path lacks it" if i < 5 else "Unrelated naming nit")
add(300, "2026-09-11", "Guard added on one path, sibling path lacks it", reviewer="coderabbitai[bot]")
add(301, "2026-09-11", "Guard added on one path, sibling path lacks it", claim_true="no")
add(302, "2026-09-11", "Guard added on one path, sibling path lacks it", caught_by_ours="yes")
with open(sys.argv[1], "w") as fh:
    fh.write("\n".join(json.dumps(r) for r in rows) + "\nnot json\n")
PY
out="$(python3 "$LB" --file "$LO" --since 2026-09-01 --until 2026-09-30 --json)"
python3 - "$out" <<'PY' || fail "lookback json: $out"
import json, sys
d = json.loads(sys.argv[1])
assert d["previous"] == ["2026-08-02", "2026-08-31"], d["previous"]
assert d["prs"] == 12 and d["missed"] == 10, (d["prs"], d["missed"])   # bot dropped; 301 and 302 PRs count, not misses
row = next(c for c in d["clusters"] if c["cluster"] == "sibling-path parity")
assert row["obs"] == 5 and row["trend"] == "up", row
assert row["guard"] == "ruver-code-review Phase 5", row
PY
out="$(python3 "$LB" --file "$LO" --since 7 --until 2026-09-12)"
grep -F -q 'lookback 2026-09-06..2026-09-12 vs 2026-08-30..2026-09-05' <<<"$out" || fail "lookback day-count window: $out"
grep -F -q 'need data' <<<"$out" || fail "lookback: empty previous window must say need data"
out="$(python3 "$LB" --file "$TMP/missing.jsonl")"
grep -F -q 'no observations' <<<"$out" || fail "lookback without file: $out"
rc=0; python3 "$LB" --file "$LO" --since yesterday >/dev/null 2>&1 || rc=$?
[[ "$rc" == "4" ]] || fail "lookback bad --since must exit 4 (rc=$rc)"
ok lookback

# --- state builders: entry.* from world.json, review.risk and failure_class from gh JSON ---
SR="$TMP/sroot"
PATH="$FIX/bin:$PATH" bash "$WORLD" --ruver-root "$FIX/world" --out "$W" >/dev/null || fail "world.sh for builders"
out="$(python3 "$BULMA" state entry.route --args "review https://github.com/o/r/pull/805" --world "$W" --ruver-root "$SR")"
[[ -f "$out" && "$out" == */sroot/.ruver-bulma/state/entry.route-*.json ]] || fail "state path: $out"
[[ "$(jget "$out" world.stack_top)" == "qa" ]] || fail "entry.route world.stack_top"
[[ "$(jget "$out" user_login)" == "ruverd" ]] || fail "entry.route user_login"
python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); w=d["world"]; assert "prs" not in w and "candidates" not in w, w; assert set(w["states"][0]) == {"graph","status","waiting_user"}' "$out" || fail "entry.route world trim"
paths="$(python3 "$BULMA" state entry.next_step --resume --world "$W" --ruver-root "$SR")"
[[ "$(wc -l <<<"$paths" | tr -d ' ')" == "2" ]] || fail "next_step prints state and criteria: $paths"
crit="$(tail -1 <<<"$paths")"
[[ "$(python3 -c 'import json,sys; print(" ".join(json.load(open(sys.argv[1]))["candidate"]))' "$crit")" == "resume:dev-4772" ]] || fail "resume filters criteria"
out="$(python3 "$BULMA" state review.risk --pr-json "$FIX/pr-805.json" --ruver-root "$SR")"
[[ "$(jget "$out" churn)" == "140" ]] || fail "review.risk churn"
[[ "$(jget "$out" files.1)" == "api/inbox.py" ]] || fail "review.risk files"
out="$(python3 "$BULMA" state reviewer.failure_class --pr-json "$FIX/pr-805.json" --check-name test --log-file "$FIX/ci-fail.log" --ruver-root "$SR")"
[[ "$(jget "$out" mergeable)" == "MERGEABLE" ]] || fail "failure_class mergeable"
[[ "$(jget "$out" same_fail_on_base)" == "unknown" ]] || fail "failure_class same_fail_on_base default"
python3 -c 'import json,sys; t=json.load(open(sys.argv[1]))["log_tail"].splitlines(); assert len(t) == 200 and t[-1] == "line 260: FAILED test_inbox", t[-1]' "$out" || fail "log_tail keeps last 200 lines"
if python3 "$BULMA" state qa.gate --ruver-root "$SR" >/dev/null 2>&1; then fail "qa.gate has no builder and must exit 4"; fi
python3 "$BULMA" ask review.risk --build --pr-json "$FIX/pr-805.json" --ruver-root "$SR" --dry-run >"$J" || fail "ask --build dry-run"
grep -F -q '"churn": 140' "$J" || fail "ask --build sends the built state"
if python3 "$BULMA" ask review.risk --build --state "$FIX/state-fd-triage.json" --ruver-root "$SR" --dry-run >/dev/null 2>&1; then fail "--build with --state must exit 4"; fi
ok state-builders

# --- graph files and text invariants ---
for f in SKILL.md GRAPH.md STATE.schema.md ARGS.md POWER.md DISPATCH.md REQUIREMENTS.md templates/STATE.md \
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
grep -F -q 'spawn=inherit' "$SKILL/nodes/overlay.md" || fail "overlay must forbid model picks outside dispatch"
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
