# Full-stack (frontend + backend)

When the task spans **frontend and backend** in **two git roots**,
the orchestrator does not implement everything in one repo. Same
**branch** on both. Sibling names come from [PRODUCT.md](PRODUCT.md),
never from this file.

`scope: mono` (both apps in one git root) is **not** this path. Stay
on the current checkout.

Ticket context still comes from the project MCP (tracker, design tool, …).

## 1. Detect

Set `scope: fullstack` only if [PRODUCT.md](PRODUCT.md) resolved a
sibling **and** the ticket/goal needs both sides.

```yaml
scope: fullstack
repos:
  frontend: <from env / AGENTS.md>
  backend: <from env / AGENTS.md>
branch: feature/<id-lowercase>
```

Empty sibling → do not enter this path.

## 2. One branch

`feature/<id-lowercase>` on both repos
([JOBS.md](../ruver-bus/JOBS.md) §Worktree).

**Forbidden:** different branch names across repos unless the user asked.

## 3. Worktrees

Default (always works):

```bash
git -C <backend-root> fetch origin
git -C <frontend-root> fetch origin
git -C <backend-root> worktree add ../<backend>-<branch> -b <branch> origin/main
git -C <frontend-root> worktree add ../<frontend>-<branch> -b <branch> origin/main
```

Reuse if that worktree already exists. Store paths in STATE:
`worktrees.backend`, `worktrees.frontend`.

If `orca` is on PATH and `orca status --json` works, you **may**
create those worktrees with `orca worktree create` using the names
from PRODUCT.md. Confirm flags with `orca skills get orca-cli`.
Orca is optional. Missing Orca is not a blocker.

## 4. Workers

Host `spawn_worker` ([ruver-host](../ruver-host/SKILL.md)) on each worktree.
Same branch. Prefer BE → FE when the UI needs a new contract.

If Orca orchestration is up, you **may** use `run-create` /
`task-create` / `worker-start` / `check`. Confirm flags with
`orca skills get orchestration`. If it is not up, host workers on
the git worktrees are the path. Do not stop.

Coordinator:

- waits for both workers
- does **not** edit product `src/`
- may edit `$RUVER_ROOT/.ruver-feature-delivery/*` and rebase conflicts

Tracker MCP for the ticket. Never a vendor CLI.

## 5. Spec each worker receives

- worktree path + **identical** branch
- tracker-context (AC)
- backend: contracts, migrations, API TDD
- frontend: UI_DESIGN_SYSTEM + Figma if any + contract consumption
- never merge; draft PR if `open_pr`
- thermo fix all in that worker's repo before shipping that repo

## 6. Dual ship + CI green

For **each** repo, after the worker is ok:

1. quality / thermo in that worktree
2. commit + push on the **same** branch
3. draft PR (base main) linking the ticket + the sibling PR
   - reviewers/assignee per [PRODUCT.md](PRODUCT.md)
4. **ci_watch** on **each** PR

**Delivered** only when **FE and BE** are green.

```yaml
prs:
  backend: https://github.com/<org>/<backend>/pull/N
  frontend: https://github.com/<org>/<frontend>/pull/M
```

## 7. Anti-patterns

- Implementing BE+FE only in the frontend repo
- Different branch names across repos
- Worktree in only one repo
- Treating Orca as required
- Inventing a sibling repo name
- Using `orca linear` to read the ticket
