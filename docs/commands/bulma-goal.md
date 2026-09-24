# `/bulma-goal`

Keeps delivery alive **across turns**. CI is often longer than a tool
timeout. This graph `schedule_wake`s until QA has commented **with
evidence** on the head SHA.

Skill: [`../../skills/bulma-goal`](../../skills/bulma-goal).

## When

- `/bulma-goal ABC-123`
- `/bulma-goal https://github.com/org/repo/pull/99`
- `/bulma-goal status`
- `/bulma-goal cancel`
- After a draft PR exists and CI is still pending

## Completion bar

All must hold on the **current** head SHA:

1. Draft PR exists
2. Required CI green
3. MERGEABLE
4. QA comment with `bulma-qa` marker for that SHA
5. That comment has evidence (Video URL when recorded; HTTP still
   or FE screens of callers on API-only)

See [COMPLETE.md](../../skills/bulma-goal/references/COMPLETE.md).

## Each wake

One step, then stop:

| World | Next |
|---|---|
| No PR | [developer](bulma-developer.md) `deliver` |
| CI pending | wait |
| CI red | developer `fix` |
| Green, not MERGEABLE | developer `mergeable` |
| Green + MERGEABLE, no QA on this SHA | enqueue-or-start [QA](bulma-qa.md) |
| QA FAIL + PR_BUG | developer `fix` |
| QA comment on this SHA (PASS / other) | **complete**, `cancel_wake` |

Wake primitive: [bulma-host](../../skills/bulma-host/SKILL.md) `schedule_wake`
(Grok `/loop`, otherwise ask the user to re-run).

## Never

- Claim done without the QA comment + evidence on **head** SHA
- `gh pr checks --watch`
- Spawn graph agents as children
- A second QA while `qa_active` is another PR
- Merge

## Related

[`/bulma-developer`](bulma-developer.md) · [`/bulma-qa`](bulma-qa.md)
