# Node: inspect

**Verb:** observe
**Capability:** forge read only

Read the real world, not STATE's memory of it.

## Steps

1. `gh pr view` for state, draft flag and mergeability.
2. `gh pr checks` for required checks. Never `--watch`.
3. Issue comments: find the newest `bulma-qa` marker comment and the SHA it
   names.
4. Write `sha`, `ci`, `mergeable`, `qa_comment`, `video_url` under
   `## Last inspect`. Record what the commands returned.

GitLab: `glab mr view`, `glab ci status`, same fields.

## Output

One row of the [GRAPH.md](../GRAPH.md) inspect table. That row decides the
single action **step** takes.

A QA comment whose SHA is not the current head does **not** count.
