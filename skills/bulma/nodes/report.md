# Node: report

**Verb:** show

| Args | Command |
|---|---|
| `report [--hook H] [--since D] [--repo-only]` | `python3 scripts/bulma.py report …` |
| `status` | print `.ruver-bulma/STATE.md` frontmatter, `bulma.py power`, and the last five rows of `.ruver-bulma/DECISIONS.tsv` as `J:` lines |
| `doctor` | `python3 scripts/bulma.py doctor` |

Print the table verbatim (it is data, not chat). Add at most three
sentences in the chat language: which question has enough data, which
`suggest` you would apply, which needs `outcome` marks. Reading guide:
`../POWER.md` §Calibration loop. Stop.
