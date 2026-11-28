# Aggregate usage is not an individual phase snapshot

## Expectation

A file-level `schema_usage.load` or `.store` object has the same keys as an
individual stream load/store snapshot, including `completed`.

## Actual behavior

`RoundTrip.usage_summary` unions schema names and sums raw-operation counts across
selected streams and explicit dependencies. It emits four summary keys and does
not emit phase identity or completion. Individual phase snapshots record their
own direction, role, source stream, completion and operation details.

The first fully admitted curve source commands exposed a checker that sent an
aggregate to `AssertSnapshot`, producing `KeyError: completed`. Earlier strict
schema failures had stopped the process assertion before this consumer ran.

## Workaround

Check aggregate unions and counts against the actual constituent snapshots.
Require completion and empty provisional/missing inventories on every phase.
Keep linked-dependency load usage in the aggregate load direction and preserve
its independent source hash, tail and map assertions. An aggregate cannot replace
phase evidence, and a new summary key should not be invented to satisfy a checker.

The [process repair](../../../../Changes/Solidworks/Model/SolidworksArchiveUsageSummaryVerification.md)
keeps the codec and strict gates unchanged. Source admission remains separate
from field classification and native writer acceptance.
