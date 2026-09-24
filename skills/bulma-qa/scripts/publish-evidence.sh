#!/usr/bin/env bash
# Post the QA comment with video/screenshots via gh --attach (CLI ≥ 2.99).
# Never gh gist create on binaries.
#
# Usage:
#   publish-evidence.sh --repo owner/repo --pr N --sha OID --body-file path
#     [--video path.webm] [--artifacts dir] [--screenshot path] [--out path]
#
# --screenshot is repeatable (extra PNGs). Prints key=value.
# Exit 0 on comment; 2 if attach/comment failed (still printed local
# paths. Caller must not skip the comment).

set -euo pipefail

REPO=""
PR=""
SHA=""
VIDEO=""
ARTIFACTS=""
BODY=""
OUT=""
SCREENSHOTS=()

usage() {
  sed -n '2,12p' "$0" | sed 's/^# \?//'
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo) REPO="${2:-}"; shift 2 ;;
    --pr) PR="${2:-}"; shift 2 ;;
    --sha) SHA="${2:-}"; shift 2 ;;
    --video) VIDEO="${2:-}"; shift 2 ;;
    --artifacts) ARTIFACTS="${2:-}"; shift 2 ;;
    --screenshot) SCREENSHOTS+=("${2:-}"); shift 2 ;;
    --body-file) BODY="${2:-}"; shift 2 ;;
    --out) OUT="${2:-}"; shift 2 ;;
    -h|--help) usage ;;
    *) echo "unknown arg: $1" >&2; usage ;;
  esac
done

[[ -n "$REPO" && -n "$PR" && -n "$SHA" && -n "$BODY" ]] || usage
[[ -f "$BODY" ]] || { echo "body file does not exist: $BODY" >&2; exit 1; }

if [[ -z "$VIDEO" ]]; then
  if [[ -f .bulma-qa/artifacts/reel.webm ]]; then
    VIDEO=.bulma-qa/artifacts/reel.webm
  else
    VIDEO=$(find test-results .bulma-qa/artifacts -name '*.webm' 2>/dev/null | head -1 || true)
  fi
fi

if [[ -z "$ARTIFACTS" && -d .bulma-qa/artifacts ]]; then
  ARTIFACTS=.bulma-qa/artifacts
fi

emit() {
  printf '%s\n' "$@"
  if [[ -n "$OUT" ]]; then
    printf '%s\n' "$@" >>"$OUT"
  fi
}

fail_upload() {
  emit "STATUS=failed"
  emit "COMMENT_URL="
  emit "ERROR=${1}"
  [[ -n "$VIDEO" ]] && emit "LOCAL_VIDEO=${VIDEO}"
  exit 2
}

ATTACH=()
if [[ -n "$VIDEO" && -f "$VIDEO" ]]; then
  ATTACH+=(--attach "$VIDEO")
fi
if [[ -n "$ARTIFACTS" && -d "$ARTIFACTS" ]]; then
  while IFS= read -r png; do
    ATTACH+=(--attach "$png")
  done < <(find "$ARTIFACTS" -maxdepth 1 -name '*.png' | sort)
fi
for shot in "${SCREENSHOTS[@]+"${SCREENSHOTS[@]}"}"; do
  if [[ -n "$shot" && -f "$shot" ]]; then
    ATTACH+=(--attach "$shot")
  fi
done

url="$(gh pr comment "$PR" --repo "$REPO" --body-file "$BODY" "${ATTACH[@]}")" \
  || fail_upload "gh pr comment failed"

emit "STATUS=ok"
emit "COMMENT_URL=${url}"
[[ -n "$VIDEO" && -f "$VIDEO" ]] && emit "VIDEO=${VIDEO}"
exit 0
