# Bulma disk (global)

**Never** create `.bulma-*` at a git root, worktree, or anywhere inside a
repo. That includes `.bulma-bus/`, `.bulma-developer/`, `.bulma-qa/`,
`.bulma-triage/`, `.bulma-reviewer/`, `.bulma-lstm/`,
`.bulma-core/`, `.bulma-code-review/`, `.bulma-feature-delivery/`, `.bulma-goal/`,
and `.bulma/`.

## Home

Harness-neutral. Claude Code, Codex, Grok, and Cursor share it.

```bash
slug=$(git rev-parse --show-toplevel | sed 's|^/||; s|/|-|g')
BULMA_HOME="${BULMA_HOME:-$HOME/.bulma}"
BULMA_ROOT="$BULMA_HOME/$slug"
mkdir -p "$BULMA_ROOT"
```

Example: repo `/Users/you/src/app` → `$HOME/.bulma/Users-you-src-app/`.

All `.bulma-*` paths in bulma skills are **under `$BULMA_ROOT`**:

```
$BULMA_HOME/
  memory.md                 # you (every repo). bulma-memory
  insights/
    observations.jsonl      # human-review observations. INSIGHTS.md
  <slug>/                   # = $BULMA_ROOT
    memory.md               # this git toplevel. bulma-memory
    .bulma-bus/
    .bulma-developer/
    .bulma-qa/
    .bulma-triage/
    .bulma-reviewer/
    .bulma-lstm/
    .bulma-code-review/
    .bulma-feature-delivery/
    .bulma-goal/
    .bulma-core/
```

`.bulma-bus/ENVELOPE.md` means `$BULMA_ROOT/.bulma-bus/ENVELOPE.md`.

Every graph appends one row per transition to
`.bulma-bus/RUN_LOG.tsv` — [LEDGER.md](LEDGER.md). Two lines per node,
and `bulma report` turns them into wall time and lap counts. When the
installer can read a host transcript, it also prints token totals.
It never gates anything.
`memory.md` is not a `.bulma-*` dir. Still never inside a repo.
Format and load: skill `bulma-memory`.

One slug per git toplevel (each worktree has its own). Do **not**
`git add` these dirs.

If a leftover `.bulma-*` exists inside the repo, move it into
`$BULMA_ROOT` and delete the copy in the repo. Do not keep writing there.
