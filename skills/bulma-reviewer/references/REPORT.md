# Review report

Exactly one status, then the blocks.

Statuses: `PASS` · `PR FAILURE` · `TEST FAILURE` · `INFRASTRUCTURE FAILURE`
· `ENVIRONMENT FAILURE` · `BRANCH FAILURE` · `UNRELATED FAILURE`
· `HUMAN INTERVENTION REQUIRED`

```text
Review: <status>
PR: <url>
SHA: <sha>
CI: green | red | pending | unknown
Mergeable: MERGEABLE | CONFLICTING | DIRTY | BLOCKED | UNKNOWN
bulma-code-review: APPROVED | CHANGES_REQUESTED | DEFERRED | SKIPPED

### Summary
<what was reviewed + result>

### Findings
<important code / test / CI / branch issues>

### Root Cause
<actual reason per failure>

### Evidence
<PR, check, test, commit, file, tracker id>

### Action
<fixed / retry / tracker / human>
```

Do not report only symptoms.

Chat example:

> CI failed on E2E because service X is not in the environment. The PR
> code is not on that path, and the same test fails on the base branch.
> Classification: INFRASTRUCTURE FAILURE.
