# 11. Failure modes

| Situation | Action |
|---|---|
| `gh` unauthenticated | stop, print `gh auth status` |
| repo or PR unresolvable | stop, never guess |
| review call fails after the one 422 retry | print the error, post nothing else, report in chat |
| codegraph unavailable | `Grep` fallback, note it in the chat summary |
| Tracker MCP unavailable | continue on the PR body, note it |
| compare endpoint 404 (force-push) | full diff, `stale_base`, stay light |
| cannot prove a suspected bug | drop it in silence, or `uncertainties` if outside the repo |
| user asks for a second opinion on the **same** PR | refuse; that is a separate run, not nested subagents |
| multi-PR invocation | **required** fan-out (§0) — one subagent per PR; never sequential multi-review on main |
| child receives 2+ PRs | refuse, return ERROR; only the orchestrator fans out |
| required CI pending | **wait_ci** ([LOOP.md](../LOOP.md)), never a PR comment |
| python3 or bind/classify script missing | stop, print the error, post nothing |
| critic spawn or script fails (risk high) | keep the bound ledger, `critic=failed`; REQUEST_CHANGES if the ledger has a blocker/major, else DEFER `reason=critic_failed` |
| `gate.py` exits 1 | DEFER with its reasons; never retry the APPROVE until the reasons are gone |
| `gate.py` exits 3 | post the same body as a `COMMENT` review, `reason=bot_quorum` |
| `bind-findings.py` exits 3 | not a crash: a blocker/major sits outside the inline set; keep it in the body and never APPROVE |
| dismissing my own approval fails | say so in the artifact body and chat; the stale approval is a known risk at merge |
