# skills

Marketplace of Bulma agent skills. Not an application repo.

- Canonical skill files live under `skills/<name>/`, one flat directory each, with `category: graph | engine | lib` in the frontmatter.
- `category: lib` marks bundled primitives (`unslop`, `grill-with-docs`, `receiving-code-review`, `principle-*`, `before-and-after`, the `bulma-bus` protocol, the `bulma-host` contract). Graphs must load those, not an external marketplace.
- Every skill is a sibling of every other, so all cross-skill links are
  `../<name>/FILE.md` (`../bulma-bus/PROTOCOL.md`). No link may leave the skills
  root: the repo root is unreachable once a skill is installed. The host contract
  is the `bulma-host` skill, not a root file, for this reason.
- `bulma setup` links `skills/<name>` into shared/host skill homes. When Codex is installed, shared `~/.agents` home gets managed copies so Codex does not namespace standalone skills through root `plugin.json` or discover duplicates. Installed layout still matches git, so no link may leave the skills root.
- Invocation syntax depends on the host. Codex users invoke public Bulma skills as `$bulma-<name>` or select them through `/skills`. Never tell Codex users to run `/bulma-*`; Codex rejects external slash commands before skill routing. Claude Code and Grok users invoke `/bulma-*` or the short aliases in `commands/`. Skill ids stay `bulma-*`.
- Do not write `.bulma-*` state in this repo. Runtime state belongs in `~/.bulma/<slug>/`. User/project memory: `~/.bulma/memory.md` and `$BULMA_ROOT/memory.md` (`bulma-memory`).
- Graphs are host-agnostic. Harness APIs live in `bulma-host`. See `docs/GRAPH_ENGINEER.md`.
- After a skill edit, run `bulma setup` (or `./install.sh setup`) if you use the symlink install. Plugin installs pick up git updates with `grok plugin update bulma`. End users: `bulma update`.
- Skill bodies stay in English. Chat follows `bulma-memory` (default English). Forge text (PR, review, comments) stays English. Unslop always.
