---
name: bulma-goal
category: graph
description: >
  Drive developer → CI green → QA comment+evidence across turns with
  schedule_wake. Use when /goal or /bulma-goal, or after a draft PR is
  opened and CI is still pending.
argument-hint: "<ticket | PR url | status | cancel>"
---

# Bulma goal / loop

The graphs do **not** finish in one turn. CI takes 20–30 min. This
skill keeps the session working until QA has **commented with evidence**.

**REQUIRED:** [COMPLETE.md](references/COMPLETE.md) ·
[LOOP.md](references/LOOP.md) · bus PROTOCOL.md ·
[DISK.md](../bulma-bus/DISK.md) (`.bulma-*` is **global**, never git root) ·
`bulma-memory`

Chat: `bulma-memory`. Unslop always.
Worktree and branch rules: [JOBS.md](../bulma-bus/JOBS.md) §Worktree.

## Commands

| Args | Action |
|---|---|
| ticket id / feature text | Start goal + developer graph |
| PR url / `owner/repo#N` | Start goal on that PR (skip implement if it exists) |
| `status` | Read `.bulma-goal/STATE.md` + `gh pr checks` + last QA comment |
| `cancel` | Delete the scheduler loop; leave graphs as-is |

## Start

1. Load `bulma-memory`. Write `.bulma-goal/STATE.md` from
   [templates/STATE.md](templates/STATE.md).
2. Name the completion bar (verifier / user):

```text
Draft PR for <id> is CI-green, MERGEABLE, and has a bulma-qa
comment on the head SHA that includes evidence.
```

If the host has a `/goal` (or equivalent) command, register that
sentence there. If it does not, STATE is enough.

3. If there is no PR yet → load **bulma-developer** GRAPH (`deliver`).
4. When a draft PR exists and CI is not green → **schedule_wake**
   ([LOOP.md](references/LOOP.md)). Do not `gh pr checks --watch`.
5. Stop the turn. The wake resumes this skill.

## Each wake (or `/bulma-goal` resume)

Read STATE. Inspect the real PR (`gh pr view`, `gh pr checks`,
issue comments). Then **one** step:

| World | Next |
|---|---|
| No PR | developer `deliver` |
| CI pending / in progress | stop (wait for next fire) |
| CI red | developer `fix` / fd ci loop |
| Green but not MERGEABLE | developer `mergeable` |
| Green + MERGEABLE, no QA comment on **this** SHA | enqueue-or-start QA (JOBS.md) |
| QA comment on this SHA, verdict FAIL + PR_BUG | developer `fix` |
| QA comment on this SHA, PASS / FAIL-unrelated / BLOCKED documented | **complete** |

Complete = [COMPLETE.md](references/COMPLETE.md) all true, then
`cancel_wake`.

## Never

- Claim the goal done without the QA comment + evidence on **head** SHA
- Sit in `--watch` (CI is longer than a tool timeout)
- Spawn graph-agents as children (bus switch / load GRAPH)
- Start a second QA while `qa_active` holds another **live** PR
- Merge

## After QA comment

Cancel the loop. Report in the chat language: PR, SHA, QA verdict, comment URL, evidence URL.
