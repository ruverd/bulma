# Maintenance

Preserve the current light-change routing. The `scope` proof names the bounded
change and whether any observable behavior changes. The `verification` proof
records the relevant executed checks and their outcomes.

Do not add a test that mirrors a copy or configuration edit. If behavior changes,
the graph's TDD requirement applies. Structural work claiming unchanged behavior
uses Refactoring instead. Agent instruction changes use Skill change.
