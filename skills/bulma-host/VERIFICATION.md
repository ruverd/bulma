# Project verification recipes

A recipe is maintained project knowledge about running and observing the real
product. The PR plan still derives coverage from its diff and acceptance criteria.
The recipe does not replace that plan or change who owns QA.

## Discover and use

Use the recipe named in project instructions or the `verification_recipe`
preference from bulma-memory. Otherwise inspect an existing project-local verify
skill or the documented development/test commands. Record the chosen path in
delivery STATE. Missing recipe does not block ordinary work or trigger generation.

Read only the launch/doctor instructions and feature entries relevant to the task.
Run doctor before driving and after a surprising failure. It checks actual build,
instance identity, readiness and auth; a bound port alone is not readiness.
Use agent-browser for UI, the declared HTTP contract for services and deterministic
PTY input for a CLI. Prefer the project's existing driver. External QA remains
external; share the recipe or read its current verdict rather than start a second QA.

## Author when requested

Discover commands, fixtures, auth, stable selectors, expected side effects and
isolation from source. Use the [recipe template](templates/VERIFICATION.md) as a
starting shape, not a demand for unnecessary sections. Put project-specific
details in the target repo at its chosen documentation or project-skill location,
never in Bulma's generic skills. Record its discoverable path in repo instructions
or project memory. Keep secrets in the existing secret mechanism.

Each mapped feature names the user path, preconditions, input/actions, observable
pass condition and evidence. Include the side effect, not only a final screenshot.
Two instances must use separate ports, profiles and data, or one driver must own
the shared instance. Cleanup removes only processes and scratch data this run owns.
Proof survives cleanup outside the checkout under the run's `$BULMA_ROOT`.

Execute launch, doctor, one real mapped feature and cleanup before delivery.
Check evidence still exists afterward. A cold-start failure must be repaired in
the recipe or reported; never claim an unexecuted recipe works. No placeholders
in a delivered recipe. State any target environment not exercised.

## Maintain when requested

Scope edits to the recipe and its own helpers. Compare feature entries to current
source, identify added/removed entry points, then exercise each mapped feature.
Use the minimum number of isolated instances needed; do not fan out UI drivers
onto one window. Distinguish documentation drift, driver failure and product bugs.
Never weaken an expected result to turn a product regression into a passing map.
Repair a driver within scope, rerun the affected path, and retain the evidence.

Report `clean`, `changed` or `blocked`, feature coverage, actual evidence and any
unreachable prerequisite. Do not call missing coverage a pass or silently edit
product code. Formal models, if present, need a separate sync check against the
covered code and a counterexample replay; a green model alone is not live proof.
