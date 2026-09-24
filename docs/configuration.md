# Configuration

This page lists every setting, environment variable, command, and file that
Bulma uses. For a guided first run, see [Getting started](getting-started.md).

## Settings file

Machine-wide settings live in `~/.bulma/bulma.json`. Every repo on the machine
shares them. Bulma writes this file when you run the commands below. Do not edit
it by hand.

```json
{
  "power": "balanced",
  "power_by_hook": { "qa.gate": "shadow", "dispatch.tier": "shadow" },
  "act_at": { "fd.triage.path": 0.70 },
  "model": "jev-1.13.0",
  "tiers": { "claude": { "light": { "model": "haiku" } } }
}
```

| Key | Set with | Meaning |
|---|---|---|
| `power` | `/bulma power <level>` | How much Jev decides everywhere. Default `balanced` |
| `power_by_hook` | `/bulma power <level> <hook>` | The same, for one hook. Overrides `power` |
| `act_at` | `/bulma tune <hook.question> <value>` | The confidence Jev needs before Bulma uses its answer on one question |
| `model` | `/bulma model <id>` | The pinned Jev model. Default `jev-1.13.0` |
| `tiers` | See [DISPATCH.md](../skills/bulma/DISPATCH.md) | Which model each worker tier uses on each agent |

A hook is one point in a run where Bulma asks Jev.
[HOOKS.md](../skills/bulma/HOOKS.md) lists the hook and question names.

## Power levels

| Level | Effect on the threshold | When to use it |
|---|---|---|
| `shadow` | Jev never decides | First runs, and any new hook or model. Jev answers are logged only |
| `cautious` | +0.10 | Jev decides only when it is very sure. For routing, Bulma always asks you |
| `balanced` | none | The built-in thresholds |
| `bold` | −0.10 | Jev decides when it is fairly sure |

Thresholds always stay between 0.50 and 0.99. When several settings apply, the
first one in this list wins:

1. The `--power` flag
2. The `BULMA_POWER` environment variable
3. `power_by_hook` for the hook
4. `power`
5. `balanced`

To raise Jev's authority safely:

1. Run in `shadow` until a question has 20 or more logged decisions.
2. Run `/bulma report`. For each question, it prints `agree%` (how often Jev
   matched the built-in rule), `reversed` (answers later proved wrong), and
   `suggest` (a threshold that the log supports).
3. Raise one hook at a time, for example `/bulma power balanced fd.triage`.

[POWER.md](../skills/bulma/POWER.md) has the full decision rule.

## Per-repo settings

Bulma reads each repo's own files for anything specific to that repo: test
commands, reviewers, tracker, and related repos. It reads `AGENTS.md`,
`CLAUDE.md`, and `CONTRIBUTING.md` first, and those win over its own guesses.
[PRODUCT.md](../skills/bulma-feature-delivery/PRODUCT.md) lists what it looks
for and the order it looks in.

To set this repo's reviewers without editing the repo, use memory:

```text
/memory --project reviewers: alice, bob
```

## Environment variables

| Variable | Default | Meaning |
|---|---|---|
| `TYPESAFE_API_KEY` | none | Required for `/bulma` routing and hooks. The stage commands work without it |
| `BULMA_HOME` | `~/.bulma` | Where Bulma keeps settings, memory, and run state |
| `BULMA_POWER` | none | Overrides `power` and `power_by_hook` for this shell |
| `BULMA_FRONTEND`, `BULMA_BACKEND` | none | Paths to the matching frontend or backend repo for full-stack work |
| `BULMA_CI_LOCAL_SKIP` | none | Checks to leave to CI instead of running on your machine |
| `BULMA_SKIP_DEPS` | `0` | Set to `1` to stop `bulma setup` from installing and checking agent-browser. QA still needs it |

## Commands in your coding agent

| Command | Needs API key | What it does |
|---|---|---|
| `/bulma` | yes | Picks the next item across your open work |
| `/bulma <ticket, PR link, or text>` | yes | Routes the work to the right stage |
| `/bulma resume` | yes | Continues a run that stopped |
| `/bulma watch` | no | Lists stalled runs and the command to continue each |
| `/bulma lookback [--since <date>]` | no | Groups what human reviewers caught that Bulma missed |
| `/bulma report` | no | Shows how often Jev agreed with the built-in rules |
| `/bulma power [<level>] [<hook>]` | no | Prints or sets the power level |
| `/bulma tune <hook.question> <value>` | no | Sets one threshold |
| `/bulma model [<id>]` | no | Prints or pins the Jev model |
| `/bulma doctor` | no | Checks the setup |
| `/bulma status` | no | Shows the current run, the power level, and the last five Jev decisions |
| `/memory [--project] [<note>]` | no | Shows or saves a preference |

The stage commands are listed in [Commands](commands/README.md).

## Commands in your terminal

```text
bulma                 Menu, or the command list when not in a terminal
bulma setup           Add Bulma's skills to every coding agent found
bulma update          Pull the latest version, then run setup
bulma status          Show the version, the agents, and the run in this repo
bulma report          Show time and loops per step, and token use
bulma uninstall       Remove Bulma's links
bulma uninstall --purge
                      Also delete Bulma's copy of the repo
bulma version         Print the version
```

| Option | Meaning |
|---|---|
| `--dry-run` | Print every action and write nothing |
| `--yes`, `-y` | Skip confirmations |
| `--only <agents>` | Only these agents: `claude`, `grok`, `cursor`, `codex`, comma-separated |
| `--all` | Every agent, even ones not installed |
| `--no-path` | Do not add `bulma` to `PATH` in `~/.zshrc` or `~/.bashrc` |

The terminal `bulma report` and the agent `/bulma report` are two commands.
The terminal one measures time. The agent one measures Jev.

## Files Bulma writes

Bulma never writes run state inside your repo. Everything lives under
`~/.bulma/`:

```text
~/.bulma/memory.md                       # your preferences, for every repo
~/.bulma/bulma.json                      # settings
~/.bulma/bulma-watch.json                # pull requests watch saw merged or closed
~/.bulma/insights/observations.jsonl     # summaries of human review comments
~/.bulma/<slug>/memory.md                # preferences for one repo
~/.bulma/<slug>/.bulma-bus/
                  STACK.md               # which stage is active
                  ENVELOPE.md            # the message between stages
                  JOBS.md                # workers and the QA slot
                  RUN_LOG.tsv            # steps, timing, and loops
~/.bulma/<slug>/.bulma-core/             # routing, the Jev decision log
~/.bulma/<slug>/.bulma-developer/        # one folder per stage
```

`<slug>` is the repo's full path with each `/` replaced by `-`. For example,
`/Users/ana/code/app` becomes `Users-ana-code-app`.
[DISK.md](../skills/bulma-bus/DISK.md) has the full layout.

Browser logins for QA are saved in
`~/.bulma/agent-browser/bulma-<owner>-<repo>/` and reused until they expire.

QA runs agent-browser with `~/.bulma/agent-browser/config.json`, which sets
`{"headed": false}`. Bulma rewrites this file at the start of each QA session.
While it is in use, agent-browser ignores `~/.agent-browser/config.json` and
any `agent-browser.json` in your repo.
