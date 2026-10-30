# Node: code_review

**Verb:** review
Run **bulma-code-review** in full (`--force` if CI red). That engine
writes the spec-first `AC.md`, binds findings to the patch, and spawns
the high-risk critic when `classify-risk.py` prints `high`. Do not spawn
a second critic here.
Pending required CI is **wait_ci**, not this node.
The engine's [preflight](../../bulma-code-review/references/PREFLIGHT.md) runs
before review and publication. Read human and AI QA concerns before posting.
AI QA `BLOCKED` (could not run) never blocks review; QA `FAIL` blocks APPROVE
and needs human approval;
the observation collection below is telemetry, not a replacement for that gate.
Apply the engine's [evidence rules](../../bulma-code-review/references/EVIDENCE.md)
within that same pass: preserve the checkout, verify regression assertions and
check paired deployment compatibility when applicable. Do not run a second
review or publish a separate checklist.
The engine's `gate.py` decides whether an APPROVE posts; this node never
posts a review around it. A gate DEFER, a bot-quorum COMMENT, or a dismissed
stale approval is an engine outcome to report, not something to retry.
Draft / conflict / CI-red DEFER is expected — keep going to diagnose.

After the engine publishes, fetch the PR's reviews, inline comments, and issue
comments (`gh api repos/<repo>/pulls/<n>/reviews|comments`,
`issues/<n>/comments`, `--paginate`). Record each human comment with
`../bulma-bus/scripts/observe.py --source reviewer --claim-true unknown` (path
from this skill's directory), passing `--ours-open` from the marker this run
just wrote.
[INSIGHTS.md](../../bulma-bus/INSIGHTS.md) has the rules. Ids already in the
file print `duplicate`, so a re-review adds only new comments. A failed write is
a chat note, never a reason to change the review.

## Learn from external concerns

Before the engine pass, read matching project `## Prevention` entries for
`review`, as required by its Phase 1. Compare current external concerns with
prior review evidence at the affected head. After the verdict, assess confirmed
gaps through [FEEDBACK.md](../../bulma-bus/FEEDBACK.md). A request for changes
alone is not confirmation; leave unverified concerns pending. Include bot
findings in assessments, while preserving human-only observation rules above.
Reuse LSTM source keys and existing tasks. Never launch LSTM, a developer or QA
for this assessment. It cannot change or bypass the engine publication gate.
