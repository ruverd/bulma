# Feature

Follow the existing route and decision policy. The `acceptance` proof names the
observable contract and records consequential decisions once. Reuse the existing
spec or ticket; do not create another design document for this checklist.

The `behavior-proof` records execution against every claimed acceptance criterion
and the relevant failure paths. Use the real artifact and matching surface.
For a behavior-changing feature, identify one consequential failure on the
changed path (for example, exhausted retries) and its expected observable
outcome before implementing that slice. Add or extend a test through the
existing test seam and record the scenario, test name and RED→GREEN receipts
in the behavior proof. If no consequential failure applies, record why.

When the failure affects a person, define what they see and can do next in
the existing acceptance criteria. For UI, specify the message, where and
when it appears, the state to preserve, and the recovery action when one is
available. Keep user-facing copy brief and specific: explain what happened
and give an actionable next step when one exists. Keep internal details in
diagnostics. For API changes, specify the status and stable error contract
the caller uses to distinguish the failure and choose the right response.
Trace that contract to the user-facing behavior when a UI consumes it. For
background work, specify how the person learns the outcome if it matters
to them. Use the existing UI and API error conventions.

Use `alternatives` only for an unresolved consequential design choice. An existing
pattern or a settled contract warrants `skip` with that reason. A throwaway
prototype may answer an empirical question in an isolated scratch directory.
Product preference still comes from the user under the decision policy. Do not
make an arena, a prototype or another interview mandatory for routine work.
