# Investigation

Answer the named question from source, history or runtime artifacts. Keep facts,
inferences and unknowns distinct. Search only relevant connected sources. Use
`how` for a named subsystem gap; do not spawn a full investigation for a lookup.

Record source locations and the evidence behind the recommendation in the
`sources` proof. The `answer` proof contains the cited explanation or alternatives
with tradeoffs. Disprove the premise when the evidence calls for it.

No product edits, branch creation, commits, pushes or PR. Runtime captures may
write disposable evidence outside the checkout, with existing access only.
Do not instrument shared production or provision services as part of this mode.
Stop at `done_report` after the playbook check. Planning-only requests likewise
return the requested plan rather than beginning implementation.
