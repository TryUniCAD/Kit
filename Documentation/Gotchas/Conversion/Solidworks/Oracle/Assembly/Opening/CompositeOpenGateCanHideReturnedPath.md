# A composite open gate can hide the actual returned path

Expected: a message saying that native load failed, warned or selected another file identifies the failing condition and records the returned file identity.

Actual: both generated concentric opens returned a nonnull document with error 0 and warning 32. The chained zero-warning predicate failed before `GetPathName` or file-identity comparison ran. The message therefore did not prove a path mismatch. The outer recorder also represented a `WindowsPath` argument by its type instead of its text.

Record the explicit requested path, type, options and configuration, separate returned errors and warnings, and actual returned document path/type before combining the checks. Retain the original zero-warning failure. A separate read-only diagnostic may inspect the known regeneration warning and rebuild state, while keeping acceptance false and every immutable input unchanged.

[Exact native failure and follow-up](../../../../../../../re/solidworks/records/GeneratedConcentricOpenFailure2026.md)
