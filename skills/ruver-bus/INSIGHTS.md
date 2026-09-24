# Review observations

`$RUVER_HOME/insights/observations.jsonl`. Global, one file for every repo,
outside git. Append-only. One line per **human** review comment a graph
processed, plus one line per defect our own feature-delivery gates caught
before the PR existed (`source: fd`). An **observation, not a gate**: no node reads it to decide
anything. It exists so a lookback can count what human reviewers catch and
the agents miss, and later check whether a skill change made that count
drop.

Writers: `ruver-lstm` `verify` and `ruver-reviewer` `code_review` (human
comments), and `ruver-feature-delivery` `reviewer` and `quality` (our own
catches). Nothing else writes here. The lookback compares the two: what the
gates catch before the PR against what humans still catch after it.

## Who counts as human

Skip, and write nothing, when any holds:

- author login ends in `[bot]`, or GitHub reports `user.type` `Bot`
- the comment, or the review it belongs to, carries a `<!-- ruver-review:`
  marker (that is our own review, even when posted under a person's login)
- author is the PR author (replies to review, not review)

## Write

```bash
python3 ../ruver-bus/scripts/observe.py \
  --comment-id <id> --pr-ref <owner/repo#n> --sha <head> \
  --reviewer <login> --source lstm|reviewer \
  --axis <axis> --severity critical|important|nice_to_have \
  --claim-true yes|no|unknown \
  --pattern "<one generalized sentence>" \
  --path <bound path> --line <n> --keywords "a,b,c" \
  --ours-open "<open= value of the latest ruver-review marker>"
```

Resolve `../ruver-bus/` from the calling skill's directory. The script
exits 4 on invalid input and writes nothing. It prints `duplicate` when the
comment id is already in the file, so re-running a PR never inflates counts.

| Field | Rule |
|---|---|
| `--axis` | The `ruver-code-review` axis the comment would have been filed under. `other` only when none fits |
| `--severity` | `critical` = data loss, security, or wrong money or permission. `important` = a real defect or a missing test for one. `nice_to_have` = everything else |
| `--claim-true` | lstm: the `claim_true` it just verified. reviewer: `unknown` (it does not verify other people's comments) |
| `--pattern` | The reusable rule the comment teaches, in one sentence of at most 300 chars. No repo, file, symbol, ticket, or people names. `Guard added on manual save is missing on autosave` is right. `Fix useSave in Editor.tsx` is wrong |
| `--ours-open` | Copy the `open=` value from the newest `<!-- ruver-review:` marker on the PR. Omit the flag when the PR has no marker. The script turns it into `caught_by_ours`: `yes` if our review had a finding on the same path within 10 lines, `no` if not, `unknown` without a marker |

`caught_by_ours` is computed from evidence, never guessed. The legacy
`would_existing_agent_catch_it` field mirrors it for older readers.

## Never

- Write raw comment text. The pattern is the only free text.
- Write a human-comment row (`lstm`, `reviewer`) for a bot, our own GitHub
  review (the `ruver-review` marker), or the PR author. Our gates write
  `source: fd` rows instead.
- Edit or delete lines. A wrong line stays; the next lookback outvotes it.
- Stop or change a disposition because writing failed. Note it in chat and
  continue.

## Our own catches (`source: fd`)

The fd `reviewer` node writes one row per finding behind a `fail` verdict. The
`quality` node writes one row per finding it fixed. There is no comment and
often no PR yet, so the row is keyed by job and finding:

```bash
python3 ../ruver-bus/scripts/observe.py --source fd \
  --reviewer ruver-fd-reviewer|ruver-fd-quality \
  --job <STATE job_id> --finding-id <kebab-slug> [--pr-ref <owner/repo#n>] \
  --axis <axis> --severity critical|important|nice_to_have --claim-true yes \
  --pattern "<one generalized sentence>" --path <path> --line <n>
```

- `--finding-id` stays the same across review laps for the same defect, so a
  lap that finds it again prints `duplicate`. Use a new slug only for a new
  defect.
- The `--pattern` rule is the same as for human comments: the reusable
  lesson, with no repo, file, or people names.
- The row is stored with `caught_by_ours: self`. The lookback never counts it
  as a miss and never counts its job as a reviewed PR.
- Record only defects: spec misses, missing tests, and quality or security
  findings. Do not record style nits the gate waived.

