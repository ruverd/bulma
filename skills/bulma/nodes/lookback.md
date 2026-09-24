# Node: lookback

**Verb:** find what keeps coming back
**Capability:** read `$RUVER_HOME/insights/observations.jsonl`; write only a
branch and a draft PR in the skills repo, and only after the user says yes

The quality half of the self-improving loop. Human reviewers keep catching
some classes of defect that the graphs miss. This node counts them by cluster,
checks whether the skill change meant to stop a cluster actually made it
shrink, and proposes the next change.

| Args | Command |
|---|---|
| `lookback` | `python3 scripts/lookback.py` (last 30 days vs the 30 before) |
| `lookback --since N` | last N days vs the N before |
| `lookback --since YYYY-MM-DD [--until YYYY-MM-DD]` | explicit window, e.g. since a skill change merged |
| `lookback --classify` | first label the unlabeled misses in both windows with Jev, then report |

Rows come from `ruver-lstm` and `ruver-reviewer`
([INSIGHTS.md](../../ruver-bus/INSIGHTS.md)). Only human comments count, and a
comment that lstm verified as wrong (`claim_true: no`) is dropped.

## Labels

Without `--classify`, clusters come from regexes and cached labels, and no key
is needed. `--classify` needs `TYPESAFE_API_KEY`. It asks the `insight.classify`
hook ([HOOKS.md](../HOOKS.md)) once per missed row that has no label for the
current catalog version, in one `ask-many` batch. Its decisions log under
`$RUVER_HOME/insights/.ruver-bulma/`, so `/bulma report --hook insight.classify`
shows agreement with the regex. The hook defaults to `shadow`, so labels are
logged and the table stays regex-only. Promote it with
`/bulma power balanced insight.classify` once the report shows the labels can be
trusted. The cache keeps the raw answers, so labels made under `shadow` start
counting after promotion without a new call.

Under the current power, a label counts only where it clears the threshold:

- `cluster` replaces the regex match for that row.
- `generalizable` decisive-no drops the row as a one-off. The header prints how
  many.
- `lesson_for` fills the `lesson` column: `implementer`, `reviewer`,
  `repo_rule`, `none`, `mixed` (no majority), or `-` (no acted label).

## Read the table

- `per PR` is misses per reviewed PR in the window. Compare it with
  `prev per PR`. Raw counts mislead when review volume changes.
- `trend`: `down` or `up` means a change of 25% or more. `need data` means
  either window has fewer than 10 PRs. Do not conclude anything from it.
- `lesson` says where the fix belongs. `implementer` means a rule for the coder
  and the fd reviewer, not only a review check. `repo_rule` means the target
  repo's `CLAUDE.md`. Prefer it over `guard` when they disagree: `guard` says
  what exists today, `lesson` says where the lesson should live.
- `guard` names the skill section that should make the cluster shrink.
  `repo rule` means the fix belongs in the target repo's `CLAUDE.md` or
  `AGENTS.md`, not in a skill.
- `unclustered` rows and their keywords are where a new cluster starts.

## Output

Print the script output as-is. Then, in the chat language, one line per
cluster that needs action, strongest evidence first:

- guard is a skill section and trend is `up` or `=` after that section
  changed: the change did not work. Say so and propose rewording that
  section. Do not stack a second rule on top of it.
- no guard fits and the cluster spans 5 or more PRs: propose a new check,
  quoting two or three patterns from `--json` `examples`.
- guard is `repo rule`: propose the one-line rule for that repo's `CLAUDE.md`.
- unclustered keywords repeat 5 or more times: name the candidate cluster.

Stop with one question: which proposals to turn into a draft PR. Only on a yes,
edit the skill on a new branch, run the repo gates, and open a draft PR. Never
edit a skill without that yes, and never merge. Stop.
