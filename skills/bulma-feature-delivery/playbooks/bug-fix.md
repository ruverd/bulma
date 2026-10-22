# Bug fix

Follow `debug_fix`. Capture the discriminating symptom before editing, identify
the mechanism with runtime evidence, then hand one bounded fix to implement.
Record those facts in `reproduction` and `mechanism`. Preserve the original repro.

The tester repeats the same observable path on the fixed artifact and records
`same-surface-proof`. A successful compile cannot substitute for that path.
Use the repository's practical regression check and retain required TDD evidence.
If the original target cannot be exercised, report that limitation, not a pass.

After two failed fixes sharing a premise, write the premise and run an observation
that would differ if it were false before another fix. Add the result to the
existing Debug section. Keep the existing retry cap; this rule does not reset it.
Revert unsupported changes rather than accumulating retries or symptom guards.
