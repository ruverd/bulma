# Ruver disk (global)

**Never** create `.ruver-*` at a git root, worktree, or anywhere inside a
repo. That includes `.ruver-bus/`, `.ruver-developer/`, `.ruver-qa/`,
`.ruver-triage/`, `.ruver-reviewer/`, `.ruver-lstm/`,
`.ruver-bulma/`, `.ruver-code-review/`, `.ruver-feature-delivery/`, `.ruver-goal/`,
and `.ruver/`.

## Home

Harness-neutral. Claude Code, Codex, Grok, and Cursor share it.

```bash
slug=$(git rev-parse --show-toplevel | sed 's|^/||; s|/|-|g')
RUVER_HOME="${RUVER_HOME:-$HOME/.ruver}"
# One-time: if ~/.ruver is missing and ~/.grok/ruver exists, use that
# tree (install.sh symlinks ~/.ruver -> ~/.grok/ruver).
if [ ! -e "$RUVER_HOME" ] && [ -d "$HOME/.grok/ruver" ]; then
  RUVER_HOME="$HOME/.grok/ruver"
fi
RUVER_ROOT="$RUVER_HOME/$slug"
mkdir -p "$RUVER_ROOT"
```

Example: repo `/Users/you/src/app` → `$HOME/.ruver/Users-you-src-app/`.

All `.ruver-*` paths in ruver skills are **under `$RUVER_ROOT`**:

```
$RUVER_HOME/
  memory.md                 # you (every repo). ruver-memory
  <slug>/                   # = $RUVER_ROOT
    memory.md               # this git toplevel. ruver-memory
    .ruver-bus/
    .ruver-developer/
    .ruver-qa/
    .ruver-triage/
    .ruver-reviewer/
    .ruver-lstm/
    .ruver-code-review/
    .ruver-feature-delivery/
    .ruver-goal/
    .ruver-bulma/
```

`.ruver-bus/ENVELOPE.md` means `$RUVER_ROOT/.ruver-bus/ENVELOPE.md`.

Every graph appends one row per transition to
`.ruver-bus/RUN_LOG.tsv` — [LEDGER.md](LEDGER.md). Two lines per node,
and `ruver report` turns them into wall time and lap counts. When the
installer can read a host transcript, it also prints token totals.
It never gates anything.
`memory.md` is not a `.ruver-*` dir. Still never inside a repo.
Format and load: skill `ruver-memory`.

One slug per git toplevel (each worktree has its own). Do **not**
`git add` these dirs.

If a leftover `.ruver-*` exists inside the repo, move it into
`$RUVER_ROOT` and delete the copy in the repo. Do not keep writing there.
