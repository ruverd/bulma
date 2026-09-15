#!/usr/bin/env bash
# Fail closed if the walk start sample is a login wall. Stop may be a
# login wall (S10 last frame). Text snapshots only. No network, no
# WebM parse.
#
# THE TEXT GATE CANNOT SEE THE TAPE. Snapshots are taken after
# hydration, but `record start` opens a fresh tab with empty
# localStorage, so on a magic-link app the first ~30s of every
# recording IS the login wall and the reviewer's poster frame is a
# Sign in screen. That is what --video is for. Do not report a text
# gate exit 0 as evidence about video content.
#
# Do not try to automate this with OCR. Verified 2026-09-10 on
# empath-ui: tesseract returns EMPTY on both the Sign in screen and
# the app (light text on dark purple), so an OCR gate passes
# everything. A gate that cannot fail is worse than none.
#
# Callers MUST snapshot the recording tab (active after `record start`),
# not a sibling authed tab. Magic-link SPAs often leave Sign in on the
# new tab while the previous tab stays gated.
#
# Usage:
#   walk-video-gate.sh --start start.txt [--middle mid.txt] [--stop stop.txt]
#   walk-video-gate.sh --text-file start.txt [--text-file more.txt]
#   walk-video-gate.sh --start start.txt --video walk.webm
#
# --video extracts frames 0s/10s/25s and exits 3, never 0. Exit 3
# means "text gate passed, now LOOK at these frames". Open them. If
# any shows a login wall, find the first keyframe after hydration and
# trim before publishing:
#
#   ffprobe -v error -select_streams v -skip_frame nokey \
#     -show_entries frame=pts_time -of csv=p=0 -read_intervals '%+60' in.webm
#   ffmpeg -ss <keyframe> -i in.webm -c copy out.webm
#
# Better still, avoid the trim: after hydrating the recording tab and
# confirming the Navbar, `record stop`, discard that file, and
# `record start` again. Then the tape never contains the login wall.
#
set -euo pipefail

print_usage() {
  sed -n '2,9p' "$0" | sed 's/^# \?//'
}

usage() {
  print_usage
  exit 1
}

need_file() {
  [[ $# -ge 2 ]] || usage
  [[ -f "$2" ]] || { echo "sample does not exist: $2" >&2; exit 1; }
}

is_login_wall() {
  grep -Eiq 'sign in|check your email|magic link|qa:login|/login' -- "$1"
}

start=""
video=""
text_files=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --start)
      need_file "$@"
      start="$2"
      shift 2
      ;;
    --middle|--stop)
      need_file "$@"
      shift 2
      ;;
    --text-file)
      need_file "$@"
      text_files+=("$2")
      shift 2
      ;;
    --video)
      need_file "$@"
      video="$2"
      shift 2
      ;;
    -h|--help)
      print_usage
      exit 0
      ;;
    *)
      echo "unknown arg: $1" >&2
      usage
      ;;
  esac
done

if [[ -z "$start" ]]; then
  [[ ${#text_files[@]} -gt 0 ]] || { echo "missing --start" >&2; exit 1; }
  start="${text_files[0]}"
fi

if is_login_wall "$start"; then
  echo "start sample is a login wall: $start" >&2
  exit 1
fi

if [[ -n "$video" ]]; then
  if ! command -v ffmpeg >/dev/null; then
    echo "--video needs ffmpeg. The tape head is UNCHECKED." >&2
    exit 1
  fi
  dir="$(dirname "$video")/frames-$(basename "${video%.*}")"
  mkdir -p "$dir"
  for s in 0 10 25; do
    ffmpeg -v error -y -ss "$s" -i "$video" -frames:v 1 \
      "$dir/t${s}s.png" </dev/null || {
        echo "could not extract ${s}s from: $video" >&2
        exit 1
      }
  done
  echo "text gate passed. NOW LOOK at the head of the tape:" >&2
  for s in 0 10 25; do echo "  $dir/t${s}s.png" >&2; done
  echo "a login wall in any of them is not a PASS. See the header to trim." >&2
  exit 3
fi

exit 0
