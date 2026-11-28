# Local body definitions can link outside the transmit

## Expectation

Every nonnull pointer in a local Parasolid body transmit resolves to a node in
that transmit.

## Observed behavior

One disclosed current-schema SOLIDWORKS 2026 imported solid has 172 resident
nodes reachable from its BODY. All twelve `ATTRIB_DEF.next` pointers target
nonresident indices. The definition identifiers, attribute owners, value
slots and type-list members resolve locally.

## Workaround

Use the local BODY boundary for the typed audit. Preserve the nonresident
definition links when comparing this disclosed native save in memory. Require
a proven receive and allocation rule before creating such links in a new
payload. The ordinary WORLD and rollback validator applies to its partition
context.

[Local BODY investigation](../../../../../../re/solidworks/records/ImportedLocalBodyKernel2026.md) · [Offline measurement](../../../../../../re/solidworks/measurements/2026/ImportedLocalBodyKernel01.json)
