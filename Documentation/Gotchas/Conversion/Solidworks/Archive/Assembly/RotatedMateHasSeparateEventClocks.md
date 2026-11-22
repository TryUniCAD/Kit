# Mate creation and file save clocks have different owners

The disclosed rotated assembly was authored with a different save event for
its child and a separate creation event for each mate. The root model
creation epoch supplies neither the child file time nor the mate FILETIME
and revision log fields. The current standalone assembler intentionally
uses one event for its source-free profile.

When comparing an older authored packet, use the supplied per-owner events
in their corresponding constructors and include both complete hashes in the
proof. Preserve the historical optional list, directory and keyword policy
as part of the comparison. A geometry match alone cannot identify the
historical files. [Exact evidence](../../../../../../re/solidworks/records/RotatedMateAssemblyBoundary2026.md)
