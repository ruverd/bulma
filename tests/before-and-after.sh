#!/usr/bin/env bash
# format.sh + ensure-session.sh. No agent-browser, no gh, no network.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FMT="$ROOT/skills/before-and-after/scripts/format.sh"
SES="$ROOT/skills/before-and-after/scripts/ensure-session.sh"

fail() { echo "FAIL: $*" >&2; exit 1; }
ok() { echo "ok  $*"; }

[[ -x "$FMT" ]] || fail "format.sh not executable"
[[ -x "$SES" ]] || fail "ensure-session.sh not executable"
grep -F -q -- '--headed false' "$ROOT/skills/before-and-after/SKILL.md" || fail "browser capture must be headless"
grep -F -q -- "--session-name \"\$SESSION\"" "$ROOT/skills/before-and-after/SKILL.md" || fail "browser capture must restore supported session"
grep -F -q "agent-browser --session \"\$SESSION\" close" "$ROOT/skills/before-and-after/SKILL.md" || fail "browser capture must close its session"
if grep -F -q -- '--restore' "$ROOT/skills/before-and-after/SKILL.md"; then
  fail "browser capture uses unsupported agent-browser --restore"
fi

TMP="$(mktemp -d "${TMPDIR:-/tmp}/bulma-baa.XXXXXX")"
trap 'rm -rf "$TMP"' EXIT
cd "$TMP"

python3 - <<'PY'
from pathlib import Path
png = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
    "890000000a49444154789c63000100000500010d0a2db40000000049454e44ae426082"
)
Path("before.png").write_bytes(png)
Path("after.png").write_bytes(png)
Path("new.png").write_bytes(png)
PY

out="$("$FMT" --before before.png --after after.png --label Desktop)"
echo "$out" | grep -q '<!-- bulma-before-and-after:start -->' || fail "missing start marker"
echo "$out" | grep -q '<!-- bulma-before-and-after:end -->' || fail "missing end marker"
echo "$out" | grep -q '| Before (Desktop) | After (Desktop) |' || fail "pair heading"
echo "$out" | grep -q '!\[Before\](./before.png)' || fail "before image ref"
echo "$out" | grep -q '!\[After\](./after.png)' || fail "after image ref"
ok pair

out="$("$FMT" --after new.png --label "New page")"
echo "$out" | grep -q '| Preview (New page) |' || fail "preview heading"
echo "$out" | grep -q '!\[Preview\](./new.png)' || fail "preview image ref"
echo "$out" | grep -q 'Before' && fail "preview should not say Before"
ok preview

out="$("$FMT" --before - --after new.png --before before.png --after after.png --label New --label Desktop)"
echo "$out" | grep -q '| Preview (New) |' || fail "mixed preview"
echo "$out" | grep -q '| Before (Desktop) | After (Desktop) |' || fail "mixed pair"
ok mixed

list="$("$FMT" --attach-list --before before.png --after after.png)"
echo "$list" | grep -qx './before.png' || fail "attach-list before"
echo "$list" | grep -qx './after.png' || fail "attach-list after"
ok attach-list

{
  printf '%s\n' '# Title'
  printf '%s\n' 'Intro prose.'
} >body.md
"$FMT" --body-file body.md --after new.png >body-next.md
grep -q '# Title' body-next.md || fail "body lost title"
grep -q 'Intro prose.' body-next.md || fail "body lost prose"
grep -q '<!-- bulma-before-and-after:start -->' body-next.md || fail "body missing block"
"$FMT" --body-file body-next.md --after new.png --label Again >body-2.md
count="$(grep -c 'bulma-before-and-after:start' body-2.md || true)"
[[ "$count" == "1" ]] || fail "marker not replaced (count=$count)"
grep -q 'Preview (Again)' body-2.md || fail "second format did not update"
ok replace-block

set +e
err="$("$FMT" --after after.png --before before.png --before extra.png 2>&1)"
got=$?
set -e
[[ "$got" -ne 0 ]] || fail "mismatched before/after should fail"
echo "$err" | grep -qi 'before' || fail "mismatch error should mention before"
ok mismatch-count

set +e
err="$("$FMT" --after missing.png 2>&1)"
got=$?
set -e
[[ "$got" -ne 0 ]] || fail "missing file should fail"
ok missing-file

mkdir -p "dir with space"
cp after.png "dir with space/x.png"
set +e
err="$("$FMT" --after "dir with space/x.png" 2>&1)"
got=$?
set -e
[[ "$got" -ne 0 ]] || fail "whitespace path should fail"
ok whitespace-path

# ensure-session: git remote, no gh. Shared dir is under BULMA_HOME, not the worktree.
HOME_FAKE="$TMP/home"
mkdir -p "$HOME_FAKE"
git init -q repo
git -C repo remote add origin git@github.com:Acme/App.git
out="$(
  cd "$TMP/repo" &&
  HOME="$HOME_FAKE" BULMA_HOME="$HOME_FAKE/.bulma" \
    "$SES"
)"
echo "$out" | grep -q 'SESSION=bulma-acme-app' || fail "session id from git remote: $out"
echo "$out" | grep -q "STATE_DIR=$HOME_FAKE/.bulma/agent-browser/bulma-acme-app" || fail "state dir: $out"
echo "$out" | grep -q "CAPTURE_DIR=$HOME_FAKE/.bulma/agent-browser/bulma-acme-app/captures" || fail "capture dir: $out"
[[ -d "$HOME_FAKE/.bulma/agent-browser/bulma-acme-app/captures" ]] || fail "did not mkdir captures"
ok ensure-session

echo "all passed"
