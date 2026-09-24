#!/usr/bin/env bash
# Format local stills as a GitHub PR before/after block.
# Images only. Video belongs on the QA comment (gh pr comment --attach).
set -euo pipefail

MARKER_START='<!-- bulma-before-and-after:start -->'
MARKER_END='<!-- bulma-before-and-after:end -->'

usage() {
  cat <<'EOF'
Format stills for a GitHub PR body.

Usage:
  format.sh --after after.png [--before before.png] [--label Desktop] ...
  format.sh --body-file pr.md --after after.png > pr-next.md
  format.sh --attach-list --before before.png --after after.png

Repeat --before/--after/--label in lockstep. --before - means after-only
(Preview) for that slot. With no --before flags, every --after is Preview.

Paths must stay inside the working directory and contain no whitespace.
EOF
  exit 2
}

befores=()
afters=()
labels=()
body_file=""
attach_list=0
have_before=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --before)
      [[ $# -ge 2 ]] || usage
      befores+=("$2")
      have_before=1
      shift 2
      ;;
    --after)
      [[ $# -ge 2 ]] || usage
      afters+=("$2")
      shift 2
      ;;
    --label)
      [[ $# -ge 2 ]] || usage
      labels+=("$2")
      shift 2
      ;;
    --body-file)
      [[ $# -ge 2 ]] || usage
      body_file="$2"
      shift 2
      ;;
    --attach-list)
      attach_list=1
      shift
      ;;
    -h|--help)
      usage
      ;;
    *)
      echo "unknown arg: $1" >&2
      usage
      ;;
  esac
done

if [[ ${#afters[@]} -eq 0 ]]; then
  echo "at least one --after file is required" >&2
  exit 1
fi

if [[ "$have_before" -eq 1 && ${#befores[@]} -ne ${#afters[@]} ]]; then
  echo "provide one --before (or --before -) for every --after" >&2
  exit 1
fi

if [[ ${#labels[@]} -gt ${#afters[@]} ]]; then
  echo "provide at most one --label for every --after" >&2
  exit 1
fi

local_ref() {
  local file="$1"
  local abs rel
  case "$file" in
    /*) abs="$file" ;;
    *) abs="$(pwd)/$file" ;;
  esac
  if command -v python3 >/dev/null 2>&1; then
    rel="$(python3 -c 'import os,sys; print(os.path.relpath(os.path.realpath(sys.argv[1]), os.getcwd()))' "$abs")"
  else
    rel="${file#./}"
  fi
  case "$rel" in
    ..|../*)
      echo "media files must be inside the working directory: $file" >&2
      exit 1
      ;;
  esac
  if [[ "$rel" != .* ]]; then
    rel="./$rel"
  fi
  if [[ "$rel" == *$'\n'* || "$rel" == *$'\t'* || "$rel" == *' '* ]]; then
    echo "media paths cannot contain whitespace: $rel" >&2
    exit 1
  fi
  printf '%s\n' "$rel"
}

is_image() {
  local ext="${1##*.}"
  case "$(printf '%s' "$ext" | tr '[:upper:]' '[:lower:]')" in
    png|jpg|jpeg|gif|webp) return 0 ;;
    *) return 1 ;;
  esac
}

check_file() {
  local file="$1"
  if [[ "$file" == "-" ]]; then
    return 0
  fi
  if [[ ! -f "$file" ]]; then
    echo "media file does not exist: $file" >&2
    exit 1
  fi
  if ! is_image "$file"; then
    echo "unsupported media (images only): $file" >&2
    exit 1
  fi
  local_ref "$file" >/dev/null
}

i=0
while [[ $i -lt ${#afters[@]} ]]; do
  check_file "${afters[$i]}"
  if [[ "$have_before" -eq 1 ]]; then
    check_file "${befores[$i]}"
  fi
  i=$((i + 1))
done

heading() {
  local label="$1"
  if [[ -n "$label" ]]; then
    printf ' (%s)' "$label"
  fi
}

emit_block() {
  local i after before label suffix
  printf '%s\n' "$MARKER_START"
  i=0
  while [[ $i -lt ${#afters[@]} ]]; do
    after="$(local_ref "${afters[$i]}")"
    label=""
    if [[ $i -lt ${#labels[@]} ]]; then
      label="${labels[$i]}"
    fi
    suffix="$(heading "$label")"
    before=""
    if [[ "$have_before" -eq 1 && "${befores[$i]}" != "-" ]]; then
      before="$(local_ref "${befores[$i]}")"
    fi
    if [[ -n "$before" ]]; then
      printf '%s\n' "| Before${suffix} | After${suffix} |"
      printf '%s\n' "|:---:|:---:|"
      printf '%s\n' "| ![Before](${before}) | ![After](${after}) |"
      printf '%s\n' ""
    else
      printf '%s\n' "| Preview${suffix} |"
      printf '%s\n' "|:---:|"
      printf '%s\n' "| ![Preview](${after}) |"
      printf '%s\n' ""
    fi
    i=$((i + 1))
  done
  printf '%s\n' "$MARKER_END"
}

if [[ "$attach_list" -eq 1 ]]; then
  i=0
  while [[ $i -lt ${#afters[@]} ]]; do
    if [[ "$have_before" -eq 1 && "${befores[$i]}" != "-" ]]; then
      local_ref "${befores[$i]}"
    fi
    local_ref "${afters[$i]}"
    i=$((i + 1))
  done
  exit 0
fi

block="$(emit_block)"

replace_block() {
  local body="$1"
  local start end prefix suffix
  start="$(printf '%s' "$body" | awk "index(\$0, \"$MARKER_START\"){print NR; exit}")"
  end="$(printf '%s' "$body" | awk "index(\$0, \"$MARKER_END\"){print NR; exit}")"
  if [[ -z "$start" && -z "$end" ]]; then
    if [[ -z "${body%"${body##*[![:space:]]}"}" ]]; then
      printf '%s' "$block"
      return
    fi
    printf '%s\n\n%s' "${body%"${body##*[![:space:]]}"}" "$block"
    return
  fi
  if [[ -z "$start" || -z "$end" || "$end" -lt "$start" ]]; then
    echo "PR body contains an incomplete before-and-after marker block" >&2
    exit 1
  fi
  local starts ends
  starts="$(printf '%s' "$body" | grep -c 'bulma-before-and-after:start' || true)"
  ends="$(printf '%s' "$body" | grep -c 'bulma-before-and-after:end' || true)"
  if [[ "$starts" -ne 1 || "$ends" -ne 1 ]]; then
    echo "PR body contains multiple before-and-after marker blocks" >&2
    exit 1
  fi
  prefix="$(printf '%s\n' "$body" | sed -n "1,$((start - 1))p")"
  suffix="$(printf '%s\n' "$body" | sed -n "$((end + 1)),\$p")"
  prefix="${prefix%"${prefix##*[![:space:]]}"}"
  suffix="${suffix#"${suffix%%[![:space:]]*}"}"
  if [[ -n "$prefix" ]]; then
    printf '%s\n\n' "$prefix"
  fi
  printf '%s' "$block"
  if [[ -n "$suffix" ]]; then
    printf '\n%s\n' "$suffix"
  fi
}

if [[ -n "$body_file" ]]; then
  [[ -f "$body_file" ]] || { echo "body file does not exist: $body_file" >&2; exit 1; }
  replace_block "$(cat "$body_file")"
else
  printf '%s' "$block"
fi
