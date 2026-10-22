# Third-party skills bundled in `skills/`

These files are copied into this repo so a clone runs without extra
marketplaces. Original licenses apply to those copies. Graph and engine
files remain MIT
© Ruver Dornelas.

| Origin | License | Copied skills |
|---|---|---|
| [mattpocock/skills](https://github.com/mattpocock/skills) | MIT © Matt Pocock | `grill-with-docs`, `diagnose`, `to-prd`, `to-issues` |
| [pstack](https://github.com/poteto/pstack) (Lauren Tan) | MIT © Lauren Tan | `unslop`, `how`, `tdd`, `blast-radius`, `architect`, `figure-it-out`, `interrogate`, `typescript-best-practices`, `no-comments`, `technical-writing`, `principle-fix-root-causes`, `principle-prove-it-works`, `principle-sequence-verifiable-units` |
| [superpowers](https://github.com/obra/superpowers) (Jesse Vincent) | MIT © Jesse Vincent | `receiving-code-review` |
| Cursor team kit | as shipped in the original skill | `thermo-nuclear-code-quality-review` |

The delivery graph **adapts** grill (ASK last resort, DECIDE internally).
Vanilla `grill-with-docs` interview-and-wait is off. See
[`GRILL.md`](skills/bulma-feature-delivery/GRILL.md).
TDD iron law in [`TDD.md`](skills/bulma-feature-delivery/TDD.md)
wins over any skip in bundled `tdd`.

Task playbook contracts and the project verification recipe adapt ideas from
[pstack 0.15.30](https://github.com/cursor/plugins/tree/4ec7ffa173eaa70d3d9467a627baf0954645a353/pstack),
MIT © Lauren Tan. Bulma retains its own graph edges, host adapters and proof helpers.
