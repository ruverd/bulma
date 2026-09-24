# Skills

One flat directory per skill, so `../other-skill/FILE.md` resolves the same in
git and after `bulma setup` flattens them into your agent homes. Nothing here
links outside this directory; `tests/repo.sh` enforces that.

`category` in each `SKILL.md` frontmatter says what a skill is:

| Category | Job |
|---|---|
| `graph` | Main-thread graph engineer. Ships GRAPH.md, STATE.schema.md, nodes/ |
| `engine` | Delivery and review engines a graph calls |
| `lib` | Bundled primitives (`unslop`, grill, tdd, the bus protocol, the host contract, `before-and-after`) |

Host contract: [bulma-host/SKILL.md](bulma-host/SKILL.md).
Bundled primitives and their licences: [../THIRD_PARTY.md](../THIRD_PARTY.md).
Repo index: [../README.md](../README.md).
