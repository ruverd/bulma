# skills

Marketplace of Ruver agent skills. Not an application repo.

- Canonical skill files live under `skills/<name>/`, one flat directory each, with `category: graph | engine | lib` in the frontmatter.
- `category: lib` marks bundled primitives (`unslop`, `grill-with-docs`, `receiving-code-review`, `principle-*`, `before-and-after`, the `ruver-bus` protocol, the `ruver-host` contract). Graphs must load those, not an external marketplace.
- Every skill is a sibling of every other, so all cross-skill links are
  `../<name>/FILE.md` (`../ruver-bus/PROTOCOL.md`). No link may leave the skills
  root: the repo root is unreachable once a skill is installed. The host contract
  is the `ruver-host` skill, not a root file, for this reason.
- `ruver setup` links `skills/<name>` into shared/host skill homes. When Codex is installed, shared `~/.agents` home gets managed copies so Codex does not namespace standalone skills through root `plugin.json` or discover duplicates. Installed layout still matches git, so no link may leave the skills root.
- Invocation syntax depends on the host. Codex users invoke public Ruver skills as `$ruver-<name>` or select them through `/skills`. Never tell Codex users to run `/ruver-*`; Codex rejects external slash commands before skill routing. Claude Code and Grok users invoke `/ruver-*` or the short aliases in `commands/`. Skill ids stay `ruver-*`.
- Do not write `.ruver-*` state in this repo. Runtime state belongs in `~/.ruver/<slug>/`. User/project memory: `~/.ruver/memory.md` and `$RUVER_ROOT/memory.md` (`ruver-memory`).
- Graphs are host-agnostic. Harness APIs live in `ruver-host`. See `docs/GRAPH_ENGINEER.md`.
- After a skill edit, run `ruver setup` (or `./install.sh setup`) if you use the symlink install. Plugin installs pick up git updates with `grok plugin update ruver`. End users: `ruver update`.
- Skill bodies stay in English. Chat follows `ruver-memory` (default English). Forge text (PR, review, comments) stays English. Unslop always.
