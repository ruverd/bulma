# Triage STATE

**Path:** `.bulma-triage/STATE.md`

```
init | receiving | inspecting | reproducing | classifying | acting | done | blocked
```

| Campo | Uso |
|---|---|
| `pr_url` | required |
| `classification` | PR rollup: `PR_BUG` \| `EXISTING_BUG` \| `NEW_BUG` \| `NOT_A_BUG` \| `BLOCKED` |
| `findings_count` | number of `## F<n>` classified |
| `tracker_issue_created` | comma-separated ids/urls from `NEW_BUG` tickets |
