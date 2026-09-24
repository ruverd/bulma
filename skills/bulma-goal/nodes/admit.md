# Node: admit

**Verb:** claim
**Writes:** `.bulma-goal/STATE.md`

## Steps

1. Load `bulma-memory`. Resolve `$BULMA_ROOT` ([DISK.md](../../bulma-bus/DISK.md)).
2. Write STATE from [templates/STATE.md](../templates/STATE.md). Record `goal`,
   `tracker`, `tracker_id`, and `pr_url` when the args already name a PR.
3. Name the completion bar:

```text
Draft PR for <id> is CI-green, MERGEABLE, and has a bulma-qa
comment on the head SHA that includes evidence.
```

4. If the host has a goal register (`/goal` or equivalent), record that sentence
   there and store the handle as `host_goal`. If it does not, STATE is enough.
5. No PR yet → **step** with developer `deliver`. PR exists → **inspect**.

## Never

- Create a second loop when STATE already has `loop_id`.
- Restart delivery for a PR that is already green.
