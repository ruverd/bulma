# Node: code_review

**Verb:** review
Run **ruver-code-review** in full (`--force` if CI red). That engine
writes the spec-first `AC.md`, binds findings to the patch, and spawns
the high-risk critic when `classify-risk.py` prints `high`. Do not spawn
a second critic here.
Pending required CI is **wait_ci**, not this node.
Draft / conflict / CI-red DEFER is expected — keep going to diagnose.
