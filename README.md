# Bulma

Bulma is a software factory for coding agents. You give it a ticket, and it
takes the work from plan to a tested pull request, then waits for you to merge.

It runs inside the coding agent you already use: Claude Code, Codex, Cursor, or
Grok. You type one command, `/bulma`, and it decides which step comes next.

```text
/bulma                    # what should happen next, across every repo
/bulma ABC-123            # deliver a ticket
/bulma https://github.com/org/repo/pull/99
/bulma watch              # what is stuck, and the command that unsticks it
/bulma lookback           # what human reviewers keep catching that Bulma missed
```

## What Bulma promises

- **You merge. Bulma never does.** Every pull request stays a draft until
  its checks pass, it has no merge conflicts, and QA has attached proof that it
  works.
- **Code is written test-first.** A fresh worker agent writes a failing test,
  then the code that makes it pass, one ticket at a time.
- **Every change is tested like a user would test it.** QA clicks through the
  app in a real browser and posts a video on the pull request. For an API
  change, it posts the HTTP requests and responses instead.
- **It stops and asks when it cannot see something.** If a ticket link does not
  open, Bulma stops. It does not invent the ticket.

These rules are instructions to an AI model, not enforced permissions. Your
agent's own permission settings are the real boundary. Read
[SECURITY.md](SECURITY.md) before you point Bulma at a repository you care about.

## What happens when you type `/bulma ABC-123`

1. **Plan.** Bulma reads the ticket and asks you only the questions it cannot
   answer from the code and docs. It writes a short spec and splits the work
   into small tickets.
2. **Build.** A worker agent does each ticket test-first. Bulma checks the result
   against the spec and runs your tests, linter, and type checker.
3. **Ship.** Bulma opens a draft pull request and waits for CI. If CI fails,
   it fixes the cause and pushes again.
4. **QA.** Bulma tests the change the way a user would, happy path and broken
   input, and comments on the pull request with the evidence.
5. **Fix or finish.** If QA finds a bug that this pull request caused, Bulma fixes
   it on the same branch and runs QA again. When QA passes, the pull request is
   ready for you.

Bulma also handles review. `/bulma <someone else's PR>` reviews it. To answer
the review comments on your own pull request, run `/lstm <PR link>`. Bulma
checks each comment, fixes the ones that are right on the same branch, and
replies to every comment.

## Quick start

You need:

- macOS, Linux, or WSL on Windows
- `git`, `curl`, and `python3` 3.9 or newer
- [GitHub CLI](https://cli.github.com/) (`gh`) 2.99 or newer, signed in. Use
  `glab` for GitLab.
- A coding agent: Claude Code, Codex, Cursor, or Grok
- A TypeSafe API key for `/bulma` itself. Create one at
  [console.typesafe.ai](https://console.typesafe.ai).

**1. Install Bulma.**

```bash
curl -fsSL https://raw.githubusercontent.com/ruverd/bulma/main/install.sh | bash
```

The installer clones Bulma, adds its skills to every coding agent it finds, and
puts the `bulma` command on your `PATH`. It also installs
[agent-browser](https://agent-browser.dev/) and Chrome for browser QA.

To read the installer before it changes anything, clone the repo and run
`./install.sh setup --dry-run`. It prints every action and writes nothing.

**2. Add your API key** to your shell profile, for example `~/.zshrc`:

```bash
export TYPESAFE_API_KEY="..."
```

**3. Restart your coding agent**, then check the setup:

```text
/bulma doctor
```

**4. Start in shadow mode.** Shadow mode lets you watch Bulma's choices before
you trust them:

```text
/bulma power shadow
/bulma
```

The [getting started guide](docs/getting-started.md) walks through a first
ticket step by step.

## Commands for each coding agent

| Agent | Type this | Notes |
|---|---|---|
| Claude Code | `/bulma` | Short aliases also work: `/developer`, `/qa`, `/reviewer`, `/lstm`, `/goal`, `/memory` |
| Grok | `/bulma` | Same short aliases as Claude Code |
| Cursor | `/bulma` | Use the full names: `/bulma-developer`, `/bulma-qa` |
| Codex | `$bulma` | Codex rejects custom `/` commands. Use `$bulma-developer`, or pick a skill from `/skills` |

This README writes commands the Claude Code way. In Codex, replace the leading
`/` with `$`.

## Everyday commands

| You type | What Bulma does |
|---|---|
| `/bulma` | Looks at your open pull requests and unfinished runs, then starts the most useful next item or asks you to pick from the top three |
| `/bulma ABC-123` | Delivers the ticket. Any tracker works, if your agent can open the link |
| `/bulma <PR link>` | Your pull request: runs QA. Someone else's: reviews it |
| `/bulma <plain text>` | Works out which step fits the request, or answers in chat |
| `/bulma resume` | Continues a run that stopped for a question |
| `/bulma watch` | Lists runs that need you, runs that stalled, and the command to continue each one |
| `/bulma lookback` | Shows the problems human reviewers keep catching that Bulma missed |
| `/bulma report` | Shows how often Bulma's automatic choices matched the built-in rules |
| `/bulma power <level>` | Sets how much Bulma decides on its own: `shadow`, `cautious`, `balanced`, or `bold` |
| `/memory <note>` | Saves a preference, for example your chat language or the reviewers for this repo |

`watch`, `lookback`, `report`, `power`, and `doctor` work without an API key.
To run one step without the router or a key, call it directly: `/developer`,
`/qa`, `/reviewer`, `/lstm`, or `/bulma-triage`. The
[command reference](docs/commands/README.md) has a page for each.

In your terminal, the `bulma` command manages the install:

```bash
bulma update      # pull the latest version and relink the skills
bulma status      # show the install and any run in the current repo
bulma report      # show time spent per step and token use
bulma uninstall   # remove Bulma's links
```

## Documentation

| If you want to | Read |
|---|---|
| Deliver your first ticket | [Getting started](docs/getting-started.md) |
| Understand how the pieces fit | [How Bulma works](docs/how-it-works.md) |
| Change settings, or find a file | [Configuration](docs/configuration.md) |
| Fix a problem | [Troubleshooting](docs/troubleshooting.md) |
| Look up a term | [Glossary](docs/glossary.md) |
| Look up one command | [Commands](docs/commands/README.md) |
| Change Bulma itself | [CONTRIBUTING.md](CONTRIBUTING.md) |

All pages are listed in the [documentation index](docs/README.md).

## Install as a plugin instead

Claude Code and Grok can also install Bulma as a plugin. The plugin updates
through your agent, but it does not add the short aliases or the `bulma`
terminal command. Pick one method per agent. `bulma status` warns you if both
are installed.

```bash
# Claude Code
claude plugin marketplace add ruverd/bulma
claude plugin install bulma@bulma

# Grok
grok plugin marketplace add ruverd/bulma
grok plugin install bulma --trust
```

Inside a Claude Code session, the same two steps are
`/plugin marketplace add ruverd/bulma` and then `/plugin install bulma@bulma`.

## Credits and license

Bulma includes copies of skills from
[mattpocock/skills](https://github.com/mattpocock/skills),
[pstack](https://github.com/poteto/pstack),
[superpowers](https://github.com/obra/superpowers), and the Cursor team kit,
so one clone is enough. The before and after screenshot flow follows
[vercel-labs/before-and-after](https://github.com/vercel-labs/before-and-after).
[THIRD_PARTY.md](THIRD_PARTY.md) lists every copied skill and its license.

MIT. See [LICENSE](LICENSE). Copied third-party skills keep their original
licenses.
