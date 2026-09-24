# Node: evidence

**Verb:** capture
**Capability:** write local PNGs and a PR-body fragment. No product fix. No PR.
**Does not** open the PR. Shipper attaches the PNGs.

## Mission

After every ticket has passed tester, before blast (`full_feature` /
`debug_fix` / `light_change`+`risk=elevated`) or before quality
(`light_change` and `risk` is not `elevated`). Capture After. Write a
fragment the shipper pastes into [../templates/PR_BODY.md](../templates/PR_BODY.md).

## When

Tester pass, no tickets left. Then this node. Then blast, or quality
when ROUTING.md skips blast. GRAPH.md owns the edges.

## Before capture

This node owns the rule. Neighbors get one sentence, not a copy.

- After the worktree exists, before the first RED, when a UI route
  already exists. [JOBS.md](../../bulma-bus/JOBS.md) §Worktree points here.
- `debug_fix`: capture during diagnose, while the bug still shows.
  [diagnose.md](diagnose.md) points here.
- New screen, no route yet: `Before: n/a (new screen)`.

Record route and viewport in STATE. After must reuse both.

## After capture

Same route and viewport as Before. New screen: After only.

If the PR SHA later changes, recapture After and refresh the open PR
body (`gh pr edit --body`). Developer `fix` and LSTM `patch` point here.

## How

**UI.** `qa_tool=agent-browser`: PNG of the route via
[before-and-after](../../before-and-after/SKILL.md). Same viewport as
Before. Restore the shared session first.

**Non-UI.** A fenced command-output pair. No invented screen.

Save PNGs under `$BULMA_ROOT/.bulma-feature-delivery/evidence/`
(`before.png` / `after.png`, or `n/a`).

## Ticket After (`risk=elevated` UI)

After a UI ticket passes tester and more tickets remain. One PNG of
**this** ticket's route, same viewport as Before.
`$BULMA_ROOT/.bulma-feature-delivery/evidence/after-ticket-<N>.png`.

Parent calls this from [IMPLEMENTATION.md](../IMPLEMENTATION.md). Do not
rewrite the PR fragment here. The final After (`after.png`) still runs
when no tickets are left.

Skip when `qa_tool` is not `agent-browser`, or `risk` is not `elevated`.
Missing file on a UI elevated ticket is a fail. Do not start the next
ticket.

## Publish

Keep the PNGs on disk. There is no PR yet. Shipper attaches them with
[before-and-after](../../before-and-after/SKILL.md) (`format.sh` +
`gh pr edit --attach`). Do not gist.

## Fragment

Write `$BULMA_ROOT/.bulma-feature-delivery/pr-body-evidence.md`.

Fill **How tested** (commands + exit codes from `gates.log`) and
**Before → After** (local PNG paths, fenced output, or `n/a`).
Shipper inlines the fragment into
[../templates/PR_BODY.md](../templates/PR_BODY.md), then replaces
local PNG paths with GitHub attachments.

## Output

```text
result: ok | skipped
before: <png path | n/a (new screen) | n/a>
after: <png path | fenced | n/a>
route: <path or n/a>
viewport: <WxH or n/a>
fragment: .bulma-feature-delivery/pr-body-evidence.md
summary: ...
```

`skipped` only when there is no UI route and no command worth fencing
(docs-only). Still write the fragment with `n/a`.

## Hard rules

- Do not invent a pass. Missing After on a UI change is a fail.
- Do not open, merge, or push the PR.
- Do not change product code.
- Do not retype `gates.log` exit codes from memory.
