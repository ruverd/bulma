# Skill evals

These checks answer one question: does the host pick the right Bulma skill
for what a user says, and does the reply change when it does? The structural
checks in `tests/` cannot see that. A skill whose description misses the
words users say never runs, however good its body is.

There are two tiers. The first runs in CI and costs nothing. The second calls
a model and runs only when you start it.

| Tier | Checks | Where | Cost |
|---|---|---|---|
| Routing | A prompt ranks its skill in the top 3. A prompt a skill must not take does not rank it first. No two descriptions are near-duplicates | `evals/routing/*.json`, run by `tests/lib/check_routing.py` from `tests/repo.sh` | Free |
| Plugin | The real Claude Code router fires the skill on a natural prompt, and the reply does what the skill promises | `evals/plugin/<case>/`, run by `claude plugin eval` | Tokens |

## Routing tier

The check scores each prompt against every skill's name and description with
stemmed TF-IDF. That is a lexical stand-in for the host's choice, so it
catches two failure modes and nothing else:

- **Missing vocabulary.** A positive prompt does not rank its skill in the top
  3. Fix the description so it carries the words people use.
- **Over-broad description.** A negative prompt ranks the wrong skill first,
  or two descriptions score above the similarity limit. Narrow one of them.

A failure usually means fix the description, not the case. All descriptions
together must stay under the 8,000-character discovery budget in
`tests/lib/check_frontmatter.py`, so a new trigger phrase usually means
removing a weaker one.

One file per skill, named after it:

```json
{
  "skill": "diagnose",
  "positive": [{ "prompt": "The export job is broken, debug this" }],
  "negative": [{ "prompt": "Write the docs for the export job", "owner": "technical-writing" }]
}
```

`top_k` on a positive prompt overrides the default of 3. `owner` on a negative
prompt names the skill that should take it; that skill must rank in the top 3.
Write prompts the way a user would type them, not by copying the description.

```bash
PYTHONPATH=tests/lib python3 tests/lib/check_routing.py . --verbose
```

`MIN_RANK1` in the script is a ratchet: the share of positive prompts that
rank their skill first. Raise it when descriptions improve. Do not lower it to
make a change pass.

## Plugin tier

`claude plugin eval` loads the whole plugin and runs each case under
`evals/plugin/` with and without it. `.claude-plugin/plugin.json` points the
command at this folder through `experimental.evals`.

```bash
claude plugin eval . --no-publish                              # every case, both arms, 3 runs each
claude plugin eval . --case diagnose-fires-on-slowdown --runs 1 --ablation none --no-publish
```

A case is a folder with `prompt.md` (frontmatter: description, outcome, turn
and tool limits; body: the prompt, sent verbatim) and one grader per file
under `graders/`. Quote frontmatter values that contain a colon. Results land
in `evals/plugin/results/`, which git ignores.

Pair a `tool_used: Skill` grader with a grader on the reply. In a two-arm run
the fire indicator is left out of the score, so on its own it measures
nothing. A `min: 0` / `max: 0` grader is a must-not-fire check.

A skill with `disable-model-invocation: true` (such as `tdd`) only runs when
the user types its command. Do not write a fire case for it; grade the reply
instead.

Firing is stochastic. Read the scores across several runs, not one exit code.
When you report numbers, record the Claude Code version and pin `--model`,
because the default model can change between runs.

## Rejected changes

Description changes that the evals showed did not help. Read this before you
propose an overlapping change. Add one row per rejected attempt. Do not record
accepted changes here.

| Date | Skill | Attempted change | Result |
|---|---|---|---|
| 2026-10-21 | receiving-code-review | Add "pasted or on a PR" so it fires on a review comment pasted in chat | `receiving-review-pushes-back`, 4 runs each, Claude Code 2.1.306: fired 0/4 before and 0/4 after. The reply declined the wrong suggestion correctly in all 8 runs. Reverted |
