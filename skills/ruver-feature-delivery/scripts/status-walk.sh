#!/usr/bin/env bash
# Print the VOICE.md Walk line from an fd STATE.md. Read-only. No network.
set -euo pipefail

STATE="${1:-}"
[[ -n "$STATE" && -f "$STATE" ]] || exit 0

yaml_get() {
  awk -v key="$1" '
    $0 == "---" { c++; next }
    c == 1 && index($0, key ":") == 1 {
      sub("^[^:]+:[[:space:]]*", "")
      print
      exit
    }
    c >= 2 { exit }
  ' "$STATE"
}

status="$(yaml_get status)"
path="$(yaml_get path)"
risk="$(yaml_get risk)"
risk="${risk:-normal}"
branch="$(yaml_get branch)"
ticket="$(yaml_get current_ticket)"

case "$status" in
  mcp) cur=mcp ;;
  triage) cur=triage ;;
  grilling) cur=grill ;;
  speccing) cur=spec ;;
  ticketing) cur=tickets ;;
  critiquing) cur=plan_critic ;;
  diagnosing) cur=diagnose ;;
  implementing) cur=implement ;;
  reviewing) cur=review ;;
  testing) cur=tester ;;
  blasting) cur=blast ;;
  quality) cur=quality ;;
  shipping) cur=ship ;;
  ci_watching) cur=ci ;;
  done|done_local|done_report) cur=DONE ;;
  *) cur="" ;;
esac

nodes=(mcp triage)
case "$path" in
  full_feature)
    nodes+=(grill spec tickets)
    [[ "$risk" != low ]] && nodes+=(plan_critic)
    nodes+=(implement review tester evidence blast quality ship ci)
    ;;
  debug_fix)
    nodes+=(diagnose implement review tester evidence blast quality ship ci)
    ;;
  light_change)
    nodes+=(tickets implement review tester evidence)
    [[ "$risk" == elevated ]] && nodes+=(blast)
    nodes+=(quality ship ci)
    ;;
  *)
    nodes+=(implement review tester evidence quality ship ci)
    ;;
esac

walk=""
seen=0
for n in "${nodes[@]}"; do
  if [[ "$cur" == "DONE" ]]; then
    mark="✓"
  elif [[ -n "$cur" && "$n" == "$cur" ]]; then
    mark="●"
    seen=1
  elif [[ "$seen" -eq 0 && -n "$cur" ]]; then
    mark="✓"
  else
    mark="○"
  fi
  walk="${walk:+$walk }${mark}${n}"
done

parked=""
case "$status" in
  waiting_user|waiting_blocker|handed_off|escalated) parked=" ($status)" ;;
esac

echo "job      ${branch:-cwd}"
echo "path     ${path:-unknown}"
echo "risk     $risk"
echo "status   ${status:-unknown}${ticket:+  ticket $ticket}"
echo "Walk:    ${walk}${parked}"
