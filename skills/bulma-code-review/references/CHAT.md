# 10. Chat summary

Lead with two to four sentences in English. Unslop. Say the
verdict and the one thing that drove it. Then the table. Do not paste the
GitHub body into chat.

```
# Review: <repo>#<pr>, <pass> pass

| | |
|---|---|
| Head | <sha7> |
| Prior | none | deep@<sha7> APPROVED | ... |
| CI | success \| failure \| pending \| unknown |
| Axes | tests, correctness, security, standards (skipped a11y no UI, deps no lockfile) |
| Risk | high or low |
| Critic | skip, ran, or skip with critic_failed |
| Read | 12 files, 5 codegraph queries |
| Findings | N blockers · N majors · N nits · N dropped by self-verify · N dropped by bind |
| Carried | N re-verified — N still reproduce, N resolved |
| Coverage | 12/12 |
| Posted | APPROVED \| CHANGES_REQUESTED \| DEFERRED — reason \| WAITING — loop <id> \| SKIPPED — reason \| DRY-RUN |
```
