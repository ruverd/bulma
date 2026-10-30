## PR run attribution

Every PR/MR needs its own separate, final `## Agent run` description section, including every stacked child and fullstack sibling.
Parent sections, stack summaries, links and comments do not satisfy a child. Keep repository templates; append [PR_BODY.md](../bulma-feature-delivery/templates/PR_BODY.md)'s section if missing.
Record actual model and reasoning effort for that PR's work. Resolve model per
[Review model identity](SKILL.md#review-model-identity); read effort from runtime metadata or explicit system-provided settings.
Never infer execution from requested tiers, config defaults or parent settings.
Use `unknown` per unavailable field. List each contributing session's distinct
model/effort pair with its role, including implementation and code review workers. Exclude
unrelated stack work. Preserve earlier contributions and add new pairs on fixes.
Include time and host-reported tokens per the template. After creation and before completing any update, read back each affected PR's saved description.
Verify model and effort are present and nonempty, including each stacked child.
PR descriptions also name code review model and effort separately from implementation, copied from the reviewer result for that PR.
Missing attribution means packaging is incomplete; repair before reporting done.
