## What changed

<!-- One or two sentences. Name the mechanism, not the feeling. -->

## Why

<!-- The problem this solves. Link the issue if there is one. -->

## Checks

- [ ] `bash tests/install.sh`
- [ ] `bash tests/repo.sh`
- [ ] Ran `./install.sh setup` if I install by symlink

## If this touches a skill

- [ ] No link leaves the skill's own directory
- [ ] Host specifics live in `bulma-host`, not in the skill
- [ ] No model id, agent home path, or personal handle hardcoded
- [ ] Listed in `plugin.json` and `.claude-plugin/plugin.json` if new
