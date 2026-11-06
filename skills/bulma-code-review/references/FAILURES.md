# 11. Failure modes

| Situation | Action |
|---|---|
| `gh` unauthenticated | stop, print `gh auth status` |
| repo or PR unresolvable | stop, never guess |
| review call fails after the one 422 retry | print the error, post nothing else, report in chat |
| codegraph unavailable | `Grep` fallback, note it in the chat summary |
| Tracker MCP unavailable | continue on the PR body, note it |
| compare endpoint 404 (force-push) | full diff, `stale_base`, stay light |
| cannot prove a suspected bug | drop it in silence, or Not verified if outside the repo; never DEFER |
| user asks for a second opinion on the **same** PR | refuse; that is a separate run, not nested subagents |
| multi-PR invocation | **required** fan-out (§0) — one subagent per PR; never sequential multi-review on main |
| child receives 2+ PRs | refuse, return ERROR; only the orchestrator fans out |
| required CI pending | **wait_ci** ([LOOP.md](../LOOP.md)), never a PR comment |
| python3 or bind/classify script missing | stop, print the error, post nothing |
| critic spawn or script fails (risk high) | keep the bound ledger, `critic=failed`; REQUEST_CHANGES if the ledger has a blocker/major, else retry once, then post nothing and report `critic=failed` |
| `gate.py` exits 1 | do not APPROVE; do not dismiss my approval. REQUEST_CHANGES for a blocker/major, DEFER for CI red/pending, else fix the payload and re-run. Never COMMENT |
| `gate.py` exits 4 | DEFER `reason=review_pending`, link the open change request or thread. The diff was reviewed |
| `gate.py` exits 5 | DEFER `reason=ci_unknown`. CI cell `not verified (tooling)`. Other text stays in the private job report |
| Actions and rollup unreadable (HTTP 403 or other read failure), `ci_overall` unverified | review the diff; REQUEST_CHANGES for a blocker/major, else DEFER `reason=ci_unknown` |
| full PR diff refused (HTTP 406, too large) | `snapshot.py --checkout` builds it from a local `git diff base...head`; no clone → collection fails, never a partial review |
| `batch-plan.py merge` exits 1 | re-run the missing batches once; still incomplete → post nothing, name the files in chat |
| `bind-findings.py` exits 3 | not a crash: a blocker/major sits outside the inline set; keep it in the body and never APPROVE |
| dismissing my own approval fails | say so in the private job report; do not post a Deferred comment for the failure |
