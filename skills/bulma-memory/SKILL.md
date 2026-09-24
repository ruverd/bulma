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
$BULMA_ROOT/memory.md    # this git toplevel
```

No git root? Only the home file. Create a file **when writing**, not
on install. Missing file = empty.

## Load

Before the first user-facing sentence of any bulma graph, engine, or
`/memory`:

1. Resolve `$BULMA_HOME` / `$BULMA_ROOT` (DISK.md).
2. Read both files if they exist.
3. Chat language = home `## Chat` `language:`. Default `en`.
4. If project `## Open` has an item and this turn is not
   `wait_ci` / `execute` / a last-resort ticket ASK: ask **one**
   Open item at the end of the turn. Do not stop the graph for it.

Workers that do not chat skip this. Ship still resolves reviewers
via [PRODUCT.md](../bulma-feature-delivery/PRODUCT.md) §6.

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

## Open
- Confirm reviewers: alice, bob (merged PRs)
```

`language:` is `en` or `pt-BR` (or another BCP-47 tag). Reviewers are
forge logins, comma-separated, never invented. `## Product` is the
**confirmed** reviewer list. How it gets filled: PRODUCT.md §6.

Do not duplicate a fact that already lives in the target repo
(`AGENTS.md`, `CODEOWNERS`).

## `/memory`

```text
/memory
/memory me responder e interagir comigo apenas em PT-BR
/memory --project reviewers: alice, bob
```

| Args | Write |
|---|---|
| empty | Print both files. Ask the first `## Open` item if any |
| `--project` / clearly this-repo (reviewers, assignee, repo notes) | project file |
| else | home file |

Parse the note. Language / idioma / PT-BR / Portuguese → home
`## Chat`. `reviewers:` logins → project `## Product` (that **is**
confirmation). Other text → `## Preferences` on the chosen file.

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
- Block CI, ship, or execute to drain Open
- Interview a first-run questionnaire
- Let chat language leak onto the forge
