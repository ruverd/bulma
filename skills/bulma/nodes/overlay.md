# Node: overlay

**Verb:** run the target under hooks
**Capability:** `load_graph` (ruver-host), run `scripts/bulma.py ask`

## Contract

1. `load_graph <target>` (skill `ruver-<target>`, or `ruver-memory` for
   `memory`). Follow its SKILL.md and GRAPH.md exactly. Bulma stays loaded.
2. When the target, or an engine it loads (`ruver-feature-delivery`,
   `ruver-code-review`), enters a node listed in `../HOOKS.md`, and before
   writing the hooked field(s):
   - build the state JSON from the recipe column, with its caps;
   - write it to `.ruver-bulma/state/<hook>-<UTC ts>.json`;
   - run `python3 scripts/bulma.py ask <hook> --state <file> --context repo=… pr=… sha=… ticket=…`
     plus `--graph-answer <q>=<v>` for every question whose graph rule you
     already evaluated (always under `shadow`), and `--power <level>` when
     the run carries a flag;
   - per question: `act: true` → write Jev's value; `act: false` → apply the
     graph's own rule. Follow the `apply` column for composite rules
     (`qa.gate`, `lstm.verify` disposition, `review.risk` critic).
3. One chat line per hook, VOICE style:
   `J: path=debug_fix .88 ok · risk=elevated .61 -> ROUTING · work_kind=bug .91 ok`
   Under `shadow`: `J(shadow): path=debug_fix .88 (graph: debug_fix)`.
4. Append `decision_id` to STATE `decision_ids`; bump `hooks_fired` or
   `hooks_fallback`.
5. Bus switches inside the target (developer → qa → triage) keep the
   overlay; hooks apply to whichever graph is on top of `STACK.md`. Bulma
   itself never appears on the stack.
6. Script exit 3 (Jev down) → apply the fallback, print
   `J: jev unavailable -> fallback`, continue. Exit 4 (bad state file) →
   fix the state file once; if it fails again, fallback and note it.
7. Outcome hooks (last column of HOOKS.md) are optional calls to
   `scripts/bulma.py outcome <decision_id> <question> reversed`; they never
   gate anything.

## Never

- Skip a gate, invent an edge, or change the target graph's loop caps.
- ASK the user because Jev was undecided.
- Turn a QA finding into PASS from a Jev answer.
- Send full files; the caps in HOOKS.md are the budget.

## Output

The target graph's own outputs, plus the counters above.
