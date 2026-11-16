# Linked map views retain entry identity

## Expectation

A configuration snapshot and its resolved stream expose the same inherited map entries.
Equal class names and unchanged object payloads are sufficient for a compatibility view.

## Actual behavior

The typed map retained the payload objects, and the archive byte comparisons passed.
Its first research bridge created fresh legacy entry tuples on each lookup.
The resolved loader also converted the typed snapshot through those legacy rows.
The linked field-inventory process rejected the resulting entry identities under source `881911895`.
Matching bytes did not establish a correct retained graph.

## Workaround

Seed the resolved stream directly from its typed configuration snapshot.
Memoize compatibility rows by immutable `MapEntry` identity, retaining the entry alongside its row.
Share that view cache across linked streams while keeping map membership and counters independently owned.
Distinct new entries with the same slot number receive different cache keys.

The existing linked-inventory assertion continues to require the same target identity for every inherited entry.
No assertion or admission gate is relaxed.
Source and AST inspection passed without local codec or test execution.
Fresh remote verification remains pending.
