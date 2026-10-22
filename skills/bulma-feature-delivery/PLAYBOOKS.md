# Task playbooks

Playbooks define the proof a task needs. [GRAPH.md](GRAPH.md) still owns every
execution edge, review gate, retry cap and delivery permission. A playbook never
authorizes a skipped gate, a merge, external messages or extra product scope.

## Select once

During triage, classify the goal, then run this skill's helper:

```bash
python3 scripts/playbook.py select --kind bug
python3 scripts/playbook.py select --kind chore --playbook refactoring
```

The default comes from [playbooks.json](playbooks.json). Explicit intent wins.
Use `refactoring` for behavior-preserving structural work, `performance` for a
measured optimization and `skill-change` for agent instructions. Other chores
keep `maintenance`; they do not acquire feature discovery or new-test obligations.
Do not infer a refactor from a rename that also changes accepted behavior.

The helper returns `playbook`, `playbook_version`, `playbook_digest`, its contract
path and a checklist. Read only that contract. Persist the three identity fields
in STATE frontmatter and the checklist under `## Playbook`. This is the only
playbook checklist; the host todo list displays it rather than maintaining a
second copy. Each step belongs to an existing graph node.

Each row records `pending`, `pass`, `fail` or `skip`, a proof file path, and a
reason. Optional work stays visible when skipped. A required step cannot be
skipped. Paths are absolute files under `$BULMA_ROOT`, outside the product tree;
references to tests or source go inside those evidence files. Do not put secrets
in them. The coordinator owns STATE and these rows.

Before the first product edit, complete any baseline step. On resume, preserve
the selected identity and completed rows while reconciling their invariants.
A changed catalog digest requires reading the changed contract and reconciling
affected obligations, not silently reinitializing the run. Older STATE without
playbook fields selects once from its existing goal and work_kind. Never invent
before evidence for work already implemented; recover the original revision or
report the missing proof.

## Complete

Run `python3 scripts/playbook.py check --state <STATE.md> --repo <worktree>`
before final evidence or `done_report`. It rejects missing required proof,
unknown rows, stale contracts and unexplained optional skips. Refactoring also
requires a current successful [equivalence comparison](playbooks/refactoring.md).
For refactoring, also pass `--environment <fingerprint>` freshly recomputed from
the current toolchain, configuration and fixtures. Do not copy it from a receipt.
Existence checks for other proof files do not judge their content. Review and
tester must read them against the selected contract; the helper is not approval.

Investigation takes the read-only spike edge before fullstack or implementation
routing. It ends at `done_report`, with sources and an answer, no PR or product
changes. A request for implementation is a new delivery goal, not permission
inferred from an investigation recommendation.

Only task-specific proof is added. Existing TDD, quality, independent review,
current-tree evidence and external QA ownership remain in force. On a new head
or changed environment, invalidate affected after evidence; preserve historical
baselines. Give workers only their applicable obligation and evidence pointers.
