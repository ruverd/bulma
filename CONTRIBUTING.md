# Contributing

This repo is a marketplace of agent skills, not an application. The thing you
ship is instructions an agent follows, so the review bar is about whether a node
can be executed unambiguously by a model that has never seen this repo.

## Layout

| Path | What lives there |
|---|---|
| `skills/` | Skills. Each has `SKILL.md` with `category: graph \| engine \| lib` |
| `agents/` | Worker and role contracts. Not skills |
| `commands/` | Slash aliases. Each points at one skill and defines no steps |
| `docs/` | Human-facing pages, one per command |
| `skills/ruver-host/` | Harness primitives. Anything host-specific belongs here |
| `tests/` | Gates, described below |

Read [docs/GRAPH_ENGINEER.md](docs/GRAPH_ENGINEER.md) before adding a graph.

## Gates

```bash
bash tests/install.sh          # the ruver CLI: setup, update, uninstall, flags
bash tests/repo.sh             # repo invariants: links, frontmatter, manifests, structure
bash tests/before-and-after.sh # PR stills formatter + session dir
bash tests/ruver-qa.sh         # QA walk video is the plan, not qa:login
bash tests/ruver-code-review.sh # spec-first, patch bind, high-risk critic
```

These run in CI on every push. `tests/repo.sh` needs `python3`, and it runs
`shellcheck` when that is installed. Using the skills still needs `git` and
`curl`; `ruver setup` also installs `agent-browser`.

## Adding a skill

1. `skills/<name>/SKILL.md` with `name` matching the directory, a `description`
   that says *when* to use it, and `category`.
2. Relative links only, and none that leave the skill's own directory. After
   install every skill is a sibling, so `../<other-skill>/FILE.md` resolves the
   same in git and on disk. A link like `../../docs/ARCHITECTURE.md` only works on hosts
   that follow symlinks with the kernel and breaks on hosts that normalise the
   path string first.
3. Host primitives go in `ruver-host`. Product policy goes in `PRODUCT.md` and the
   target repo. Never hardcode `~/.claude`, `~/.grok`, `~/.cursor`, `~/.codex`,
   a model id, or a company's handles.
4. List the path in `plugin.json` and `.claude-plugin/plugin.json`. The Grok
   plugin index is derived from frontmatter, so do not hand-edit it.
5. Run `./install.sh setup` if you install by symlink, then commit.

`bash tests/repo.sh` will tell you which of these you missed.

## Writing style

Skill bodies, commit messages, PR text and CI output are English. Chat language
follows `ruver-memory`. Apply the bundled `unslop` skill to anything a person
reads.

## Third-party skills

`skills/` bundles copies from other projects so a clone runs without extra
marketplaces. Keep the origin and licence rows in
[THIRD_PARTY.md](THIRD_PARTY.md) accurate when you add or update one.
