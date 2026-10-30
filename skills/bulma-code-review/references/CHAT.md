# 10. Chat summary

Lead with two to four sentences in English. Unslop. Say the
verdict and the one thing that drove it. Then the table. Do not paste the
GitHub body into chat.

```
# Review: <repo>#<pr>, <pass> pass

| | |
|---|---|
| Model | <reviewer_model> |
| Reasoning effort | <reviewer_effort> |
| Head | <sha7> |
| Prior | none | deep@<sha7> APPROVED | ... |
| CI | success \| failure \| pending \| unknown |
| Axes | tests, correctness, security, standards (skipped a11y no UI, deps no lockfile) |
| Risk | high or low |
| Critic | skip (low risk), ran, or failed |
| Gate | pass, blocked — reasons, or bot_quorum |
| Read | 12 files, 5 codegraph queries |
| Findings | N blockers · N majors · N nits · N dropped by self-verify · N dropped by bind |
| Carried | N re-verified — N still reproduce, N resolved |
| Coverage | 12/12 |
| Posted | APPROVED \| CHANGES_REQUESTED \| COMMENTED — bot_quorum \| DEFERRED — reason \| WAITING — loop <id> \| SKIPPED — reason \| DRY-RUN |
```
