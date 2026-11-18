---
name: bulma
category: graph
description: Jev-gated router and overlay for bulma graphs. Use when /bulma.
argument-hint: "<empty | ticket | PR url | text | power <level> | report | watch | lookback | resume>"
---

# Bulma (graph)

Orchestrator. You do not implement product code. You never merge.

Bulma decides **which** bulma graph runs now, loads it on this thread, and
stays loaded while it runs. At each fork listed in [HOOKS.md](HOOKS.md) it asks
TypeSafe Jev a typed question and acts on the answer when confidence clears a
threshold the user controls ([POWER.md](POWER.md)). Code owns the edges; Jev
only picks among options the node already has.

**REQUIRED:** [GRAPH.md](GRAPH.md) · [ARGS.md](ARGS.md) ·
[STATE.schema.md](STATE.schema.md) · [HOOKS.md](HOOKS.md) ·
[POWER.md](POWER.md) · [DISPATCH.md](DISPATCH.md) ·
[REQUIREMENTS.md](REQUIREMENTS.md) ·
[bulma-host](../bulma-host/SKILL.md) · [DISK.md](../bulma-bus/DISK.md)
(`.bulma-*` is **global**, never the git root) · `bulma-memory`

Chat: `bulma-memory`. Apply Kevin for human-facing communication. Scripts live in `scripts/` next to this
file; the host tells you where the skill directory is. Run them with
`python3` and `bash`.

## Requirement

Every other graph works without Jev. This one does not. `admit` runs
`scripts/bulma.py doctor`; exit 2 or 3 means print the message it returns in
the chat language, write `status: blocked`, and stop. Nothing else runs.
Details: [REQUIREMENTS.md](REQUIREMENTS.md).

## Start

1. Load `bulma-memory`. Resolve `$BULMA_ROOT`. Init `.bulma-core/STATE.md`
   from [templates/STATE.md](templates/STATE.md) unless one is live.
2. Parse args with [ARGS.md](ARGS.md) **before** any Jev call. Local verbs
   (`power`, `tune`, `model`, `timeout`, `report`, `status`, `doctor`, `watch`,
   `lookback`) run and stop.
3. Walk [GRAPH.md](GRAPH.md): **admit → inventory → route → overlay → done**.

## Routing

Deterministic first: a tracker id or tracker URL goes to `developer` with no
Jev call. Bare PR or MR refs go by author with no Jev call: the user's own PR
goes to `qa`, anyone else's to `reviewer`. A PR ref with other words, or free
text, goes through `entry.route`. Empty args or `resume` go through `entry.next_step` over the
candidates `scripts/world.sh` found. Below threshold, or under `shadow` and
`cautious`, bulma suggests and waits; it never guesses a graph.

## Overlay

After `load_graph <target>` follow that graph exactly. When it (or an engine
it loads) reaches a node in HOOKS.md, ask first, then write the field:
`act: true` means Jev's value, `act: false` means the graph's own rule.
Bus switches inside the target keep the overlay. Bulma never appears on
`STACK.md`. Jev down mid-run means fallback and continue; only `admit`
stops. Contract: [nodes/overlay.md](nodes/overlay.md).

Workers: the overlay also picks the tier each coder worker runs on
(`dispatch.tier`), escalates it on a fail, and never lowers a gate.
[DISPATCH.md](DISPATCH.md).

## Watch

`/bulma watch` checks every workspace under `$BULMA_HOME`, not just this repo,
and lists stalled work, work that needs the user, and orphaned work, each with
its next command. It reconciles against GitHub first, so a PR that already
merged is not reported as stuck. Report only, no key.
[nodes/watch.md](nodes/watch.md).

## Lookback

`/bulma lookback` counts what human reviewers caught and the graphs missed, by
cluster, per reviewed PR, against the previous window of the same length. Each
cluster names the skill section meant to stop it, so a cluster that does not
shrink after that section changed shows the change failed. It proposes skill
edits and opens a draft PR only after the user says yes. No key.
[nodes/lookback.md](nodes/lookback.md).

## Power

`shadow | cautious | balanced | bold`, global or per hook, plus a per-question
`act_at` override, all in `$BULMA_HOME/bulma.json`. `/bulma power <level>`,
`/bulma tune <hook.question> <act_at>`, `/bulma report`. Math and the
calibration loop: [POWER.md](POWER.md).

## Chat shape

```text
S: bulma route -> developer (DEV-4772)
J: target=developer (deterministic: ticket id)
P: developer admit
```

One `J:` line per hook while the overlay runs, for example
`J: path=debug_fix .88 ok · risk=elevated .61 -> ROUTING`.

## Never

- Enter the bus stack, spawn a graph, merge, or write product code.
- Skip a gate or invent an edge because Jev said so.
- ASK the user because Jev was undecided. Undecided means the graph rule.
  The only hook that can produce ASK is `policy.ask`, inside
  `../bulma-feature-delivery/DECISION_POLICY.md`.
- Send full files to Jev. Caps are in HOOKS.md.
- Run any hook before `doctor` passed in this run.
- Write outside `$BULMA_ROOT/.bulma-core/`, `$BULMA_HOME/bulma.json`, and
  `$BULMA_HOME/bulma-watch.json`.
- Print `TYPESAFE_API_KEY`.

## Bulma Answer

Hosts receiving an open-ended thread can call [answer.py](scripts/answer.py) before composing a reply. Pass ordered turns with verified speaker IDs, thread membership and attachment evidence, a structured model adapter, verified identity mappings and read-only source adapters. The model selects evidence and can request additional reads after seeing results. Work decisions retain independent feedback and review actions for each verified PR. The host rechecks identity, commit and workflow gates before execution and gives Kevin the decision and actual receipts for wording.

For `answer` in chat, inspect the supplied thread and attachments, consult project code for application questions and the owning review policy for gate questions. Reassess the evidence and verify findings at the relevant revision. For work, invoke [reviewer](../bulma-reviewer/SKILL.md) or [feedback](../bulma-lstm/SKILL.md) for the authorized targets, preserving both when applicable. Return actual receipts or a specific outstanding dependency. Ask Kevin to phrase that result.

For a subprocess host, run `python3 scripts/bulma.py answer`. Its JSON-lines session starts with `messages`, `repositories` and verified `identities`. Each turn supplies `ts` (an opaque event ID), `user`, `role`, `in_thread`, `text`, optional extracted `references` and attachment evidence in `files`. For each `{"call": ..., "args": [...]}`, reply with `{"result": ...}` or `{"error": "..."}`. The host supplies structured inference, author lookup, evidence reads and transactional dispatch. The final envelope contains `intent`, factual `content` (dispatch receipts for work), and `jobs`. Delivery belongs to the host. An in-process host may reuse the same investigation function and commit dispatch with its inbox transaction.

A host can opt a channel into team participation with `participation: {"audience": "team_open", "assistant": {"id": "...", "names": [...]}, "owner": {"id": "...", "names": [...]}}`. Supply the complete current post and relevant thread turns with their original mentions. Answer interprets audience across the post, contributes to open conversations, and scopes requested actions and prerequisites to each PR. Pending work yields reply facts or `waiting` facts alongside independent dispatchable work. Hosts carry those facts into the reply. A prerequisite alone never grants future dispatch authority.

Include `thread_ts` to identify the thread root even for background turns with `in_thread: false`. Those turns supply context for the current message. A host may mark same-author link bullets that continue the current request with `request_continuation: true`, after verifying their association with the request.

For visual evidence, advertise `attachment_images: true` and include opaque `image_id` values in `files`. Answer requests up to four images via `read_images(policy, schema, data)`, prioritizing the current message, its thread, and relevant recent background. The host binds the requested IDs to temporary image bytes, invokes its multimodal provider with the supplied policy, and returns a map from ID to `{"status": "vision" | "OCR", "text": "..."}`. Omit unreadable entries. Never send attachment credentials, authenticated URLs or local paths as model text. When the provider cannot read an image, mark extracted text as `OCR`. Raw images do not enter dispatch records.

For that audience, the host's `linked_review_organizations` may authorize review of explicitly referenced GitHub PRs across named organizations. These PRs require a reference from the requesting author in the same request. The profile's optional `linked_review_organizations` can narrow this capability, and its `actions` still applies. The organization scope grants no author-wide lookup, code search, or feedback workflow access. The host still verifies GitHub access and the checkout before execution.

To enable authenticated direct requests, provide `direct_request` with the current `ts`, verified `user`, their authored `utterance`, and authorized `capabilities` chosen from `investigate`, `qa`, `review` and `address_feedback`. Hosts verify the author and destination using their own transport. Exclude quotes and code from `utterance`. A normalized `addresses` array can bind rendered text to a participant as `{"user": "...", "text": "..."}`. Answer matches that text or an unambiguous vocative in the current utterance. An optional `direct_only` limits participation to direct address. Earlier turns provide context and evidence.

Bind `read_investigation` to allowlisted read-only product evidence with the same arguments as `read`. It grants no command execution, environment access or mutation. Filter sensitive content before inference or composition and check the final text before delivery. Deletion, changes to the assistant or its rules, unsafe operations and disclosure requests return policy replies. The existing PR workflows keep their explicit requester, target and evidence requirements.

Hosts may advertise `qa_targets` with safe target IDs, environment labels and steps. Bind `run_qa(event, target, pr)` to the direct [Bulma QA reproduction executor](../bulma-qa/references/THREAD_REPRO.md). The host rechecks the target before execution and owns delivery of approved artifacts. A QA request returns a reply with its evidence or blocker and does not dispatch a PR review.

Compose a human-facing result with [the host's Kevin binding](../bulma-host/references/HUMAN_OUTPUT.md) once the verified facts are available.

Answer reads its own local memory at `$BULMA_HOME/answer/memory.json` (default `~/.bulma/answer/memory.json`). A host may explicitly select another profile with `--memory PATH`. Configure `guidance` for workflow preferences, `repositories` to narrow host-authorized repositories, and `actions` to enable any subset of `review` and `address_feedback`. For advisory-only use, set `actions` to `[]`. Missing fields use host capabilities. Profiles are independent. They never add permissions, override current instructions or change Kevin's voice. In chat, apply this profile specifically for Answer before selecting workflows.

Hosts can advertise other PR workflows in the opening `workflows` array. Answer intersects these with profile actions and returns enabled names in each target’s `workflows` field. The dispatch adapter validates each capability and returns its own receipt.
