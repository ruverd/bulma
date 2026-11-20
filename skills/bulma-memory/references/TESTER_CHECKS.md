# Local feature-delivery checks

## Executable prevention

With authorization, register an existing regression test in shared project
memory. Use a single line in `## Checks` with a JSON object. All paths below
are examples.

```markdown
## Checks
- prevention: {"feedback":"lookup-error/review-comment-123.md","paths":["src/lookup/"],"argv":["npm","test","--","--run","src/lookup/lookup.test.ts"],"red":"/local/evidence/red/result.json","green":"/local/evidence/green/result.json"}
```

`feedback` is relative to the project's local `feedback/` directory and must
name a confirmed defect. `paths` accepts repository-relative files and
directory prefixes ending in `/`. Include the affected production and test
paths when edits to either can reintroduce the defect. `red` and `green`
point to intact [runtime receipts](../../bulma-bus/PERFORMANCE.md) for that same
argv on different trees. Inspect their logs for the expected failing assertion
and passing test before registration. Use a deterministic local test with the
usual tester time limit. Use the runner's existing guarantees that an absent
or skipped target cannot exit successfully. No shell, deploy, service
provisioning or credentials.

The tester runs a registered check when its paths intersect the current diff.
Unregistered lessons, missing evidence and irrelevant assessments retain
their existing advisory behavior. The command comes from trusted local
project configuration. Assessment prose never supplies executable input.
The [feedback contract](../../bulma-bus/FEEDBACK.md) defines when to promote it.

## Feature line coverage

The feature-delivery tester uses an 80% minimum for new executable feature
code. Set a project-specific integer minimum (1–100) in shared project memory
under `## Preferences`. Use the project's existing coverage runner. Configure
its argv in the same preference if the tester cannot discover a suitable
command from the project instructions or test scripts.

```markdown
## Preferences
- feature_coverage: {"minimum":85,"argv":["./scripts/test-coverage","{report}"]}
```

The command must write a fresh LCOV report to `{report}` (an absolute path
ending in `lcov.info`) or to `lcov.info` in `{report_dir}`. Use the native
reporter or a project-owned format adapter. Configure instrumentation to
include all feature files and report uncovered executable lines with zero
hits. The report must use original source paths and lines, including source
maps for transpiled code. The tester compares only added or modified lines in
the feature's production scope with the report's executable line records.
Unchanged lines in the same file, test files and other changes outside the
feature scope do not enter the calculation. The minimum is inclusive.
Unavailable reports and missing instrumentation fail the tester for executable
features. This check does not apply to ordinary fixes, chores or refactors.
