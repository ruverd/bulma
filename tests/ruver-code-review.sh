#!/usr/bin/env bash
# Spec-first, patch bind, and high-risk critic. No network.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SKILL="$ROOT/skills/ruver-code-review"
BIND="$SKILL/scripts/bind-findings.py"
RISK="$SKILL/scripts/classify-risk.py"
REVIEWER="$ROOT/skills/ruver-reviewer"

fail() { echo "FAIL: $*" >&2; exit 1; }
ok() { echo "ok  $*"; }

[[ -f "$BIND" ]] || fail "missing $BIND"
[[ -f "$RISK" ]] || fail "missing $RISK"
[[ -f "$SKILL/nodes/critic.md" ]] || fail "missing nodes/critic.md"

TMP="$(mktemp -d "${TMPDIR:-/tmp}/ruver-cr.XXXXXX")"
trap 'rm -rf "$TMP"' EXIT

assert_json() {
  local file="$1"
  local expr="$2"
  python3 - "$file" "$expr" <<'PY' || fail "json check: $expr ($file)"
import json, sys
data = json.load(open(sys.argv[1], encoding="utf-8"))
if not eval(sys.argv[2], {"d": data}):
    raise SystemExit(1)
PY
}

# --- classify-risk ---

assert_risk() {
  local want="$1"
  shift
  local got
  got="$(python3 "$RISK" "$@")"
  [[ "$got" == "$want" ]] || fail "classify-risk: want $want got $got ($*)"
}

assert_risk high src/auth/login.ts
assert_risk high src/db/migrations/001_init.sql
assert_risk high apps/api/src/billing/invoice.ts
assert_risk high src/sessionStorage.ts
assert_risk low src/author/page.tsx
assert_risk low src/components/Button.tsx
assert_risk low README.md

python3 "$RISK" --files-from /dev/null >"$TMP/empty.txt" || true
[[ "$(python3 "$RISK")" == "low" ]] || fail "classify-risk: no files should be low"

cat >"$TMP/FILES.txt" <<'EOF'
src/components/Button.tsx
src/author/page.tsx
EOF
assert_risk low --files-from "$TMP/FILES.txt"

cat >"$TMP/raw.patch" <<'EOF'
diff --git a/src/db.ts b/src/db.ts
--- a/src/db.ts
+++ b/src/db.ts
@@ -1,3 +1,4 @@
 export const db = {}
+  await prisma.$queryRaw`SELECT 1`
EOF
assert_risk high --files-from "$TMP/FILES.txt" --patch "$TMP/raw.patch"
assert_risk high docs/openapi.yaml
assert_risk high prisma/schema.prisma
assert_risk high src/sync/mutex.ts
assert_risk high --files-from "$TMP/FILES.txt" --churn 3000
assert_risk high --files-from "$TMP/FILES.txt" --changed-files 30
assert_risk low --files-from "$TMP/FILES.txt" --churn 10 --changed-files 2

cat >"$TMP/comment.patch" <<'EOF'
diff --git a/src/db.ts b/src/db.ts
--- a/src/db.ts
+++ b/src/db.ts
@@ -1,3 +1,3 @@
-  await prisma.$queryRaw`SELECT 1`
+  await prisma.user.findMany()
EOF
assert_risk low --files-from "$TMP/FILES.txt" --patch "$TMP/comment.patch"
ok classify-risk

# --- bind-findings ---

cat >"$TMP/sample.diff" <<'EOF'
diff --git a/src/x.ts b/src/x.ts
--- a/src/x.ts
+++ b/src/x.ts
@@ -40,6 +40,8 @@ export function retry() {
   const attempts = 1
   const cap = 3
+  fire(attempts)
   return attempts
 }
EOF

cat >"$TMP/findings.json" <<'EOF'
[
  {"severity":"blocker","path":"src/x.ts","line":42,"in_diff":true,"title":"in hunk"},
  {"severity":"major","path":"src/x.ts","line":99,"in_diff":true,"title":"outside hunk"},
  {"severity":"major","path":"src/y.ts","line":1,"in_diff":true,"title":"wrong file"},
  {"severity":"nit","path":"src/x.ts","line":42,"in_diff":false,"title":"flagged false"},
  {"severity":"major","path":"src/x.ts","title":"no line"}
]
EOF

python3 "$BIND" --patch "$TMP/sample.diff" --findings "$TMP/findings.json" >"$TMP/bound.json"
assert_json "$TMP/bound.json" "len(d['kept']) == 1 and d['kept'][0]['title'] == 'in hunk'"
assert_json "$TMP/bound.json" "len(d['dropped']) == 4"
ok bind-in-hunk

cat >"$TMP/carry.json" <<'EOF'
[{"severity":"blocker","path":"src/old.ts","line":10,"title":"carried"}]
EOF
python3 "$BIND" --patch "$TMP/sample.diff" --findings "$TMP/carry.json" \
  --allow-path src/old.ts >"$TMP/carry-bound.json"
assert_json "$TMP/carry-bound.json" "len(d['kept']) == 1"
python3 "$BIND" --patch "$TMP/sample.diff" --findings "$TMP/carry.json" >"$TMP/carry-drop.json"
assert_json "$TMP/carry-drop.json" "len(d['kept']) == 0"
ok bind-allow-path

cat >"$TMP/wrap.json" <<'EOF'
{"findings":[{"severity":"blocker","path":"src/x.ts","line":"42","in_diff":true,"title":"str line"}]}
EOF
python3 "$BIND" --patch "$TMP/sample.diff" --findings "$TMP/wrap.json" >"$TMP/wrap-bound.json"
assert_json "$TMP/wrap-bound.json" "len(d['kept']) == 1"
ok bind-wrapper

# --- skill contract ---

grep -q 'Do not Read product files until Phase 1' "$SKILL/nodes/fetch.md" \
  || fail "fetch.md must delay product-file Read until Phase 1"
grep -q 'classify-risk.py' "$SKILL/nodes/fetch.md" \
  || fail "fetch.md must run classify-risk.py"
grep -q 'Do not Read product files in this phase' "$SKILL/nodes/review.md" \
  || fail "review.md Phase 1 must run before product-file Read"
grep -q 'AC.md' "$SKILL/nodes/review.md" \
  || fail "review.md must write AC.md before Reads"
grep -q 'bind-findings.py' "$SKILL/nodes/review.md" \
  || fail "review.md Phase 10 must run bind-findings.py"
grep -q '4.3' "$SKILL/nodes/review.md" \
  || fail "review.md must call fetch §4.3 after the AC checklist"
grep -q 'spawn_worker' "$SKILL/nodes/critic.md" \
  || fail "critic.md must spawn_worker"
grep -q 'high-risk critic' "$SKILL/SKILL.md" \
  || fail "SKILL.md must name the high-risk critic exception"
if grep -q 'Single-PR stays on the main thread' "$SKILL/SKILL.md"; then
  fail "unqualified Single-PR main-thread rule blocks the critic"
fi
grep -q 'critic' "$SKILL/GRAPH.md" || fail "GRAPH.md must name critic"
grep -q 'publish' "$SKILL/GRAPH.md" || fail "GRAPH.md must name publish"
grep -q 'high-risk critic' "$REVIEWER/nodes/code_review.md" \
  || fail "reviewer code_review node must name the high-risk critic"
python3 - "$SKILL/nodes/review.md" <<'PY' || fail "Tests phase must run before Correctness"
import pathlib, sys
text = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
i_tests = text.find("### Phase 4 — Tests")
i_corr = text.find("### Phase 5 — Correctness")
if i_tests < 0 or i_corr < 0 or i_tests > i_corr:
    raise SystemExit(1)
PY
grep -q 'axis' "$SKILL/nodes/review.md" || fail "review.md must require axis on findings"
grep -q 'CONTRIBUTING.md' "$SKILL/nodes/review.md" \
  || fail "standards must read CONTRIBUTING.md when present"
grep -q 'Accessibility' "$SKILL/nodes/review.md" || fail "review.md must gate accessibility"
grep -q 'package.json' "$SKILL/nodes/review.md" || fail "review.md must gate dependencies"
grep -q 'Acceptance' "$SKILL/nodes/publish.md" || fail "publish.md must render Acceptance"
grep -q 'Contracts' "$SKILL/nodes/critic.md" || fail "critic.md must name the contracts lens"
grep -q 'Integration / state' "$SKILL/nodes/critic.md" \
  || fail "critic.md must name the integration lens"
grep -q 'Security / data loss' "$SKILL/nodes/critic.md" \
  || fail "critic.md must name the security lens"
grep -q 'Do not vote' "$SKILL/nodes/critic.md" || fail "critic.md must forbid voting findings off"
grep -q -- '--churn' "$SKILL/nodes/fetch.md" || fail "fetch.md must pass churn into classify-risk"
ok skill-contract

echo "all passed"
