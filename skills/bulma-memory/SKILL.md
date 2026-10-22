---
name: bulma-memory
category: lib
description: >
  Use when /memory, /bulma-memory, a bulma graph or engine starts,
  the first run in a repo, CODEOWNERS or AGENTS.md list no reviewers,
  or the user states a durable preference (chat language, reviewers,
  project notes, open questions).
argument-hint: "[--project] [<note>]"
---

# Bulma memory

Durable prefs **outside git**. Not STATE. Not AGENTS.md.

Paths: [DISK.md](../bulma-bus/DISK.md).

```
$BULMA_HOME/memory.md    # you (every repo)
$BULMA_REPO/memory.md    # this repository, shared by all its worktrees
$BULMA_ROOT/memory.md    # this worktree only, when it differs from $BULMA_REPO
```

`$BULMA_REPO` is the `$BULMA_ROOT` of the repository's main worktree, so a
task worktree (Orca, Codex, Grok, `git worktree add`) reads the same project
memory as the main clone:

```bash
main=$(git worktree list --porcelain | sed -n '1s/^worktree //p')
BULMA_REPO="$BULMA_HOME/$(printf '%s' "$main" | sed 's|^/||; s|/|-|g')"
```

In the main clone `$BULMA_REPO` and `$BULMA_ROOT` are the same directory.
"Project file" below means `$BULMA_REPO/memory.md`.

No git root? Only the home file. Create a file **when writing**, not
on install. Missing file = empty.

## Load

Before the first user-facing sentence of any bulma graph, engine, or
`/memory`:

1. Resolve `$BULMA_HOME`, `$BULMA_ROOT` (DISK.md) and `$BULMA_REPO` (above).
2. Read the home file, then the project file, then the worktree file when it
   is a different path. Later files win on the same key; sections merge.
3. Chat language = home `## Chat` `language:`. Default `en`.
4. If project `## Open` has an item and this turn is not
   `wait_ci` / `execute` / a last-resort ticket ASK: ask **one**
   Open item at the end of the turn. Do not stop the graph for it.

Workers that do not chat skip this. Ship still resolves reviewers
via [PRODUCT.md](../bulma-feature-delivery/PRODUCT.md) §6.

## Worktree location

The Git fallback worktree directory is a memory preference. Read
`worktree_root` from `## Preferences` using the normal memory precedence.
If absent, use `$BULMA_HOME/workspaces`, where `BULMA_HOME` defaults to
`$HOME/.bulma`. Installation creates this default directory without creating
or rewriting memory files.

For a custom location, write to home memory, or project memory for a repo-only
override:

```markdown
## Preferences
- worktree_root: /absolute/path/to/workspaces
```

Resolve the value to an absolute path and pass it as `WORKTREE_ROOT` to
[JOBS.md](../bulma-bus/JOBS.md#worktree). A leading `~`, `$HOME` or
`$BULMA_HOME` denotes that directory; expand it as path text, never with
`eval` or command substitution from the memory value. Create the resolved
root before Git fallback creation. A custom location does not move existing
checkouts or change paths chosen by host isolation or Orca.

## Chat vs forge

| Surface | Language |
|---|---|
| Chat with the user | home `## Chat` (default English) |
| GitHub / GitLab (PR body, review, thread, issue comment, dismiss) | **English** |
| Spec, tickets, commits, CI, skill bodies | **English** |

Unslop always. A PT-BR chat pref does not translate forge text.

## Files

Same headings. Write `## Chat` only in the **home** file. Write
`## Product` and `## Open` only in the **project** file.

```markdown
# Memory

## Chat
language: pt-BR

## Preferences
- short durable notes

## Product
reviewers: alice, bob

## Gotchas
- src/billing/**: amounts are minor units; divide once, at display
- duration: stored in seconds everywhere

## Checks
- python3 tools/prcheck.py --base origin/main

## Open
- Confirm reviewers: alice, bob (merged PRs)
```

`language:` is `en` or `pt-BR` (or another BCP-47 tag). Reviewers are
forge logins, comma-separated, never invented. `## Product` is the
**confirmed** reviewer list. How it gets filled: PRODUCT.md §6.

`second_opinion:` under `## Preferences` turns on a second critic on another
model for elevated-risk plans: `codex`, `gemini`, or `claude`. Leave it out
for `off`. It names a CLI installed on this machine, so it is usually a user
preference, not a project one. How it runs: `bulma-host` §Second opinion.

`## Gotchas` and `## Checks` live only in the **project** file.

- `## Gotchas`: one line per domain fact the code does not make obvious
  (units, id conventions, provider quirks, fields that look alike). Start
  each line with a path glob or a keyword, then `:` and the fact. The coder
  gets the lines whose glob or keyword matches its files; the reviewer gets
  the lines that match the diff. A gotcha is a lead, never a finding by
  itself. Add one when a review or an incident shows a fact that the next
  change will trip on again.
- `## Checks`: one command per line that this project runs before a push
  (a guardrail scanner, a schema validator). The fd tester runs them from the
  repo root after its own commands. Never put a deploy or a destructive
  command here.

Do not duplicate a fact that already lives in the target repo
(`AGENTS.md`, `CODEOWNERS`, `REVIEW.md`).

## `/memory`

```text
/memory
/memory me responder e interagir comigo apenas em PT-BR
/memory --project reviewers: alice, bob
```

| Args | Write |
|---|---|
| empty | Print both files. Ask the first `## Open` item if any |
| `--project` / clearly this-repo (reviewers, assignee, repo notes, gotchas, checks) | project file |
| else | home file |

Parse the note. Language / idioma / PT-BR / Portuguese → home
`## Chat`. `reviewers:` logins → project `## Product` (that **is**
confirmation). `gotcha:` → project `## Gotchas`. `check:` → project
`## Checks`. Other text → `## Preferences` on the chosen file.

Append or replace the matching key. Do not rewrite unrelated
sections. Do not commit these files.

## Open

Graphs may append one line under project `## Open` when a fact is
useful later and lookup failed. One question per turn. After the
answer: write the fact, delete that Open line, continue.

Open is not grill. Ticket ASK stays [DECISION_POLICY.md](../bulma-feature-delivery/DECISION_POLICY.md).

## Never

- Write memory inside a repo
- Hardcode a company's handles in a graph
- Copy a project's gotchas or checks into a skill file
- Block CI, ship, or execute to drain Open
- Interview a first-run questionnaire
- Let chat language leak onto the forge
