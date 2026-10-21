# Node: plan_critic

**Verb:** critique the plan. Read-only on product code.
**Capability:** read SPEC.md, TICKETS.md, decisions. Write STATE only.
**When:** [ROUTING.md](../ROUTING.md). Skip `debug_fix`, `light_change`, and
`full_feature` + `risk=low`. Diagnose is the critic on a bug.

## Mission

Catch a bad plan before the first coder. Grill, spec, and tickets ran on
the same main thread. This node is the independent check.

## Mode

| risk | How |
|---|---|
| `low` | skip (GRAPH did not enter this node) |
| `normal` | main thread. Table, no spawn |
| `elevated` | `spawn_worker` when `risk=elevated`, read-only, this file as the contract |

Do not spawn on `normal`. Do not spawn a second critic.

## Scan

Write a table, not a verdict paragraph. One row per finding. Check:

1. Two tickets share a file or an interface: what one produces vs what the other consumes
2. A ticket's tests vs the behavior it specifies
3. A ticket that contradicts SPEC.md or a DECIDE row
4. An acceptance line with no seam
5. A ticket that cannot be verified alone (not one implement window)
6. Expert gap: a method or check the best practitioner of this domain would
   apply that the plan omits (rollback for a migration, idempotency for a
   retried job, a measured budget for "fast"). Name the method, not a persona.
   Asking the model to "act as a senior X" changes tone, not the work.
7. Proof oracle: a behavior AC whose only proof is the implementer saying so.
   Each one names its evidence: a test, a command exit code, a QA observation.

"The scan is clean" without those rows is not a scan you ran. If there
is nothing to flag, write one row: `none | n/a | clean`.

## Verdict

- **pass** — no blocking row
- **revise** — blocking rows exist

Blocking: contradiction, missing seam on a behavior AC, ticket that
cannot be the implement window it claims, behavior AC with no proof oracle,
expert gap inside an existing AC's scope.

An expert gap outside every AC is not blocking and never becomes a new AC.
Log it in STATE decisions as a follow-up.

## Apply

The worker never edits SPEC.md or TICKETS.md. Main thread DECIDE and
applies, then this node once more. `plan_critic_loops: 1`.
Still blocking: DECIDE residuals, log, continue. Escalate only if a
residual leaves every path a guess (last-resort policy).

## Output

```text
plan_critic_verdict: pending | skip | pass | revise
plan_critic_mode: main | spawn | skip
findings: N
summary: ...
```

`status: critiquing` while this node runs. `status: implementing` after
pass, or after residuals are logged.

## Hard rules

- Zero product code.
- Do not reopen grill as an interview.
- Do not invent AC.
- Do not skip because the spec looks long.

Resolve spec and tickets through STATE paths. Compact mode points both at the
same canonical contract; read it once and critique its decisions without expanding
it into a second plan. Risk still controls whether this node runs.
