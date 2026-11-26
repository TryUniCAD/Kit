# Feature ladder counts depend on archive owners

## Expectation

A feature count found at a fixed stream offset applies to every document of the same format version.

## Observed behavior

The SOLIDWORKS 2026 part ladder stores the CMgr `fb00` row count at byte 1610.
In the P04 part, the same field is at byte 1662.
Byte 1610 in P04 holds a different field.

The ResolvedFeatures history folder has twice the boss count in the part ladder.
The P04 part has one boss and an empty history folder.
The A0 assembly has one history item.

## Workaround

Walk the typed configuration graph to find `moBaseConfiguration_c.fb00`.
Use the actual row count for its `u32` prefix.
Use the vendor archive count for the actual `moHistoryFolder_c.f3c8` items.

[Archive compatibility](../../../../../../re/solidworks/records/Solidworks2026ArchiveCompatibility.md) · [Count-owner receipt](../../../../../../re/solidworks/measurements/2026/ReverificationCountOwners01.json)
