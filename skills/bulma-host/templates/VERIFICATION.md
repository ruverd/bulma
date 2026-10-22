# <Project> verification

## Launch and isolation

<Exact command, toolchain, fixtures, auth source, readiness signal and owned
ports/profiles/data. Name how a second instance stays isolated, or who serializes
driving. No secret values.>

## Doctor

<Read-only command proving this is the expected usable build and session.
Recovery after a surprising failure.>

## Feature map

| Feature | User entry and prerequisites | Actions | Observable pass condition | Evidence |
|---|---|---|---|---|
| <feature> | <actual route/command and fixture> | <stable driver actions> | <result and side effect> | <capture path> |

## Cleanup

<Stop only owned processes and disposable data. Keep proof outside the checkout.
Confirm it still exists after cleanup, including failed attempts.>

## Last verified

<Revision, environment, features exercised and commands run. Record missing
coverage as unknown and distinguish product bugs from recipe drift.>
