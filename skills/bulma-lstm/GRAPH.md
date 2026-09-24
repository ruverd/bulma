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
  → reply            # 👍 + unslopped reply on every comment, resolve, dismiss CHANGES_REQUESTED, re-request
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
| verify | only skip / nits / nothing new | **reply** |
| verify | unclear + last-resort ASK | **stop** (`waiting_user`) |
| patch | complicated and grill not done | **grill** |
| grill | frontier empty | **patch** (coder) |
| grill | ASK last resort | **stop** (`waiting_user`) |
| patch | coder DONE / pushed | **prove** |
| patch | coder NEEDS_CONTEXT | DECIDE or ASK last resort |
| prove | spec_verdict=pass and quality_verdict=pass and tester pass | **reply** |
| prove | either fail + loops left | **patch** |
| prove | either fail + loops exhausted | **escalate** |
| reply | always | **report** |
| report | stacked | `LSTM_RESULT` + pop |
| report | invoked alone | chat report only |

## Nodes

`nodes/admit.md` · `nodes/resume.md` · `nodes/resolve.md` ·
`nodes/conflict.md` · `nodes/verify.md` · `nodes/grill.md` ·
`nodes/patch.md` · `nodes/prove.md` · `nodes/reply.md` ·
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
