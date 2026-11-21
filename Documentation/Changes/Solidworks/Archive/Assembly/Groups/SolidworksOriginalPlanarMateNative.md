# Verify original SOLIDWORKS planar mate groups

Both pre-writer locked assemblies pass the internal SDK comparison for a
coincident or parallel mate paired with a positive driving distance. The
generated assemblies retain two or three rigid occurrences of one fully
dimensioned child, the original ordered trees, and each mate's actual datum
owners.

The pinned SOLIDWORKS 2026 SP05.2 oracle passed 992 numerical checks across
ten fresh processes with healthy controls. Both generated distance edits
survived child-first save and fresh reopen. The public SDK reads all four
endpoints and three child driving lengths per case before and after save.
All 26 scoped saved stream round trips are byte-identical.

Use the frozen method's guest `prepare` and `measure` subcommands with
the exact slot and packet hash for these original cases. The public assembly
writer remains disabled. The two source cases are native SOLIDWORKS assemblies
and add no qualified FCStd corpus conversions.

[Native lifecycle, scope and reproduction links](../../../../../../re/solidworks/records/SdkOriginalPlanarMateNative2026.md)

[Sanitized hash-bound measurement](../../../../../../re/solidworks/measurements/2026/SdkOriginalPlanarMateNative01.json)
