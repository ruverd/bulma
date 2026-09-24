# 7. High-risk critic

Always reach this node after Phase 10 bind, before
[verdict.md](verdict.md). It is not a second GitHub artifact.

If STATE `risk` is `low`, set `critic=skip` and continue. Do not spawn.

If `risk` is `high`, spawn **one** `spawn_worker`
([bulma-host](../../bulma-host/SKILL.md)). That spawn is the single-PR
subagent this skill allows. The worker does not post, merge, fan out, or
spawn a nested reviewer.

## Spawn payload

Pass, and nothing else:

- this node file
- PR url + head SHA
- `$BULMA_ROOT/.bulma-code-review/AC.md`
- bound findings JSON (blockers and majors only; nits stay on the parent)
- `$BULMA_ROOT/.bulma-code-review/PATCH.diff`
- whitelist: at most 4 high-risk paths from `FILES.txt`, plus 20–40 line
  excerpts of cited hunks
- “do not spawn, do not post, do not merge”

Do not pass GRAPH.md, the parent review notes, or the session history.

If spawn is impossible, run this node on the current thread from those
files only. Do not re-read the rest of the first pass.

## Job

You did not write the first review. Treat the ledger as untrusted.

Walk **three lenses in this order**. Do not vote. A finding that only one
lens can prove still stands. `lenses` on a finding is metadata, never a
reason to drop.

1. **Contracts.** Signature, return shape, AC.md `missing`/`partial`,
   public export with no migration, mass assignment onto role/tenant/price.
2. **Integration / state / repro.** Shared path side effects, state not
   reset between runs, races, callers outside the diff that do not handle
   the new shape, a test that asserts a mock.
3. **Security / data loss.** Permission on the write, user input in
   SQL/HTML/shell/href, SSRF, path concat, CSRF on cookie-auth writes,
   PII in logs.

For each bound blocker or major: keep it only if a lens's hunk proves the
trigger. Drop it if the refutation holds or the line is not the bug.

Then look for at most **2** missed **blockers** across the whitelist.
Contract break, data loss, or missing permission only. No nits. No new
majors.

Every kept or added finding still needs `axis`, `path`, `line`, `trigger`,
`impact`, `fix`. Return JSON: `{kept, dropped_by_critic, added}`.

Caps: 4 extra Reads, 3 codegraph queries, 2 added blockers.

## After the worker

Pipe `kept` + `added` through `scripts/bind-findings.py` with the same
patch and allow-paths. Unbound drops. Nits from the first pass stay
bound as they were. STATE `critic=ran`.

Spawn or script failure: keep the first-pass bound ledger, set
`critic=skip`, note `critic_failed` in chat, still publish.
