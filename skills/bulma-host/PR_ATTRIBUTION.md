## PR run attribution

Publish model attribution only when the executing identity is known from runtime
metadata or explicit system identity. Follow [Review model identity](SKILL.md#review-model-identity).
Never infer execution from requested tiers, config defaults, CLI brands or parent
settings. Ambiguous aliases, missing values, `unknown`, `undefined` and `null` do
not qualify. Omit those contributors. Never publish reasoning effort.

When at least one model is known, append a final `## Agent run` section to each
PR/MR, including stacked children and fullstack siblings. List distinct known
models by role (implementation, code review, plan critic when it contributed).
Review attribution comes from that review's result and reviewed SHA; a shipper
or critic cannot stand in for the verdict reviewer. Preserve earlier supported
contributions on updates. Unknown contributors do not erase findings or results.
When none are known, omit the entire section, including its heading.

Keep repository templates and [PR_BODY.md](../bulma-feature-delivery/templates/PR_BODY.md).
Time and host-reported tokens can accompany a populated section; never estimate
usage. Internal effort controls and telemetry remain unchanged. After every
create/update, read back the saved description: no empty attribution, unknown
placeholders, unsupported identities or reasoning effort rows.

The bundled `scripts/model_identity.py --kind pr --records <json-file>` renders
known-only attribution from records shaped as
`{"role":"Implementation","identity":{"model":"fixture-v1","source":"runtime"}}`.
Use `--kind review` for the optional review table row. `source` is supplied by
the host/adapter from execution metadata, never accepted from model prose;
`ambiguous: true` omits aliases that do not establish the executing identity.
This formatter does not verify that an adapter told the truth. Keep the source
receipt internally. Append time/tokens only if a section was emitted.
