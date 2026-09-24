# Self-improving loop: quality lookback first, then reconcile and watchdog

Status: proposed

The graphs improve only when someone edits a skill by hand. Two signals
already exist on disk and nothing reads them:

- A past review pipeline appended human-review observations to
  `~/.bulma/insights/observations.jsonl` (pattern, axis, severity, and a
  self-assessed "would an existing agent catch it"). About 1100 rows over
  seven weeks and about 220 per-PR reports with suggested edits. No
  suggestion became a skill diff. Collection stopped in July.
- Run state under `~/.bulma/*/.bulma-*/STATE.md`. Dozens of jobs sit in a
  non-terminal status (`shipping`, `ci_watching`, `waiting_ci`,
  `delivering`) for days. Some of them finished outside the graph and
  their state was never updated.

Builder's factory skills (`BuilderIO/skills`) frame the same problem as
two loops: a watchdog that finds stalled work, and a periodic lookback
that asks "what came back after we thought we fixed it" and prefers one
fix at the shared boundary over another patch per caller. Their input is
product telemetry. Ours is the graphs' own runs and the human review on
their PRs, so the lookback targets skills, not product code.

Decision, in order:

1. **Quality lookback: `/bulma lookback`.** Cluster what human reviewers caught and agents
   missed, compare each cluster against the current skill text, and
   output one proposed skill diff per real gap, shipped as a PR to this
   repo. Never self-applied. Each cluster names the skill section that
   guards it. Verification is the same count on the next
   window, normalized per PR. A cluster that does not shrink means the
   change failed, and the fix is to reopen that change, not to add a
   second rule. Repo-specific patterns (a vendor SDK quirk, a project's
   error-reporting rule) go to that repo's `CLAUDE.md` or `AGENTS.md`,
   never to a skill. The first report ran by hand over the existing file
   and found four gaps in `bulma-code-review` (sibling-path parity,
   multi-store partial failure, tests that cannot fail, unvalidated input
   into typed columns). One cluster was already fixed by `bind-findings.py`.
   Jev labels each observation (`insight.classify`): its cluster, whether
   it generalizes, and whether the lesson belongs to the implementer, the
   reviewer, or the repo's own rules. A lesson that could have been avoided
   while writing the code goes to the coder, not only to review. Jev is
   used per observation, where volume allows calibration, and not to
   decide whether a whole cluster deserves a change: that stays a
   threshold plus the user's yes. Implementer lessons live in
   `bulma-feature-delivery/LESSONS.md`, and each coder brief carries the
   current repo's top recurring misses (`bulma/scripts/lessons.py`), so
   the loop prevents the defect as well as catching it.
2. **Collection.** `bulma-lstm` and `bulma-reviewer` append one
   observation per human comment they process, using the existing schema.
   Without this, step 1 has nothing to verify against.
3. **Reconcile, then watchdog: `/bulma watch`.** Scans every workspace
   under `$BULMA_HOME`. A PR that `gh` reports merged or closed counts as
   finished upstream and is cached in `$BULMA_HOME/bulma-watch.json`. It
   never edits the other graph's STATE. A missing workspace directory is
   orphaned. Everything else is listed with its next command. Report only.
   The host scheduler runs it. On the first real run, most of the jobs that
   looked stalled were PRs already merged or closed on GitHub.
4. **Process lens of the lookback.** Once reconcile makes state
   trustworthy, cluster where runs die (node, status, lap count from the
   `bulma report` ledger) and propose graph edits the same way.

Both loops live in `bulma`, the single entry point: the other graphs
become stages bulma loads, not commands a user types. Neither loop needs
Jev, so both are local verbs (`watch`, `lookback`) that run without
`TYPESAFE_API_KEY` or `doctor`, like `report`. Observation collection
stays in the `bulma-lstm` and `bulma-reviewer` nodes, because those are
the only places that read review comments.

Deferred, not rejected: product-signal intake (error trackers, chat,
issues). `bulma` is heading toward a software factory, and intake is the
factory's front door. It waits until the watchdog and lookback make the
internal loop trustworthy, because more input into an unreliable loop only
multiplies stalled work.

Rejected for now:

- Policy-based auto-merge: `never_merge` is a design rule.
- A separate human-decision digest: no `waiting_user` job sat longer than
  three days, so it becomes a section of the watchdog report.
- Auto-applying `bulma` threshold suggestions: the decision ledgers hold
  2 to 8 rows each, too few to tune.
- Recurrence memory inside triage: it ran 15 times. It comes for free once
  the lookback exists.

Decided (2026-09-24): the watchdog only reports. On the day it shipped,
auto-resume would have applied to one stalled item, because items that need
the user and orphaned items cannot be resumed. The risks are pushing old work
onto a branch that moved, spending tokens on work abandoned on purpose, and
colliding with a live session in the same worktree. Revisit when
`/bulma watch` regularly shows three or more stalled items. Scheduling the
report (`/loop 6h /bulma watch`) is the supported middle ground.

`insight.classify` was promoted to `balanced` the same day. In a sample of 10
of the 37 confident labels that disagreed with the regex, the regex had
matched on a stray word (`emit`, `sibling`, `pagination`) and Jev picked the
right cluster in all 10.
