# TDD

Bundled `tdd` + this iron law. **No production code before a failing test** on a **confirmed seam**.

Bundled `tdd` may say "skip when the path is expensive". **Ignore that skip** on a behavior change. Write the failing test or upgrade the path (DECIDE). Do not ASK to skip TDD.

## Iron law

```
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
```

Production code before the failing test → delete it and start over. Do not "adapt" it. Do not "use it as reference".

## Seams

A seam is the public boundary you observe. Use case, HTTP route, hook, screen behavior. Not a private helper.

Before the first test of a ticket, pick the seam from the table (DECIDE, log). If two seams could work, pick the outer public one. Do not ASK.

Default seam: the **same layout as the nearest neighbor test** in this repo
(DECIDE, log). If two seams could work, pick the outer public one.

| Change | If the repo already does this |
|---|---|
| API / use case | co-located unit test |
| HTTP contract | controller or request test + the repo's schema style |
| Persistence | repository test |
| UI behavior | co-located component test |
| Bug | failing test that reproduces the bug |

Match the neighbor test's naming and runner (`test_cmd` in STATE). Tests live next to the code when the repo already does that.

## Loop

1. RED. Write the test. Run it. Watch it fail for the right reason.
2. GREEN. Minimum code to pass.
3. Re-run that test. Then the local file.
4. Next slice. Refactor after review, not inside the red-green loop.

## Anti-patterns

- Tests that mirror implementation
- Tautological expects
- All tests first, then all code (horizontal slice)
- Mocking the thing under test
- Skipping RED because "it is simple"
- "I will test later" / "I already tested by hand"

## Evidence

Coder returns:

```text
tdd_behaviors: N
red: <command> → fail <name>
green: <command> → pass
files_changed: [...]
```

Parent writes `## TDD evidence` in STATE. Reviewer **fails** the ticket if evidence is missing. Prose does not replace the exit code in `.bulma-feature-delivery/gates.log`.

## What may skip TDD

Only with an explicit log in Decisions, and only:

- Throwaway prototype (grill)
- Generated config
- Pure CSS with no behavior

## E2E

Only if done criteria needs an end-to-end UI flow. Use `e2e_cmd` from
STATE (the app's suite, CI). Unit/integration first. E2E does not
replace TDD of logic. `/qa` is agent-browser, not this suite.
