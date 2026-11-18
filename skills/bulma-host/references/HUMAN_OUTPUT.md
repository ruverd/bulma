# Human-facing output

Use [Kevin](../../kevin/SKILL.md) for Bulma's human-facing prose. Supply the
destination, audience, and selected profile binding through the host. Keep
protocol records, logs, code, verdicts, hashes and evidence outside the voice layer.

Answer's JSON-lines `mode: "compose"` accepts `messages`, verified `facts`, reply
`intent`, and a trusted communication `context`. Supply `github_organizations`
for verified GitHub citations. Choose `reference_style` as `markdown` (default)
or `angle_label` for the destination's link syntax. Neither field grants work.

Bind `compile_kevin(request)` to the destination's Kevin profile and
`decide(policy, schema, data)` to a tool-free structured provider. Bulma checks
the result against verified facts and returns final `text` with delivery metadata.
The host verifies the destination and delivers the exact returned text with
approved artifacts. If a verified screenshot cannot be attached, use the
returned `without_attachment` variant when present.
