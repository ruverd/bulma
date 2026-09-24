# Glossary

Terms used across the Bulma docs, in alphabetical order.

## Agent

The AI coding tool you chat with: Claude Code, Codex, Cursor, or Grok. The
skills call it the host.

## Bus

The files that stages use to hand work to each other: a message file
(`ENVELOPE.md`) and a stack of active stages (`STACK.md`). See
[How Bulma works](how-it-works.md#how-the-stages-hand-off).

## Draft pull request

A pull request that GitHub marks as not ready for review. Bulma opens every
pull request as a draft and marks it ready only after QA passes.

## Engine

A skill that does one large job and that stages call: feature delivery
(`/bulma-fd`) and code review (`/bulma-code-review`). You can also run an
engine alone.

## Envelope

One message on the bus, for example `QA_REQUEST` from developer to QA. Each
envelope has a type, a sender, a receiver, and a pull request link.

## Graph

The written map of steps that a stage follows. Each step is a node, and the
arrows between steps are edges. A graph lives in the stage's `GRAPH.md` file.

## Head SHA

The ID of the newest commit on a pull request. QA evidence counts only when it
belongs to the head SHA, so a new push needs new QA.

## Hook

A point in a run where `/bulma` asks Jev. The full list is in
[HOOKS.md](../skills/bulma/HOOKS.md).

## Jev

A model from TypeSafe that answers a multiple-choice question with an answer
and a confidence score. Bulma asks Jev at a few judgment calls and uses the
answer only when the confidence is high enough. `/bulma` needs Jev. The stage
commands do not.

## LSTM

Short for "looks shit to me", a joke on "LGTM" (looks good to me). The `/lstm`
stage handles review comments on your own pull request.

## Mergeable

GitHub's word for a pull request with no conflicts against its base branch.
Bulma waits for a pull request to be mergeable and have green CI before QA.

## Power

How much Jev decides on its own: `shadow`, `cautious`, `balanced`, or `bold`.
See [Configuration](configuration.md#power-levels).

## `PR_BUG`

A problem that QA found and that the pull request itself caused. Triage also
uses `EXISTING_BUG` (already there), `NEW_BUG` (real, but not from this pull
request), `NOT_A_BUG`, and `BLOCKED` (could not be proved).

## Shadow mode

The power level where Jev answers every question but decides nothing. Bulma
logs the answers so that you can compare them with the built-in rules.

## Skill

A folder of instructions that a coding agent loads, with a `SKILL.md` file at
its root. Bulma is a set of skills.

## Stage

One part of the delivery loop: developer, QA, triage, reviewer, or LSTM. Each
stage is a skill with its own graph and command.

## State

The file where a stage records where it is in its graph. State lives in
`~/.bulma/`, so a run can continue in a later session.

## TDD

Test-driven development. The worker writes a test that fails, then writes the
code that makes it pass.

## Worker

A fresh agent that Bulma starts for one task, such as one ticket. Workers write
the code. The chat thread never does.
