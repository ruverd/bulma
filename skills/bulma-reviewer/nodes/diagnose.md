# Node: diagnose

**Verb:** classify  
[../references/FAILURES.md](../references/FAILURES.md).
Read CI logs. Compare base when needed. Check MERGEABLE via gh.

For runtime failures, query captured logs before repeating a reproduction.
Use [runtime evidence](../../bulma-bus/PERFORMANCE.md); missing Trail falls back
to file capture. Logs support diagnosis, but do not replace behavioral tests.
