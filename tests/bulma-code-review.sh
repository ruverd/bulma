#!/usr/bin/env bash
# Spec-first, patch bind, and high-risk critic. No network.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SKILL="$ROOT/skills/bulma-code-review"
BIND="$SKILL/scripts/bind-findings.py"
RISK="$SKILL/scripts/classify-risk.py"
REVIEWER="$ROOT/skills/bulma-reviewer"

fail() { echo "FAIL: $*" >&2; exit 1; }
ok() { echo "ok  $*"; }

[[ -f "$BIND" ]] || fail "missing $BIND"
[[ -f "$RISK" ]] || fail "missing $RISK"
[[ -f "$SKILL/nodes/critic.md" ]] || fail "missing nodes/critic.md"

TMP="$(mktemp -d "${TMPDIR:-/tmp}/bulma-cr.XXXXXX")"
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
assert_risk high .github/workflows/build.yml
assert_risk high terraform/environments/dev/main.tf
assert_risk high src/seatLimits.ts
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

python3 "$RISK" --human-signoff \
  .github/workflows/build.yml terraform/dev/main.tf infra/main.tf.json \
  src/auth/login.ts src/billing/plan.ts src/seatLimits.ts src/secrets.ts \
  .env.production keys/deploy.pem src/author/page.tsx src/secretary.ts \
  src/components/Button.tsx prisma/schema.prisma >"$TMP/human.json"
assert_json "$TMP/human.json" "len(d) == 9 and 'src/seatLimits.ts' in d and 'src/author/page.tsx' not in d and 'prisma/schema.prisma' not in d"
python3 "$RISK" --human-signoff --files-from "$TMP/FILES.txt" >"$TMP/no-human.json"
assert_json "$TMP/no-human.json" "d == []"
python3 "$RISK" --human-signoff infra/stack.yaml scripts/ci/apply-amplify-custom-rules.mjs \
  .github/actions/setup/action.yml Dockerfile amplify.yml .npmrc bunfig.toml apps/web/package.json \
  src/jobs/tasks/provider-subscription-reconcile.ts \
  src/services/identity-provider/oidc/oidc-saml-idp.service.ts \
  src/roles/guard.ts src/acl.ts >"$TMP/deploy-human.json"
assert_json "$TMP/deploy-human.json" "len(d) == 12"
python3 "$RISK" --human-signoff src/features/certification/CredentialCard.tsx \
  src/seats/__snapshots__/SeatPicker.test.tsx.snap e2e/seat-picker.png src/useAccessibility.ts >"$TMP/over.json"
assert_json "$TMP/over.json" "d == []"
cat >"$TMP/signoff.patch" <<'EOF'
diff --git a/src/a.ts b/src/a.ts
--- a/src/a.ts
+++ b/src/a.ts
@@ -1 +1,2 @@
+const key = process.env.AWS_SECRET_ACCESS_KEY
diff --git a/ci/x.yml b/ci/x.yml
--- a/ci/x.yml
+++ b/ci/x.yml
@@ -1 +1,3 @@
+      - uses: actions/checkout@v4
+      - uses: actions/setup-node@0123456789abcdef0123456789abcdef01234567
diff --git a/src/ok.ts b/src/ok.ts
--- a/src/ok.ts
+++ b/src/ok.ts
@@ -1 +1,2 @@
+const x = 1
EOF
python3 "$RISK" --human-signoff --patch "$TMP/signoff.patch" --author 'renovate[bot]' --author-type Bot \
  src/ok.ts >"$TMP/lines.json"
assert_json "$TMP/lines.json" "d == ['src/a.ts', 'ci/x.yml', 'author:renovate[bot]']"
ok human-signoff-paths

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

# Exit status of a command, stdout to $1, without tripping set -e.
status() { local out="$1" rc=0; shift; "$@" >"$out" || rc=$?; echo "$rc"; }

[[ "$(status "$TMP/bound.json" python3 "$BIND" --patch "$TMP/sample.diff" --findings "$TMP/findings.json")" == 3 ]] \
  || fail "bind: unplaced majors must exit 3"
assert_json "$TMP/bound.json" "len(d['kept']) == 1 and d['kept'][0]['title'] == 'in hunk'"
assert_json "$TMP/bound.json" "len(d['dropped']) == 4 and d['body'] == []"
ok bind-in-hunk

# A break in an unchanged file, caused by a changed hunk, lands in body and exits 3.
cat >"$TMP/caused.json" <<'EOF'
[{"severity":"blocker","path":"src/caller.test.ts","line":12,"in_diff":false,
  "cause_path":"src/x.ts","cause_line":42,"title":"caller breaks"}]
EOF
[[ "$(status "$TMP/caused-bound.json" python3 "$BIND" --patch "$TMP/sample.diff" --findings "$TMP/caused.json")" == 3 ]] \
  || fail "bind: body blocker must exit 3"
assert_json "$TMP/caused-bound.json" "len(d['body']) == 1 and d['dropped'] == [] and d['kept'] == []"
cat >"$TMP/pre.json" <<'EOF'
[{"severity":"major","path":"src/old.ts","line":3,"in_diff":false,"pre_existing":true,"title":"old debt"},
 {"severity":"nit","path":"src/old.ts","line":4,"in_diff":false,"title":"old nit"}]
EOF
[[ "$(status "$TMP/pre-bound.json" python3 "$BIND" --patch "$TMP/sample.diff" --findings "$TMP/pre.json")" == 0 ]] \
  || fail "bind: pre-existing majors and nits must exit 0"
ok bind-body-bucket

cat >"$TMP/carry.json" <<'EOF'
[{"severity":"blocker","path":"src/old.ts","line":10,"title":"carried"}]
EOF
python3 "$BIND" --patch "$TMP/sample.diff" --findings "$TMP/carry.json" \
  --allow-path src/old.ts >"$TMP/carry-bound.json"
assert_json "$TMP/carry-bound.json" "len(d['kept']) == 1"
[[ "$(status "$TMP/carry-drop.json" python3 "$BIND" --patch "$TMP/sample.diff" --findings "$TMP/carry.json")" == 3 ]] \
  || fail "bind: unplaced carried blocker must exit 3"
assert_json "$TMP/carry-drop.json" "len(d['kept']) == 0"
ok bind-allow-path

cat >"$TMP/wrap.json" <<'EOF'
{"findings":[{"severity":"blocker","path":"src/x.ts","line":"42","in_diff":true,"title":"str line"}]}
EOF
python3 "$BIND" --patch "$TMP/sample.diff" --findings "$TMP/wrap.json" >"$TMP/wrap-bound.json"
assert_json "$TMP/wrap-bound.json" "len(d['kept']) == 1"
ok bind-wrapper

# --- gate ---

GATE="$SKILL/scripts/gate.py"
[[ -f "$GATE" ]] || fail "missing $GATE"
HEAD=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
EV="$TMP/ev"
mkdir -p "$EV"

reset_evidence() {
  echo '[[]]' >"$EV/reviews.json"
  echo '[[]]' >"$EV/comments.json"
  echo '[[]]' >"$EV/timeline.json"
  echo '[{"data":{"repository":{"pullRequest":{"reviewThreads":{"nodes":[]}}}}}]' >"$EV/threads.json"
  cat >"$EV/checks.json" <<EOF
[{"total_count":1,"check_runs":[{"id":1,"name":"build-and-test","head_sha":"$HEAD","status":"completed","conclusion":"success"}]}]
EOF
  echo '[[]]' >"$EV/statuses.json"
  echo '[]' >"$EV/signoff.json"
  echo '{"kept":[],"body":[],"dropped":[]}' >"$EV/bound.json"
}

write_payload() {
  python3 - "$EV/payload.json" "$1" "$HEAD" "$2" <<'PY'
import json, sys
path, event, head, marker = sys.argv[1:]
body = f"""## Approved: o/r#1

| | |
|---|---|
| Model | test-model |
| Reviewed head | {head} |
| Pass | deep |
| CI | green on {head} |
| Review context | clear |
| Human sign-off | not required |
| Coverage | 3 of 3 changed files |

<!-- bulma-review: v=1 {marker} sha={head} preflight=1 -->
"""
json.dump({"commit_id": head, "event": event, "body": body, "comments": []}, open(path, "w"))
PY
}

gate() {
  status "$TMP/gate.out" python3 "$GATE" --dir "$EV" --payload "$EV/payload.json" --me review-bot \
    --head "$HEAD" --signoff "$EV/signoff.json" --ledger "$EV/bound.json" "$@"
}

blocked_with() {
  [[ "$(gate)" == 1 ]] && grep -q "$1" "$TMP/gate.out"
}

CLEAN="pass=deep blockers=0 majors=0 reason=- open=- risk=low critic=skip"

reset_evidence; write_payload APPROVE "$CLEAN"
[[ "$(gate)" == 0 ]] || fail "gate: clean approve must pass ($(cat "$TMP/gate.out"))"

reset_evidence; write_payload APPROVE "$CLEAN"
cat >"$EV/reviews.json" <<EOF
[[{"id":5,"user":{"login":"alice","type":"User"},"state":"CHANGES_REQUESTED","submitted_at":"2026-10-19T10:00:00Z","commit_id":"$HEAD"}]]
EOF
blocked_with 'open change request from alice' || fail "gate: open change request must block"

reset_evidence; write_payload APPROVE "$CLEAN"
cat >"$EV/reviews.json" <<EOF
[[{"id":5,"user":{"login":"alice","type":"User"},"state":"DISMISSED","submitted_at":"2026-10-19T10:00:00Z","commit_id":"$HEAD"}]]
EOF
cat >"$EV/timeline.json" <<'EOF'
[[{"event":"review_dismissed","actor":{"login":"author"},"created_at":"2026-10-19T11:00:00Z",
   "dismissed_review":{"state":"changes_requested","review_id":5}}]]
EOF
blocked_with 'dismissed by author, never cleared' || fail "gate: author-dismissed change request must block"

reset_evidence; write_payload APPROVE "$CLEAN"
echo '[{"data":{"repository":{"pullRequest":{"reviewThreads":{"nodes":[{"id":"T1","isResolved":false,"comments":{"nodes":[{"url":"u1"}]}}]}}}}}]' >"$EV/threads.json"
blocked_with 'unresolved thread: u1' || fail "gate: unresolved thread must block"

reset_evidence; write_payload APPROVE "$CLEAN"
cat >"$EV/reviews.json" <<EOF
[[{"id":8,"user":{"login":"alice","type":"User"},"state":"APPROVED","submitted_at":"2026-10-19T10:00:00Z","commit_id":"$HEAD"}]]
EOF
echo '[{"data":{"repository":{"pullRequest":{"reviewThreads":{"nodes":[{"id":"T1","isResolved":false,"comments":{"nodes":[{"url":"u1","author":{"login":"alice"}}]}}]}}}}}]' >"$EV/threads.json"
[[ "$(gate)" == 0 ]] || fail "gate: approver's own thread must not block ($(cat "$TMP/gate.out"))"

reset_evidence; write_payload APPROVE "$CLEAN"
cat >"$EV/reviews.json" <<EOF
[[{"id":8,"user":{"login":"alice","type":"User"},"state":"APPROVED","submitted_at":"2026-10-19T10:00:00Z","commit_id":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"}]]
EOF
echo '[{"data":{"repository":{"pullRequest":{"reviewThreads":{"nodes":[{"id":"T1","isResolved":false,"comments":{"nodes":[{"url":"u1","author":{"login":"alice"}}]}}]}}}}}]' >"$EV/threads.json"
blocked_with 'unresolved thread: u1' || fail "gate: approval on an older SHA must not clear a thread"

reset_evidence; write_payload APPROVE "$CLEAN"
echo '[[{"context":"AI QA","state":"failure","description":"FAIL: login fails","created_at":"2026-10-19T10:00:00Z"}]]' >"$EV/statuses.json"
blocked_with 'needs human approval: status AI QA says FAIL' || fail "gate: AI QA FAIL must block"

reset_evidence; write_payload APPROVE "$CLEAN"
echo '[[{"context":"AI QA","state":"success","description":"BLOCKED: env down","created_at":"2026-10-19T10:00:00Z"}]]' >"$EV/statuses.json"
[[ "$(gate)" == 0 ]] || fail "gate: AI QA BLOCKED must not block ($(cat "$TMP/gate.out"))"

reset_evidence; write_payload APPROVE "$CLEAN"
cat >"$EV/checks.json" <<EOF
[{"check_runs":[{"id":1,"name":"build-and-test","head_sha":"$HEAD","status":"completed","conclusion":"skipped"},
                {"id":2,"name":"CodeRabbit","head_sha":"$HEAD","status":"completed","conclusion":"success"}]}]
EOF
blocked_with 'no successful build/test check' || fail "gate: skipped CI must block"

reset_evidence; write_payload APPROVE "$CLEAN"
echo '["infra/stack.yaml"]' >"$EV/signoff.json"
[[ "$(gate)" == 0 ]] || fail "gate: sign-off list must not block ($(cat "$TMP/gate.out"))"

reset_evidence; write_payload APPROVE "$CLEAN"
python3 - "$EV/payload.json" <<'PY'
import json, sys
p = json.load(open(sys.argv[1]))
p["body"] = "\n".join(l for l in p["body"].splitlines() if not l.startswith("| Coverage"))
json.dump(p, open(sys.argv[1], "w"))
PY
blocked_with 'template row missing: Coverage' || fail "gate: missing row must block"
[[ "$(status /dev/null python3 "$GATE" --dir "$EV" --payload "$EV/payload.json" --me review-bot --head "$HEAD")" == 1 ]] \
  || fail "gate: missing row must block payloads without approval evidence too"

reset_evidence; write_payload APPROVE "$CLEAN"
echo '{"kept":[],"body":[{"severity":"blocker","title":"caller breaks"}],"dropped":[]}' >"$EV/bound.json"
blocked_with 'blocker in ledger (body)' || fail "gate: body blocker must block"

reset_evidence; write_payload APPROVE "pass=deep blockers=0 majors=0 reason=- open=- risk=high critic=failed"
blocked_with 'risk=high but critic=failed' || fail "gate: failed critic must block"

reset_evidence; write_payload APPROVE "pass=light blockers=0 majors=0 reason=- open=- risk=low critic=skip"
cat >"$EV/reviews.json" <<'EOF'
[[{"id":7,"user":{"login":"review-bot"},"state":"CHANGES_REQUESTED","submitted_at":"2026-10-19T09:00:00Z",
   "body":"<!-- bulma-review: v=1 pass=deep sha=old blockers=1 majors=0 reason=- open=a:1:x preflight=1 -->"}]]
EOF
blocked_with 'needs pass=deep' || fail "gate: light flip after my change request must block"
write_payload APPROVE "$CLEAN"
[[ "$(gate)" == 0 ]] || fail "gate: deep flip after my change request must pass ($(cat "$TMP/gate.out"))"

reset_evidence; write_payload APPROVE "pass=light blockers=0 majors=0 reason=- open=- risk=low critic=skip"
cat >"$EV/comments.json" <<'EOF'
[[{"user":{"login":"review-bot"},"created_at":"2026-10-19T09:00:00Z",
   "body":"<!-- bulma-review: v=1 pass=light sha=old blockers=0 majors=0 reason=coverage open=- preflight=1 -->"}]]
EOF
blocked_with 'needs pass=deep' || fail "gate: light approve after coverage defer must block"

reset_evidence; write_payload APPROVE "$CLEAN"
cat >"$EV/reviews.json" <<EOF
[[{"id":9,"user":{"login":"peer-bot","type":"User"},"state":"APPROVED","submitted_at":"2026-10-19T10:00:00Z","commit_id":"$HEAD"}]]
EOF
[[ "$(gate --bot-login peer-bot)" == 3 ]] || fail "gate: second bot approval must exit 3"
[[ "$(gate)" == 0 ]] || fail "gate: a human approval must not trip bot quorum"

reset_evidence; write_payload APPROVE "$CLEAN"
rm "$EV/checks.json"
blocked_with 'evidence missing' || fail "gate: missing evidence must block"
ok gate

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

python3 - "$SKILL" <<'PY' || fail "approval preflight contract"
import pathlib, sys
root = pathlib.Path(sys.argv[1])
skill = (root / 'SKILL.md').read_text()
assert "Other reviewers' state is ignored" not in skill
preflight = (root / 'references/PREFLIGHT.md').read_text()
collector = (root / 'scripts/snapshot.py').read_text()
for required in ('reviewThreads', 'pageInfo', '--paginate'):
    assert required in collector, required
for required in ('in_reply_to_id', 'review_dismissed',
                 'CI did not run', 'needs human sign-off', 'reviewed_sha == headRefOid',
                 'Critical/High', 'PR_FILES.txt'):
    assert required in preflight, required
for node in ('pass_decision', 'gates', 'verdict', 'publish'):
    assert 'PREFLIGHT.md' in (root / f'nodes/{node}.md').read_text(), node
publish = (root / 'nodes/publish.md').read_text()
assert publish.index('PREFLIGHT.md') < publish.index('-X POST')
assert '## ✅ Approved:' not in publish.split('```markdown', 1)[1].split('```', 1)[0]
assert 'reviews/$REVIEW_ID' in publish
review = (root / 'nodes/review.md').read_text()
assert '{ success, data }' in review and 'cause_path' in review
assert 'Uncertainty about a major or a nit disappears' not in review
assert 'keeps its severity' in review
assert 'gate.py' in publish and '&& gh api "repos/$REPO/pulls/$PR/reviews"' in publish
assert 'dismissals' in preflight and 'Retire my stale approval' in preflight
critic = (root / 'nodes/critic.md').read_text()
assert 'critic=failed' in critic and 'still publish' not in critic
verdict = (root / 'nodes/verdict.md').read_text()
assert 'anchored to a changed path' not in verdict and 'wherever it surfaces' in verdict
assert 'Loaded by another reviewer' in skill
PY
ok approval-preflight-contract

# --- convergence, rebase-only, project knowledge ---
python3 - "$SKILL" <<'PY'
import sys
from pathlib import Path
root = Path(sys.argv[1])
skill = (root / 'SKILL.md').read_text()
decide = (root / 'nodes/pass_decision.md').read_text()
review = (root / 'nodes/review.md').read_text()
publish = (root / 'nodes/publish.md').read_text()
verdict = (root / 'nodes/verdict.md').read_text()
fetch = (root / 'nodes/fetch.md').read_text()
assert 'Converge, do not loop' in skill and '## Convergence' in decide
assert 'round=<n>' in decide and 'round=1' in publish
assert '## Rebase only' in decide and 'git patch-id --stable' in decide
assert 'reason=rebase' in decide and 'Rebase only' in fetch
assert '"instances"' in review and 'Same in' in publish
assert 'REVIEW.md' in review and '## Gotchas' in review
assert 'Reuse (major)' in review and 'duplicates an existing one' in verdict
assert 'root changelog' in review and 'root changelog' in verdict
assert 'disputes the finding' in fetch
assert 'Human focus' in publish and 'Nothing to fix.' in publish
assert 'unlikely conditions' in review
PY
ok convergence-contract

# rebase-only detection: same change on a new base gives the same patch id
G="$TMP/rebase"
gc() { git -C "$G" -c user.name=t -c user.email=t@t "$@"; }
git init -q -b main "$G"
gc commit -q --allow-empty -m base
echo a >"$G/a.txt"; gc add a.txt; gc commit -q -m a
gc checkout -q -b pr
echo feature >"$G/f.txt"; gc add f.txt; gc commit -q -m feature
PRIOR="$(gc rev-parse HEAD)"
gc checkout -q main
echo b >"$G/b.txt"; gc add b.txt; gc commit -q -m b
gc checkout -q pr
gc rebase -q main
NEW_HEAD="$(gc rev-parse HEAD)"
pid() { gc diff "$(gc merge-base main "$1")" "$1" | git -C "$G" patch-id --stable | cut -d' ' -f1; }
[[ "$PRIOR" != "$NEW_HEAD" ]] || fail "rebase did not move head"
[[ "$(pid "$PRIOR")" == "$(pid "$NEW_HEAD")" ]] || fail "rebase-only: patch ids differ"
echo more >>"$G/f.txt"; gc commit -q -am more
[[ "$(pid "$PRIOR")" != "$(pid HEAD)" ]] || fail "rebase-only: content change not detected"
ok rebase-only-patch-id

if grep -rniE 'empath|chargebee|frontegg|zitadel|dynamo' "$ROOT/skills" "$ROOT/agents" "$ROOT/commands"; then
  fail "product or vendor names leaked into skills"
fi
ok no-project-knowledge

echo "all passed"

PYTHONDONTWRITEBYTECODE=1 python3 "$ROOT/tests/lib/test_review_snapshot.py"
