# LSTM graph

Looks shit to me. Author handles review + conflict.

```
start (ARGS.md: URL | resume | LSTM_REQUEST)
  → admit
  → resolve          # PR + review ids + comment ids
  → conflict         # DIRTY / CONFLICTING → rebase always
  → verify           # claim_true + fix_ok_here → fix | skip | unclear
  → grill?           # complicated should-fix only
  → patch            # bulma-fd-coder + TDD, same branch
  → prove            # spec_verdict + quality_verdict + tester
  → request_qa?      # human sign-off requested, including evidence-only runs
  → reply            # 👍 + unslopped reply on every comment, resolve fixed threads, dismiss proved change requests; re-request non-approved reviewers after changes
  → report
```

## Edges

| From | Condition | To |
|---|---|---|
| start | `resume` / live STATE | **resume** at saved node |
| start | URL(s) or `LSTM_REQUEST` | **admit** |
| start | empty, no STATE | **stop** (ask for a PR or comment URL) |
| admit | idle + one PR | **resolve** |
| admit | busy or 2+ PRs | one worker+worktree per PR; **stop** on main |
| resolve | unresolvable | **stop** |
| resolve | `DIRTY` / `CONFLICTING` | **conflict** |
| resolve | else | **verify** |
| conflict | rebased / still dirty after try | **verify** |
| verify | ≥1 should-fix | **patch** (grill first if complicated) |
| verify | no fixes, human sign-off requested | **request_qa** |
| verify | only skip / nits / nothing new, no sign-off request | **reply** |
| verify | unclear + last-resort ASK | **stop** (`waiting_user`) |
| patch | complicated and grill not done | **grill** |
| grill | implementation decisions resolved | **patch** (coder) |
| grill | ASK last resort | **stop** (`waiting_user`) |
| patch | coder DONE, more groups | **patch** (next group, sequential) |
| patch | all groups DONE / pushed | **prove** (final combined tree) |
| patch | coder NEEDS_CONTEXT | DECIDE or ASK last resort |
| prove | all proof passes, human sign-off requested | **request_qa** |
| prove | all proof passes, no sign-off request | **reply** |
| request_qa | admitted or queued | bus switch to **qa**; wait for matching `QA_RESULT` |
| request_qa | fresh complete visual QA PASS | **reply**, human approval still pending |
| request_qa | FAIL with triaged PR_BUG and loops left | **verify** then **patch**, **prove**, QA again |
| request_qa | BLOCKED / PENDING_TRIAGE / incomplete evidence / provider external / stack refused | report blocker, keep sign-off pending; **escalate** when no independent work remains |
| prove | either fail + loops left | **patch** |
| prove | either fail + loops exhausted | **escalate** |
| reply | always | **report** |
| report | stacked | `LSTM_RESULT` + pop |
| report | invoked alone | chat report only |

## Nodes

`nodes/admit.md` · `nodes/resume.md` · `nodes/resolve.md` ·
`nodes/conflict.md` · `nodes/verify.md` · `nodes/grill.md` ·
`nodes/patch.md` · `nodes/prove.md` · `nodes/request_qa.md` · `nodes/reply.md` ·
`nodes/report.md`

Concurrency: `../bulma-bus/JOBS.md`.

GitHub API: [references/GITHUB.md](references/GITHUB.md)
Failures: [references/FAILURES.md](references/FAILURES.md)

## Defaults

```yaml
never_merge: true
stay_draft: if_already_draft
new_pr: false
same_branch: true
always_rebase_conflicts: true
tdd: required_for_behavior_change
prove_fix_loops: 2
chat_language: en
voice: unslop
decide_by_default: true
ask_last_resort_only: true
```
