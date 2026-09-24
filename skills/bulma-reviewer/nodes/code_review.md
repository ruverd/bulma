# Node: code_review

**Verb:** review
Run **bulma-code-review** in full (`--force` if CI red). That engine
writes the spec-first `AC.md`, binds findings to the patch, and spawns
the high-risk critic when `classify-risk.py` prints `high`. Do not spawn
a second critic here.
Pending required CI is **wait_ci**, not this node.
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
