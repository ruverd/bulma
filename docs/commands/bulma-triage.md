# `/bulma-triage`

Graph engineer for **bug classification**. Investigate first. Decide
second. Act third. Not a ticket bot.

Skill: [`../../skills/bulma-triage`](../../skills/bulma-triage).

## When

- Envelope: `TRIAGE_REQUEST` from [QA](bulma-qa.md)
- `/bulma-triage <PR url>` (standalone, still needs a PR)

## Graph

```
TRIAGE_REQUEST or args
  → receive          PR link required
  → inspect          diff + tracker + each finding
  → reproduce
  → classify         one class per finding
  → act
       ├ NEW_BUG     → tracker ticket
       ├ PR_BUG      → no ticket, no jump to developer
       └ others      → no new ticket
       └ always: TRIAGE_RESULT → pop (back to QA)
```

## Classes

| Class | Meaning | Next |
|---|---|---|
| `PR_BUG` | This PR introduced it | QA verdict FAIL → developer **fix** |
| `EXISTING_BUG` | Was already there | Note. Do not block this PR |
| `NEW_BUG` | Real, not this PR | Tracker ticket |
| `NOT_A_BUG` | Intended / invalid | Note |
| `BLOCKED` | Cannot prove (env/auth) | Note |

`PR_BUG` does **not** switch to developer from here. Order:

1. Write `TRIAGE_RESULT`.
2. Pop back to QA.
3. QA writes `QA_RESULT` FAIL and pops to developer.
4. Developer `apply_qa` sees FAIL+PR_BUG → **fix**.

## Never

- Spawn `bulma_developer`.
- Skip QA verdict on a PR_BUG.
- Invent a tracker ticket for PR_BUG.
- Classify without trying to reproduce.

## Related

[`/bulma-qa`](bulma-qa.md) · [`/bulma-developer`](bulma-developer.md)
