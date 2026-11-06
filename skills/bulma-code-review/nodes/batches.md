# 4b. Batched deep pass — very large PRs only

A normal PR, including a large one, never enters this node. Batches exist so a
very large PR (a stack cleanup, a mass rename) gets full coverage instead of a
partial review after 15 files.

## When

Run after [fetch.md](fetch.md) §4.0 on a **deep** pass:

```bash
python3 scripts/batch-plan.py plan --dir "$REVIEW_DIR"
```

| Output | Action |
|---|---|
| `"batched": false` | stay on the normal deep pass and its caps |
| `"batched": true` | follow this node |

The script marks a PR very large when one of these holds:

- more than 50 changed files
- more than 5000 changed lines (additions + deletions)
- GitHub refused the full diff (HTTP 406), so `snapshot.json` has
  `diff_source=local`

Light passes never batch. A delta that is itself very large has already forced
the full diff and a deep pass.

## Plan

`batches.json` lists batches of at most 15 files and about 1500 changed lines.
Hotspot files go first (auth, permissions, billing, migrations, public API,
secrets), and files from the same directory stay together. Lockfiles,
snapshots and binary assets go in one final `mechanical` batch that gets a
patch skim only. Each `batches/<NN>/` holds `FILES.txt` and the `PATCH.diff`
cut from the full PR patch. `missing_patch` lists files with no text diff
(binaries, pure renames); cover them from the file list.

## Run the batches

Phase 1 (`AC.md`, spec checklist) runs **once** on the main thread before any
batch. Every batch reviews against that same `AC.md`.

Spawn one fresh worker per batch ([bulma-host](../../bulma-host/SKILL.md)
`spawn_worker`), at most 4 at a time. Pass paths, never diff text:

- `REVIEW_DIR`, the batch dir, `HEAD_SHA`, `AC.md`
- the axes in [review.md](review.md) and [EVIDENCE.md](../references/EVIDENCE.md)
- the constraint: **review only the files in this batch's `FILES.txt`; read
  source at `HEAD_SHA`; do not post anything on GitHub; do not spawn workers**

Each batch has the deep caps of [SKILL.md](../SKILL.md) §Caps on its own: 15
full-file Reads, 8 caller queries. A Read outside the batch is allowed only to
follow a caller or contract of a file in the batch, within those caps.

Each worker writes, in its batch dir:

- `coverage.json` — one row per file in `FILES.txt`: `{"path", "checked"}`
- `findings.json` — the findings from [review.md](review.md), before binding

A host without workers runs the batches one after another on the main thread,
clearing file bodies from context between batches. Same outputs.

## Merge

```bash
python3 scripts/batch-plan.py merge --dir "$REVIEW_DIR"
```

The script writes the merged `coverage.json` and `findings.json` (deduplicated,
blockers first) into `REVIEW_DIR`. Then continue at [review.md](review.md)
Phase 10 (bind) with the full `PR_PATCH.diff` and the merged findings. Cross-batch
classes collapse to one finding with `instances`, like any other pass.

| Exit | Meaning |
|---|---|
| 0 | every batch finished and every file has a coverage row |
| 1 | a batch failed or left files unchecked; re-run only those batches once, then merge again. Still incomplete → no artifact this run; name the uncovered files in chat |
| 2 | manifest missing or for another head; re-plan |

The critic ([critic.md](critic.md)), the verdict and the publish run **once**,
on the merged ledger. Caps on published findings (10) and nits (5) apply to the
whole PR, not per batch.

## Publish

One review artifact for the whole PR, same template
([publish.md](publish.md)). Never one review per batch. The `Pass` row reads
`deep, batched (N batches)`. The `Coverage` row counts files across all
batches. The Coverage details table adds a `Batch` column. The marker keeps
`pass=deep` and adds `batches=N`.
