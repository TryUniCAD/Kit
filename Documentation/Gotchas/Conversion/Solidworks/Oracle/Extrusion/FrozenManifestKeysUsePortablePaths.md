# Frozen manifest keys use portable paths

## Expectation

A relative file path appeared to be a stable dictionary key on macOS and Windows.

## Actual behavior

`str(Path.relative_to(...))` uses the host path separator.
The frozen manifest had POSIX keys, but Windows generated a backslash key.
The lookup failed before the native application started.
The partial record had no `result` member.
A summary that required that member failed again.

## Workaround

Serialize manifest keys with `as_posix()`.
Keep the declared key when selecting a manifest entry.
Use `Path` only to resolve the filesystem location.
Treat missing, partial and malformed phase records as incomplete evidence.
Record absent measurements as `not_run`.
Keep the original failed records and freeze a separate retry.

The [through-all retry record](../../../../../../re/solidworks/records/ThroughAllObserverPathRetry2026.md) binds the exact failure and process checks.
