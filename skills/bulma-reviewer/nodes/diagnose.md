# Node: diagnose

**Verb:** classify  
[../references/FAILURES.md](../references/FAILURES.md).
Read CI logs with `gh run view <id> -R "$REPO" --log-failed` for a failed run.
Compare base when needed. Check MERGEABLE via gh. Do not use `gh pr checks`
or the check-runs / check-suites REST endpoints.

For runtime failures, query captured logs before repeating a reproduction.
Use [runtime evidence](../../bulma-bus/PERFORMANCE.md); missing Trail falls back
to file capture. Logs support diagnosis, but do not replace behavioral tests.
