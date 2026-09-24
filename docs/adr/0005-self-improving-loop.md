# Self-improving loop: quality lookback first, then reconcile and watchdog

Status: proposed

The graphs improve only when someone edits a skill by hand. Two signals
already exist on disk and nothing reads them:

- A past review pipeline appended human-review observations to
  `~/.ruver/insights/observations.jsonl` (pattern, axis, severity, and a
  self-assessed "would an existing agent catch it"). About 1100 rows over
  seven weeks and about 220 per-PR reports with suggested edits. No
  suggestion became a skill diff. Collection stopped in July.
- Run state under `~/.ruver/*/.ruver-*/STATE.md`. Dozens of jobs sit in a
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

1. **Quality lookback.** Cluster what human reviewers caught and agents
   missed, compare each cluster against the current skill text, and
   output one proposed skill diff per real gap, shipped as a PR to this
   repo. Never self-applied. Verification is the same count on the next
   window, normalized per PR. A cluster that does not shrink means the
   change failed, and the fix is to reopen that change, not to add a
   second rule. Repo-specific patterns (a vendor SDK quirk, a project's
   error-reporting rule) go to that repo's `CLAUDE.md` or `AGENTS.md`,
   never to a skill. The first report ran by hand over the existing file
   and found four gaps in `ruver-code-review` (sibling-path parity,
   multi-store partial failure, tests that cannot fail, unvalidated input
   into typed columns). One cluster was already fixed by `bind-findings.py`.
2. **Collection.** `ruver-lstm` and `ruver-reviewer` append one
   observation per human comment they process, using the existing schema.
   Without this, step 1 has nothing to verify against.
3. **Reconcile, then watchdog.** Reconcile first: a job whose PR `gh`
   reports merged or closed becomes terminal. Then list stalled jobs with
   their concrete next step, and resume only when the worktree still
   exists. Report-only by default. The host scheduler runs it.
4. **Process lens of the lookback.** Once reconcile makes state
   trustworthy, cluster where runs die (node, status, lap count from the
   `ruver report` ledger) and propose graph edits the same way.

Neither loop needs Jev, so neither lives inside `bulma`, which requires
`TYPESAFE_API_KEY`. Target shape: a `ruver-lookback` graph, host-agnostic
like the others.

Rejected for now:

- Product-signal intake (error trackers, chat, issues): that is a product
  factory, not a skill marketplace.
- Policy-based auto-merge: `never_merge` is a design rule.
- A separate human-decision digest: no `waiting_user` job sat longer than
  three days, so it becomes a section of the watchdog report.
- Auto-applying `bulma` threshold suggestions: the decision ledgers hold
  2 to 8 rows each, too few to tune.
- Recurrence memory inside triage: it ran 15 times. It comes for free once
  the lookback exists.

Open: whether the watchdog may resume on its own, or only report.
