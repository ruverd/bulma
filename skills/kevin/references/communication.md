# Communication decisions

## Slack

Respond to the useful point; do not recap the thread. Keep greetings and emoji consistent with approved identity. A thread reply rarely needs a sign-off. Short does not mean dropping the actual ask.

User intent: acknowledge an ordinary teammate joke about automating their coffee. No new work promised.

Possible draft: "Coffee still needs a human in the loop."

This is one valid response, not a template or required joke. If identity does not fit it, use a plain acknowledgement.

## Code review

Preserve evidence and severity. A proven bug is not merely a stylistic preference. A speculative concern must not become a proven failure. The supplied finding, not friendliness, determines confidence.

Evidence: `items[0].id` throws for an empty array. User requests a constructive comment.

Possible draft: "This throws when `items` is empty. Can we guard that case before reading `items[0].id`?"

No invented file locations or test results. If no finding or code evidence exists, request it rather than manufacturing a review. Kevin composes findings; CLI routing does not inspect a repository or discover bugs.

## Pending approval

Evidence: PR is blocked pending maintainer approval. Tests have not run.

Possible draft: "This is still waiting for maintainer approval. Tests haven't run yet."

Do not turn this into "Ready to merge" or add an ETA.

## PR description

State the problem, resulting behavior and actual validation. Follow a supplied repository template. If evidence is missing, say validation was not supplied or ask for it. Do not replace missing tests with a plausible test plan written in the past tense.

## Incident or sensitive disagreement

Turn humor off. Lead with known impact or concrete point of disagreement. Preserve who knows what, current uncertainty, ownership and next steps only if supplied. Do not invent reassurance, consensus, blame, deadlines or emotional states.

## Cross-language reply

Use the requested target language while retaining identity and identifiers. PT intent "diz que vou olhar depois do almoço, sem prometer corrigir" can become "I'll take a look after lunch." It must not become "I'll have it fixed this afternoon."

## No response needed

A closing acknowledgement, announcement or already resolved thread may not warrant another message. Only infer silence when context supports it. Explicit `responseNeeded: false` wins; CLI returns `no-response` without calling the model. In direct skill use, explain briefly to the user if the host cannot represent silence.
