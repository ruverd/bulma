# UI → design system + repo patterns

When the work is **UI**, follow the design system and the **real implementation
patterns** in the repo. Inventing a style or "a dialog from scratch" without
looking at recent examples is a process bug.

**Figma is not required.** Many tasks have no Figma. Then the gold standard is
**copy how recent same-type features/components were built**.

## How to know it is UI

Signals (any of these):

- Goal/ticket: page, screen, button, form, **dialog/modal**, drawer, table UI, empty state, typography
- Diff in presentation `*.tsx` / `shared/ui` / `shared/components` / Storybook

API/hook/service only, no UI → this doc does not apply.

## Source of truth (order)

| Priority | Source | When |
|---|---|---|
| 1 | **Figma** (`figma-context.md` via MCP) | Only if the ticket/goal has a Figma link |
| 2 | **Design system / repo primitives** | Always (Button, Dialog, Input, tokens, `cn()`…) |
| 3 | **Recent same-type examples** | **Always if there is no Figma**; also with Figma to map composition |
| 4 | **Neighbor feature in the domain** | Same product module/area |
| 5 | CLAUDE.md / AGENTS.md / Storybook | Rules and catalog |

Missing Figma ≠ visual creativity is allowed.
Missing Figma → **required** to find and follow code references.

**Authority split (deterministic, no ASK):**
Figma owns **structure, copy, and states**; the DS owns **values** — Figma spacing/hex
that does not match a token 1:1 → **snap to the nearest token**, do not ask.
**ASK** only when Figma requires a **component/behavior the DS does not have**
(e.g. a missing date-range picker; a layout no primitive can compose) —
that is a material conflict; a 2px / color-tone gap is not.

## No Figma: pattern discovery (required)

Before implementing UI, **spec/tickets and the coder** must find **recent examples** of the same UI type.

### 1. Name the UI type

E.g. `Dialog` / `Modal`, `Drawer`/`Sheet`, `Form page`, `Table+filters`, `Empty state`, `Card grid`, `Tabs`, `Toast/banner`.

### 2. Search the repo (2–5 references)

Prefer the **newest** and the **same domain**:

```bash
# search examples (adapt to the repo)
rg -l "Dialog|Modal" --glob "*.tsx" src/
rg -l "AlertDialog|Sheet" --glob "*.tsx" src/
# git by mtime / recent commits if useful
git log --oneline --diff-filter=A -- "*.tsx" | head
```

Typical folders (adapt to the repo):

- design system: `shared/ui`, `components`, `ui/`
- feature screens: `src/App/<Domain>/`, `app/`, `pages/`, `views/`
- Storybook next to the component if the repo uses it

### 3. Read the pattern (not just the path)

From each reference, note in STATE / spec:

- Primitives used (e.g. `Dialog`, `DialogContent`, `Button`)
- Folder structure (`ComponentName/ComponentName.tsx` + `index.ts`)
- Props / compose pattern
- Loading / empty / error
- `cn()` / tokens
- Co-located RTL tests if they exist

### 4. Implement **like** the reference

- Same component family
- Same file organization
- Same states
- Minimal style diff vs the example

Record in STATE (spec/coder):

```markdown
## UI references (no Figma, or complement)
- type: Dialog
- refs:
  - <dialog from this repo>
  - <same-type screen from this repo>
- extracted pattern: uses shared/ui Dialog + ...
```

**Without at least 1 concrete reference on a UI task with no Figma** → spec/coder invalid (`NEEDS_CONTEXT` or review fail).

## With Figma

1. Load via MCP → `figma-context.md`.
2. **Map** frames to DS primitives + composition like recent features.
3. Do not copy raw Figma HTML/CSS; compose with the DS.
4. If Figma MCP is **critical** (link on the ticket) and fails → MCP error (gate), do not invent layout.

## Hard rules (UI)

| # | Rule |
|---|---|
| 1 | **Reuse** DS/primitives. Forbidden to recreate Button/Input/Dialog if they exist. |
| 2 | **Tokens** via theme/`cn()` — no magic hex/spacing. |
| 3 | **No one-off CSS** if the DS covers it. |
| 4 | **States** loading/empty/error/disabled like recent refs. |
| 5 | **A11y** of the repo primitives (Radix etc.). |
| 6 | **Icons** from the project set. |
| 7 | **Responsive** only like existing layouts. |
| 8 | **Copy** from the ticket/Figma; structure from DS/refs. |
| 9 | **Storybook** if the local pattern requires it for a new component. |
| 10 | **YAGNI visual** — no "improving" outside Figma/refs. |
| 11 | **No Figma → recent refs required** (same UI type). |

## Find the DS in this repo

Look for `shared/ui`, `components.json`, Storybook, `src/components`.
Follow **that** tree. Do not force a folder layout from another product.

## What each node does

| Node | Duty |
|---|---|
| **mcp_context** | Figma **only if** there is a URL; no URL means Figma is not critical |
| **spec / tickets** | List DS + **recent refs** (paths) if UI |
| **coder** | Read the refs; implement in the same pattern; record refs used |
| **reviewer** | Fail if a primitive was reinvented **or** UI with no Figma and no evidence of a recent ref |

## Coder checklist (UI)

- [ ] Repo DS/primitives
- [ ] If Figma existed → aligned
- [ ] If **no** Figma → ≥1 recent same-type ref read and followed
- [ ] Loading/empty/error like the refs
- [ ] Tests in the local pattern

## Anti-patterns

- Invented dialog without opening the latest dialogs in the repo
- "No Figma so I designed it my way"
- Recreating Button/Modal
- Ignoring `figma-context.md` when it exists
- Copying Figma pixel-for-pixel without mapping to the DS
