# Coder cost pilot

Eight small execution cases complement routing/plugin evals. This is a pilot for
coder instructions, not an end-to-end factory benchmark. Two cases reduce the
Empath #2430 warning and missing-database findings; the others model documented
Bulma defect classes. No claim that these are archived production task replays.

Each arm starts in a fresh temporary workspace. The baseline contains Bulma's
current LESSONS.md and the bounded coder mission. The candidate appends the short
reuse ladder in compact-reuse.md. Neither changes the installed coder. No Ponytail
plugin, extra reviewer, hooks, memory or MCP server is loaded. Tools are limited
to reading/editing files and Node commands. This is not an OS security sandbox;
use trusted fixtures only. Agent-generated code runs locally.

To include the full Ponytail prompt, download a reviewed revision outside this
repo and pass `--ponytail-file /path/to/SKILL.md`. The third arm appends that prompt
without installing the plugin. Record its source commit alongside results. Use
`--arm ponytail` to run only that arm, or omit --arm to compare all available arms.
At the default budget, all three arms request a $6 ceiling for one eight-case run.

The runner withholds executable assertions until the host returns, then grades
code using Node assertions, not an LLM judge. The verifier does not establish that
the agent's own tests are good, nor cover every possible product behavior. A host
error or budget stop cannot win on correctness even if the resulting code passes.
Missing usage stays unknown. Results keep actual model ids, host version, prompt
and fixture hashes, input/output/cache usage, cost, turns and delivered code.

```bash
python3 evals/factory/run.py --model claude-haiku-5-5 --runs 1 \
  --budget-per-run 0.25 --out "$HOME/.bulma/evals/coder-pilot-001"
```

Requires authenticated Claude Code and Node. Paid, explicitly opt-in; never part
of CI. The command requests at most $4 across 16 sessions; provider billing and a
final in-flight request can exceed a CLI budget. A timeout may leave usage unknown.
Use --case to select cases. Existing output directories are refused.

One run is a smoke comparison, not a reliable savings estimate. Before promoting,
repeat paired cases with the production model and include full repository replays.
Compare cost per correct result and inspect critical regressions, not output length
alone. Reject a cheaper arm that loses a required criterion. Keep failed runs in
the denominator and cost total. Do not update production prompts from one sample.
