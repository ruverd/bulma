# Context assignments

Use named rules to choose a voice for an action, a Slack channel or a particular recipient. Use only metadata supplied by the user or already available in the authorized task. Kevin does not fetch a workspace directory, determine a relationship, or identify the actual channel from a quoted message.

Context selectors include `platform`, `task`, `audience`, `seriousness`, `energy`, `language`, `workspace`, `channel`, `recipient`, `existingHumor` and `responseNeeded`. All declared conditions must match exactly. Prefer stable platform IDs, including a workspace for channel/person disambiguation. A name is usable only when explicitly supplied as the intended routing key; do not guess that a mention maps to it.

Example rule:

```json
{
  "name": "team-channel",
  "priority": 80,
  "when": {"platform": "slack", "workspace": "T_EXAMPLE", "channel": "C_EXAMPLE"},
  "voice": "witty-engineer",
  "overrides": {}
}
```

Another rule can target `task: "review"` or `recipient: "U_EXAMPLE"`. Higher integer priority wins; declaration order breaks ties. Only the first matching rule applies. If a recipient assignment should win over a channel assignment, give it a higher priority explicitly. There is no hidden specificity scoring. Starter serious-context rules have priority 100/90; CLI user rules default to 80. A higher-priority custom rule can keep its voice in serious contexts, but it cannot enable forbidden humor.

Selection order: manual voice, matching configured rule, saved default or bundled `tony-stark` starter. Missing unrelated fields do not cancel a match. Unknown seriousness still disables humor. Rules and voice choice cannot make private notes from another voice available.

With CLI:

```bash
kevin rule set reviews --task review --voice professional-reviewer
kevin rule set team-channel --platform slack --workspace T_EXAMPLE --channel C_EXAMPLE --voice witty-engineer --priority 80
kevin rule set one-person --platform slack --workspace T_EXAMPLE --recipient U_EXAMPLE --voice minimalist --priority 85
kevin rules
kevin rule remove team-channel
```

With file tools, an explicit request naming the voice and target authorizes a focused change to that named rule, preserving unrelated rules, identity and default. Validate the voice exists and the target metadata is sufficient. If a required target is missing, ask one concrete question. Without tools, return the proposed rule and state that it has not been saved.
