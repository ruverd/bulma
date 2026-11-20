# Stacked delivery

Each child owns a branch, a worktree, and a pull request. The orchestrator
runs the same feature-delivery worker for each child and owns CI, the developer
gates, and re-entry. The umbrella is the last pull request. It integrates the
children into the repository's default branch.

## Choose the delivery shape

- **Single tracker issue with child discovery:** feature delivery's
  [tracker discovery](../bulma-feature-delivery/LINEAR.md#child-discovery)
  checks for actual children before checkout. One or more open children select
  stack mode, including a parent with only one open child. A leaf or a parent
  with no remaining children takes ordinary delivery.
- **Several issue IDs or an explicit stack request:** resolve the actual tasks
  and dependency edges before building the stack.
- **Locally planned feature:** [tickets](../bulma-feature-delivery/nodes/tickets.md)
  defaults to one PR with a coder per slice. Select a stack when the slices
  justify distinct review, validation or delivery boundaries. For example,
  ship a disabled path through one PR and its activation through the next.
  Keep the parent acceptance criteria, rollout decisions, and each slice's
  tests. Both plans use local tickets and the existing worker contract.

The relay below uses GitHub and a single repository. Select it only for
shipping requests with PRs enabled. For a tracker parent on another forge,
report the stack capability as blocked before publishing. A fullstack pair
across repositories keeps its [own workflow](../bulma-feature-delivery/FULLSTACK.md).

## Plan and state

Keep `$BULMA_ROOT/.bulma-developer/STACK.md` as the job registry. Save the
immutable branch and task plan beside it as `STACK.plan.json` before creating
refs. Resume the saved plan for the same parent, even as children are marked
complete in the tracker. Re-read changed requirements and dependencies before
dispatching the affected child. If membership or dependencies changed, report
the difference and reconcile it explicitly with existing PRs. Never replace a
published plan or infer it from PR numbers.

| child | job_id | depends_on | branch | worktree | worker | pr | sha | ci | ci_fix_loops_used | status |
|---|---|---|---|---|---|---|---|---|---|---|

Add the umbrella as its own row. Record the candidate SHA before a worker
pushes, and record gate results against the exact PR head and observed base
tip. Store worker state, RESULT and QA envelopes under the existing
[JOBS](../bulma-bus/JOBS.md) paths. Use one writer for the stack registry.

Use `python3 <fd-skill>/scripts/stack.py plan --repo <owner/repo> --default
<branch> --anchor <origin-default-sha>` with JSON on stdin. The developer
route uses the default `--qa final`. Direct feature delivery keeps its
CI-only policy with `--qa none`. Get the default
from origin's symbolic HEAD and fetch its tip. Confirm origin is the selected
GitHub repository. Input:

```json
{
  "source": "linear",
  "parent": {"id": "ABC-10", "task": "Parent issue URL and acceptance context"},
  "parent_ids": ["Parent issue UUID", "ABC-10"],
  "children_complete": true,
  "children": [
    {"id": "ABC-12", "task": "Child issue URL and acceptance context", "parentId": "Parent issue UUID", "statusType": "started", "depends_on": ["ABC-11"]},
    {"id": "ABC-11", "task": "Child issue URL and acceptance context", "parentId": "Parent issue UUID", "statusType": "started", "depends_on": []}
  ]
}
```

Manual requests use `source: explicit`. Local plans use `source: planned`
for separate PR boundaries or `source: integrated` for one PR. Use a stable
parent slug and stable slice IDs when no tracker ID exists. For local and explicit
inputs omit `parent_ids`, `children_complete`, `parentId` and `statusType`.
The planner orders actual dependency edges and uses issue IDs as the tie
break for independent work. Dependencies outside the stack stay in the task
contract and are checked by the usual blocker flow.

## Branch and PR order

For two children, the merge destinations are:

| Position | PR head | PR base |
|---|---|---|
| First | `feature/abc-11` | `feature/abc-12` |
| Second | `feature/abc-12` | `feature/abc-10` |
| Final / Umbrella | `feature/abc-10` | repository default |

Open PRs in merge order. Before dispatching a child, create its destination
branch at the saved default tip if absent. The first worker starts at that
tip. Every later worker starts from the actual commit delivered to its
branch by its predecessor's human merge. This supports changes that depend
on code introduced by an earlier child, including edits to newly added
files. Forwarded PRs contain the accumulated changes. Summarize the current
slice and link the earlier merges in each body. Use the incoming commit as
the slice's validation baseline and the actual PR base for cumulative review.

The final worker starts at the last child's merge on the umbrella branch.
It validates the combined acceptance criteria and packages the existing
history through the normal review, tester, evidence and shipper gates. It
does not implement a new slice or create an empty commit to open the PR.
If the default branch advanced, validate the combined merge candidate
against its current tip in a disposable checkout. Keep integrated merge
commits on the umbrella branch. Surface real conflicts through the existing
fix/escalation gate, preserving that history. Repeat base-sensitive proof
after a base change.

## Run and resume

1. Reconcile with `python3 <fd-skill>/scripts/stack.py reconcile --plan
   <STACK.plan.json> --checkout <checkout>`. It verifies origin's refs and
   GitHub's real head/base links, walks the chain to the default, and confirms
   each merge result is in its receiving branch or the next PR's head.
   Closed unmerged PRs, diverged refs, ambiguous history and mismatched bases
   stop the stack. Do not retarget a legacy main-based PR, replace a branch,
   or report a guessed merge order.
2. If the next row has no PR, rerun with `--prepare --gates <file>`. Pass
   the existing registry's verified proof as JSON keyed by task ID with
   `head`, `base`, `ci`, and `review` (`pass` or `skip`). When CI is
   out of scope, include the verified `stack-ci.py` output as `ci_scope`.
   The helper checks merged predecessors against these receipts before
   creating a missing destination ref with an empty-ref lease. Then spawn one [worker](../bulma-host/SKILL.md#spawn_worker)
   in a recorded worktree at `active.start_sha`; a successor's source branch
   already exists remotely. If local planning already reserved the umbrella
   branch in an isolated worktree, reuse that clean worktree for the final
   worker and fast-forward it to the verified start SHA. Reuse each job,
   worktree and worker receipt on
   resume. When a push succeeded before PR creation was recorded, pass
   `--candidate <recorded-sha>` and rerun shipper on that same head.
3. Worker prompt: run feature delivery **end-to-end yourself, in this worktree**,
   inline. Supply job ID, checkout, full child task or tracker URL, parent
   goal, dependencies, actual `head` and `base`, `start_sha`, `base_sha`,
   `position`, and `final`. Persist this as `stack_member` in fd STATE.
   Never recurse into stack, renumber, or merge. Write the existing
   `RESULT.md` with status, PR URL, SHA, CI and the fd STATE path.
4. On every wake, reconcile before acting. For the active PR use the existing
   `gh pr checks` CI and applicable review gates. In developer mode each open PR walks
   mergeability and bot review. Schedule integrated QA only when
   `active.qa_required` is true for the umbrella. Require the combined
   acceptance and evidence on its current head. A child result never
   substitutes for final QA. Keep existing external QA-provider and
   repository check requirements.
   A **fresh** fix worker resumes the same row at `ci_watch` on red, up to
   `ci_fix_loops`. Any head or base drift invalidates the affected gate
   evidence. Verify expected and required checks. A child may pass the CI
   gate with the verified `out_of_scope` result in
   [CI_DELIVERY.md](../bulma-feature-delivery/CI_DELIVERY.md#stack-child-ci).
   Report **CI out of scope for this base** with the local test receipt.
   Unknown or missing expected checks still block. The default-targeted
   umbrella keeps the usual hosted CI gate.
   Keep the single QA lease and route the result by the umbrella's job ID.
5. When that row passes, wait for the human merge and verify its result before
   starting the next row. Use one `schedule_wake` to re-enter **stack**.
   If a PR merged early, require verifiable gate evidence for its merged head
   and the relevant base. Escalate a missing prerequisite before advancing.
   For the umbrella, report verified delivery and its actual review status
   after its gates pass. If it is a manual draft, report that status. The human
   owns the final merge. A later resume can confirm that merge.

Only publish the verified prefix of linked PRs as merge order. Report
unopened rows as planned destinations, with the next action and current
CI/QA status. The shipper uses title prefixes such as `[First]`, `[Second]`,
`[Third]` and `[Final / Umbrella]`. Reapplying a position replaces the
managed prefix. Manual drafts retain their draft status. Bulma never merges.
