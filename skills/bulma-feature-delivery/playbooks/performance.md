# Performance

Reproduce the reported cost on a realistic workload before changing code.
Record workload, versions, configuration and a primary metric in `baseline`.
Use diagnose for a named measured cause, not a source-only guess.

Freeze the probe and regression gate. Compare production-equivalent settings,
same data and same work. Count errors and work completed. Confirm the timed
region actually performs the operation and consumes its result. Lazy, cached,
rejected or skipped work can produce an attractive meaningless number.

Alternate baseline and candidate runs at least five times per side for a decision.
Record median, range, run count and a measured limiting resource or code path in
`measurement`. Profile separately from timed runs. Measure the end-to-end path
the user waits on alongside a microbenchmark. A gap within run variation, an
untuned alternative, missing work/error counts or an unknown limiter is
inconclusive, not a speedup. A requested one-run ballpark must be labeled as such
and cannot select an implementation or satisfy a claimed improvement.

Remove unnecessary work before caching, deferring, parallelizing or cheapening it.
Keep one hypothesis per attempt; retain only gains supported by the frozen
measurement and `regression-proof`. Failed assumptions follow Bug fix's premise
check without resetting retry limits. Do not add a perf gate to unrelated tasks.
