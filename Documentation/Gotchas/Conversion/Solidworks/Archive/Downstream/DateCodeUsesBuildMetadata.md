# Date code uses build metadata

## Expectation

The downstream constructor's `su_getFullDateCode()` result is a current wall-clock date or can be replaced by an authored archive epoch.

## Actual behavior

The pinned 2026 producer obtains a cached tagged value. On a cache miss it constructs a string from embedded build metadata, trims trailing whitespace, discards the first 14 characters through the actual right-substring operation and parses the remaining decimal text. The full-code utility then applies its historical short-code expansion only for values in `1..99999`.

For this exact original build the computed cache-miss tagged/full value is `2026306`, already outside that expansion range. It is not a value captured from a saved model or a live-clock measurement. Actual warm-cache state and other releases are outside that constant's scope.

## Workaround

Keep build provenance, authored chronology and volatile archive clocks as distinct owners. Preserve a source archive's actual `f10` and history instead of replacing them with the target constructor result. Derive a release-specific producer only from its pinned implementation, and do not make a general native-save provenance claim from this note.

The [exact native record](../../../../../../re/solidworks/records/DownstreamDateAndEnable2026.md) supplies complete bounds, framework operation evidence and remaining limits. No new constructor default or writer policy is introduced.
