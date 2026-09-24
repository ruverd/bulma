# Contributing

Bulma is a set of agent skills, not an application. What you change here is
instructions that an AI model follows. So the review question for every change
is: can a model that has never seen this repo follow this step one way only?

## Set up a development checkout

```bash
git clone https://github.com/ruverd/bulma.git
cd bulma
./install.sh setup
```

`./install.sh setup` points the `bulma` command and every agent at this
checkout, so your edits take effect after you restart the agent. In this
checkout, `bulma update` runs `git pull`.

## Repo layout

| Path | What lives there |
|---|---|
| `skills/` | One flat folder per skill. Each has a `SKILL.md` with `category: graph`, `engine`, or `lib` |
| `agents/` | Contracts for workers and stage roles. These are not skills |
| `commands/` | Slash command aliases. Each one points at a skill and defines no steps |
| `docs/` | Pages for people. [docs/README.md](docs/README.md) lists them |
| `skills/bulma-host/` | How each coding agent starts workers and schedules later turns. Anything agent-specific goes here |
| `tests/` | The checks listed below |

The skill categories:

- `graph`: a stage with its own graph of steps, such as `bulma-developer`
- `engine`: a large job that stages call, such as `bulma-feature-delivery`
- `lib`: a small shared skill, such as `unslop` or `tdd`

Read [docs/GRAPH_ENGINEER.md](docs/GRAPH_ENGINEER.md) before you add or change
a graph.

## Run the tests

```bash
bash tests/repo.sh              # links, frontmatter, manifests, structure
bash tests/install.sh           # the bulma CLI: setup, update, uninstall, flags
bash tests/bulma.sh             # the /bulma router, hooks, watch, and lookback
bash tests/bulma-developer.sh   # risk levels, split review verdicts, resume
bash tests/bulma-code-review.sh # spec first, findings bound to the patch, critic
bash tests/bulma-lstm.sh        # comment binding, proof before reply
bash tests/bulma-qa.sh          # QA clips and evidence rules
bash tests/before-and-after.sh  # the PR screenshot formatter
```

CI runs all of them on every push. `tests/repo.sh` needs `python3`, and it
also runs `shellcheck` when `shellcheck` is installed.

If you have the Grok CLI, also run `grok plugin validate .` to check the Grok
plugin manifest.

## Add a skill

1. Create `skills/<name>/SKILL.md`. Set `name` to the folder name, set
   `category`, and write a `description` that says when to use the skill.
2. Use relative links only. After install, every skill sits next to every
   other one, so link to another skill as `../<other-skill>/FILE.md`. A link
   that leaves the skills folder, such as `../../docs/ARCHITECTURE.md`, breaks
   on agents that resolve paths as text.
3. Put agent-specific details in `bulma-host`. Put repo-specific details in
   [PRODUCT.md](skills/bulma-feature-delivery/PRODUCT.md) and the target repo.
   Never write `~/.claude`, `~/.grok`, `~/.cursor`, `~/.codex`, a model ID, or a
   person's handle into a skill.
4. Add the folder path to `plugin.json` and `.claude-plugin/plugin.json`. Add
   the name and description to `.grok-plugin/plugin-index.json`.
5. Run `./install.sh setup`, then `bash tests/repo.sh`. The test names anything
   you missed in steps 1 to 4.

## Write for people and for models

- Write skill files, commit messages, pull request text, and CI output in
  English. The chat language follows `bulma-memory`.
- Apply the bundled [unslop](skills/unslop/SKILL.md) skill to anything a person
  reads.
- For pages in `docs/`, follow [technical-writing](skills/technical-writing/SKILL.md).
  Each page is one kind: a tutorial, a how-to guide, a reference, or an
  explanation. Add new terms to [docs/glossary.md](docs/glossary.md).

## Third-party skills

`skills/` includes copies of skills from other projects, so a clone works
without extra marketplaces. When you add or update one, keep its origin and
license row in [THIRD_PARTY.md](THIRD_PARTY.md) correct.
