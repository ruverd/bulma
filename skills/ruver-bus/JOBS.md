# Jobs, workers, QA queue

**One home.** Developer, reviewer, lstm, and QA admit/enqueue here.
Do not copy this table into those SKILL.md files.

## Disk

Under `$RUVER_ROOT` ([DISK.md](DISK.md)). **Never** the git root.

```
.ruver-bus/
  JOBS.md                 # registry + qa_active / qa_waiting
  jobs/<id>/
    STATE.md              # worker / parked job (not the foreground)
    qa-request.md         # parked QA_REQUEST
    RESULT.md             # worker return
```

Init JOBS from [templates/JOBS.md](templates/JOBS.md) if missing.

## Job id

`dev-<TICKET|pr-N>` · `rev-pr-N` · `lstm-pr-N` · `qa-pr-N`

## Main is busy

Last line of `STACK.md` is `qa` or `triage`, **or** a
**foreground** developer/reviewer/lstm job is not terminal
(`done` / `done_notes` / `escalated`).

Idle: empty stack, or only terminal jobs.

## Interrupt (user / envelope while a graph runs)

| Incoming | Active main | Action |
|---|---|---|
| developer ticket / fix | busy | **worker + worktree**. Do not steal main. |
| reviewer | busy | **worker + worktree**. Do not steal main. |
| lstm | busy | **worker + worktree**. Do not steal main. |
| `QA_REQUEST` / `/ruver-qa` | other QA `qa_active` set | **enqueue**. Never start a second QA. |
| `QA_REQUEST` / `/ruver-qa` | no `qa_active` | start QA (claim `qa_active`). |
| developer / reviewer / lstm | QA or triage on main | worker + worktree. **Do not abort QA.** |

Never two `plan`/`execute` QA runs. Browser / e2e / HTTP QA
on this machine is **one slot**.

## Developer / reviewer / lstm — admit

1. Register the job on `JOBS.md`.
2. If main is **idle** for this call → `lane=foreground`.
   Write `.ruver-<kind>/STATE.md`. Continue the graph.
   Use a worktree + branch unless already isolated.
3. If main is **busy** → `lane=worker`:
   - Create a worktree ([Worktree](#worktree)).
   - Spawn **one** `general-purpose` subagent ([Worker](#worker)).
   - Record `worktree`, `worker_id`. Chat (`ruver-memory`): job id + path.
   - **Do not** leave the graph that already owns main.

Foreground job keeps `.ruver-developer/STATE.md` (or reviewer / lstm).
Worker jobs use `.ruver-bus/jobs/<id>/STATE.md` only.

## Worktree

Every task, including foreground, gets its own worktree and branch from
`origin/main` (or the repo default). If the host already created a
worktree, keep the **directory**. The **git branch** is still the name
below. Host isolation on `{login}/dev-4525` (or any tracker
`gitBranchName` that is not `feature/<id-lowercase>`) is not the task
branch: `git checkout -b feature/<id-lowercase>` from `origin/main` if
the name is free, else check that name out. Do not open the PR from
`{login}/<id>`.

If a UI route already exists, capture Before after this worktree exists
and before the first RED
([evidence.md](../ruver-feature-delivery/nodes/evidence.md)).

`git fetch origin` before creating any branch or worktree.

Prefer host `spawn_worker` with worktree isolation ([ruver-host](../ruver-host/SKILL.md)).
Do not also pass `cwd` when isolation is a worktree.

Else git fallback (`.worktrees/` if the repo gitignores it, else a sibling dir):

```bash
git fetch origin
git rev-parse --show-toplevel
git check-ignore -q .worktrees
git worktree add ".worktrees/<id>" -b "<branch>" origin/main
```

Branch name:

- Tracker id (`DEV-4525`, `ABC-123`): always `feature/<id-lowercase>`.
  `DEV-4525` → `feature/dev-4525`. Ignore tracker `gitBranchName`.
  Ignore `{login}/<id>`.
- Free goal: `feature/<slug>`.
- Name taken: append `-<n>`. Never reuse. Never force.
- Resume with STATE: reuse STATE.branch only when it already matches
  this rule. Else move to `feature/<id-lowercase>`.

Never touch another agent's worktree, branch, or uncommitted files.
Do not nest a worktree inside another worktree.

Scope check at fd tickets, once files are known: `gh pr list` and
`gh pr diff <n> --name-only`. Overlap: DECIDE, or ASK last resort.

Never `--force`. `--force-with-lease` only on the task branch, never on
main/master.

Shipper: rebase onto `origin/<base>` and re-run the hard gate before push.

Lockfile conflict: regenerate with the discovered `pkg`. Never hand-merge.

Shared resources: `lsof -i :<port>` before trusting a port. No migration
on a shared DB. Install deps inside the worktree with the discovered
`pkg` only if they are missing there.

Keep the worktree until the PR is merged or closed. Cleanup is
`git worktree remove` + `git branch -D` by a human after `ruver status`
lists orphans. No auto-remove. `ruver status` also prints the cwd job
Walk when fd STATE exists (plugin health first, then the job).

Do not run the full test suite as a baseline (too heavy).

## Worker

Child type: general-purpose ([ruver-host](../ruver-host/SKILL.md) `spawn_worker`).
**Never** spawn types `ruver_developer` / `ruver_qa` / `ruver_triage` /
`ruver_reviewer` / `ruver_lstm`.
Worker **must not** spawn children.

Prompt must include: job id, worktree path (or “host worktree”),
PR/ticket, “execute the skill **yourself** — no ruver-* / ruver-fd-*
spawns”, never merge, stay draft.

| kind | Worker does |
|---|---|
| developer | `ruver-feature-delivery` nodes inline (or Fix contract). Draft PR. Write `jobs/<id>/RESULT.md`. |
| reviewer | `ruver-code-review` for **one** PR only. Write `RESULT.md`. |
| lstm | `ruver-lstm` nodes inline for **one** PR. Same branch. TDD via coder contract (spawn `ruver-fd-coder` on foreground; inline on depth-1 worker). Write `RESULT.md`. |

On RESULT: update JOBS. Developer worker with green+MERGEABLE →
[Enqueue or start QA](#enqueue-or-start-qa). CI pending → start
`ruver-goal` loop for **that** PR (one loop per PR).

## The QA slot is a lease, not a lock

A QA run reaches `verdict` only on the happy path. It also dies `handed_off`
on a context limit, `escalated`, or with the session — and `verdict` is the
only node that clears the slot. A dead claim therefore parks every later QA in
`qa_waiting` for good, while the graph keeps answering with a queue position,
which reads exactly like working software. So the claim carries a timestamp and
expires.

```yaml
qa_lease_minutes: 90   # default; raise on suites that legitimately run longer
```

Claim = write `qa_active` and `qa_claimed_at` in the same edit.

The slot is **free** when any of these holds:

| | Condition |
|---|---|
| 1 | `qa_active` is empty |
| 2 | `qa_active` is **this** job id |
| 3 | **expired** — `qa_claimed_at` is more than `qa_lease_minutes` in the past |
| 4 | **abandoned** — the claiming job's row is terminal (`done`, `done_notes`, `escalated`, `handed_off`), or `jobs/<qa_active>/` is gone |

**Renew** while you hold it. `execute` is the long node: rewrite
`qa_claimed_at` every time you append to `FINDINGS.md`, so a slow but live QA
never reads as expired.

**Take over** an expired or abandoned claim:

1. Append to `log.md`: `<ISO> reclaim qa_active=<old> reason=expired|abandoned`,
   and a `reclaim` row to `RUN_LOG.tsv` ([LEDGER.md](LEDGER.md)).
2. Overwrite `qa_active` and `qa_claimed_at` with your own.
3. Reset `.ruver-qa/STATE.md` from the template. The old STATE describes
   another PR.
4. Say in chat which claim you took and why. A silent takeover hides a crash
   the user needs to know happened.

**Release** on every terminal exit, not only `verdict`: `blocked`,
`handed_off`, `escalated`, and the `stop` edges out of `resolve` and `plan`.
Clear both fields, then dequeue. Releasing a slot you no longer hold is a
no-op, so check `qa_active` is still your id first.

## Enqueue or start QA

Slot free by the table above.

1. Write `jobs/<id>/qa-request.md` (full `QA_REQUEST` body).
2. **Free:** write `qa_active=<id>` and `qa_claimed_at=<ISO UTC>` in one
   edit. Copy to `ENVELOPE.md`. Bus switch to `qa`.
3. **Taken:** append `<id>` to `qa_waiting`. Do **not** switch.
   Do **not** touch `.ruver-qa/STATE.md`. Chat: queue position.

Triage stacked on QA still holds the slot (`qa_active` stays).

## After a QA verdict

1. Write `QA_RESULT`. Pop. Run developer `apply_qa` for that job
   **to completion** (do not skip).
2. Clear `qa_active` and `qa_claimed_at`.
3. If `qa_waiting` is non-empty: dequeue head → `qa_active`,
   copy `jobs/<id>/qa-request.md` → `ENVELOPE.md`, push `qa`,
   load QA graph. Reset `.ruver-qa/STATE.md` from the template
   for the new PR.

Standalone `/ruver-qa` (no developer on stack): same dequeue
after verdict.

## Anti-patterns

- Two QA `execute` at once
- Aborting QA because a new ticket arrived
- Spawning a graph type as the worker
- Worker spawning fd coder / another graph
- Overwriting `.ruver-qa/STATE.md` for a queued PR
- Holding `qa_active` past a `handed_off`, `escalated` or `blocked` exit
- Taking over an expired claim without saying so in chat
- `git worktree add` when `isolation: "worktree"` is available
