# Node: admit

**Verb:** gate
**Capability:** run `scripts/bulma.py`, write `.ruver-bulma/STATE.md`

## Steps

1. Load `ruver-memory` (both files). Resolve `$RUVER_ROOT` (DISK.md).
2. Parse args with `../ARGS.md`. `power`, `tune`, `model` → **power**.
   `report`, `status`, `doctor` → **report**. These need no key.
3. Otherwise run `python3 scripts/bulma.py doctor`.
   - exit 0 → continue.
   - exit 2 or 3 → print the script's message in the chat language, write
     `status: blocked`, end the turn. Do not load any graph.
   - exit 4 → same, quoting the catalog or config error.
4. `python3 scripts/bulma.py power` → `power`, `power_source`. A `--power`
   flag in args wins for this run; pass it to every `ask`. `--effort` and
   `--session-model` are run flags for **spend**, not Jev.
5. Init `.ruver-bulma/STATE.md` from `../templates/STATE.md` unless a live
   one exists (then keep `decision_ids` and counts). Write `args`, `power`,
   `power_source`, `model` (`bulma.py model`), `updated_at`.

## Output

`status: inventory`, or `blocked` with the message.
