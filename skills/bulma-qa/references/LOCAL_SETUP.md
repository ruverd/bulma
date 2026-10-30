# Local QA data and auth setup

Prepare the product states needed by PLAN.md before declaring missing fixtures
or auth a blocker. This applies to ordinary QA and LSTM human-signoff requests.
Use the repo's setup docs, seed scripts, migrations, auth helpers and dev config;
discover actual schemas and provider settings rather than inventing commands.

## Scope and preparation

1. Resolve the app origin, database connection and auth issuer independently.
   A localhost app can still use a shared database or remote identity provider.
   Verify each mutation target is an isolated local/dev QA resource before writing.
   If its scope cannot be established, record the blocker. This contract grants
   setup of local QA resources, not changes to production or shared auth policy.
2. Derive needed states from ACs and requests: eligible and ineligible users,
   roles, tenant/org membership, flags, record ownership and lifecycle state.
   Use dedicated QA accounts and synthetic records. Prefer documented seed or
   admin helpers; targeted SQL is allowed after inspecting schema and constraints.
3. For the local identity provider discovered in the repo, configure the QA user's
   verification/activation state, org/project grants, role assignments, required
   claims and documented dev client settings as the scenario needs. Check both
   identity-provider assignments and application DB membership. Use existing
   local admin credentials through documented tooling. Do not expose secrets.
4. Keep changes minimal, repeatable and reversible. Record prior values, resource
   IDs, setup commands without secrets, and cleanup steps in a private setup log
   under `.bulma-qa/`, rooted at `$BULMA_ROOT`. Never reset an entire database or
   grant every role to make a walk pass. Separate allowed-role and denied-role
   identities; least-privilege failures are part of the proof.
5. Refresh the session/token after role or claim changes and confirm the active
   user, tenant and effective permissions. Then exercise the real application
   through its normal UI or endpoints. Seeds create preconditions; they never
   replace the action or manufacture its result. Preserve validation, tenant
   checks and authorization controls under test.

## Evidence and cleanup

Record sanitized setup and active scenario identity in PLAN.md. Keep tokens,
passwords, connection strings, personal data and private setup logs out of PR
comments, screenshots and clips. Publish only safe setup summaries.

Map each fixture to the steps it enables. After execution, restore changed
settings and remove disposable records/accounts when no longer needed. Preserve
dedicated reusable QA fixtures only when repo convention calls for them. Record
cleanup done or pending before handing back results; report cleanup failures.

Missing seed scripts alone is not a coverage exemption. Inspect the documented
local database/auth administration path and prepare the required state when
possible. Missing authority, credentials or an isolated environment is BLOCKED
for the affected requested case, with the exact prerequisite. Never weaken a
shared provider or application security to obtain a green screenshot.
