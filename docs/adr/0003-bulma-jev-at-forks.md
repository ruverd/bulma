# Bulma: Jev answers at graph forks, code keeps the edges

Status: accepted

The graphs decide with prose heuristics: `ROUTING.md` picks a path by
keywords, `VERDICTS.md` lists five FAIL conditions, `FAILURES.md` seven
classes, `verify.md` a fix/skip table. Each call is made once, in the
session model's head, with no number attached and no record to calibrate.

Decision: one new graph, `bulma`, loads the target graph on the main thread
and asks TypeSafe Jev a typed question at nine named forks
(`skills/bulma/decisions.json`). Jev returns a choice or a probability with
calibrated confidence; bulma acts when confidence clears a threshold the
user tunes (`$RUVER_HOME/bulma.json`), else the graph's own rule applies.
Every answer is logged with the graph's answer, so thresholds come from
data (`bulma.py report`).

Boundaries: Jev picks only among options a node already has; edges, loop
caps, the code-review verdict and the deterministic tables (`goal.step`,
`apply_qa`) stay in code. Existing graphs are not edited; hooks live in
bulma and a test keeps catalog enums equal to graph enums. Jev is optional
everywhere else; `/bulma` stops with a requirement message without a key.

Naming: the skill id is `bulma`, not `ruver-bulma`. It is a product name the
user chose; the `ruver-*` rule stays for the graphs it drives. Its state dir
is `.ruver-bulma/` so `DISK.md`, `ruver status` and `ruver report` still see
it.
