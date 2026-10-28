# Node: report

**Verb:** show

| Args | Command |
|---|---|
| `report [--hook H] [--model M] [--policy-id P] [--source S] [--since D] [--repo-only]` | `python3 scripts/bulma.py report …` |
| `status` | print `.bulma-core/STATE.md` frontmatter, `bulma.py power`, and the last five rows of `.bulma-core/DECISIONS.tsv` as `J:` lines |
| `doctor` | `python3 scripts/bulma.py doctor` |

Print the table verbatim (it is data, not chat). Add at most three
sentences in the chat language: which question has enough data, which
`suggest` you would apply, which needs `outcome` marks. Reading guide:
`../POWER.md` §Calibration loop. Stop.
