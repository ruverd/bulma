#!/usr/bin/env bash
# Concatenate per-surface WebM clips into one reel for gh --attach.
# Usage: concat-clips.sh --out reel.webm clip1.webm [clip2.webm ...]
set -euo pipefail

OUT=""
CLIPS=()

print_usage() {
  sed -n '2,4p' "$0" | sed 's/^# \?//'
}

usage() {
  print_usage
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --out)
      [[ $# -ge 2 ]] || usage
      OUT="$2"
      shift 2
      ;;
    -h|--help)
      print_usage
      exit 0
      ;;
    --)
      shift
      CLIPS+=("$@")
      break
      ;;
    -*)
      echo "unknown arg: $1" >&2
      usage
      ;;
    *)
      CLIPS+=("$1")
      shift
      ;;
  esac
done

[[ -n "$OUT" && ${#CLIPS[@]} -gt 0 ]] || usage

for clip in "${CLIPS[@]}"; do
  [[ -f "$clip" ]] || { echo "missing clip: $clip" >&2; exit 1; }
done

mkdir -p "$(dirname "$OUT")"

if [[ ${#CLIPS[@]} -eq 1 ]]; then
  cp "${CLIPS[0]}" "$OUT"
  exit 0
fi

if ! command -v ffmpeg >/dev/null; then
  echo "ffmpeg missing; not concatenating" >&2
  exit 2
fi

list="$(mktemp "${TMPDIR:-/tmp}/concat-clips.XXXXXX.txt")"
trap 'rm -f "$list"' EXIT
: >"$list"
for clip in "${CLIPS[@]}"; do
  abs="$(cd "$(dirname "$clip")" && pwd)/$(basename "$clip")"
  printf "file '%s'\n" "${abs//\'/\'\\\'\'}" >>"$list"
done

ffmpeg -v error -y -f concat -safe 0 -i "$list" \
  -c:v libvpx -b:v 1M -an "$OUT" </dev/null
[[ -s "$OUT" ]] || { echo "empty reel: $OUT" >&2; exit 1; }
