# Node: inventory

**Verb:** observe
**Capability:** read `$RUVER_ROOT`, `gh` read-only

Run `bash scripts/world.sh` (add `--pr <url>` when args carry a PR or MR
URL). It writes `.ruver-bulma/world.json` and `.ruver-bulma/candidates.json`
and prints a three-line summary. Copy `stack_top`, `qa_active`, and the
candidate ids into the chat `S:` line only when they change what happens
next. Warnings (no `gh`, not authenticated) go into `D:` once.

Then `python3 scripts/watch.py --summary` (no `gh` calls). It prints one line
only when other workspaces have stalled or blocked work; put that line in `D:`
so the user knows to run `/bulma watch`.

Never edit `world.json` by hand. Never call Jev here.

## Output

`world_path`, `status: routing`.
