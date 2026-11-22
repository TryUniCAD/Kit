# Assigned material follows the active solid shell

The disclosed saved parts have a top-level WORLD body at index 2 and a
different body owning the active shell at index 3. The latter owns the
`ATOM_ID_2001` attribute. Looking for the attribute on the WORLD's
first body would miss the actual assignment.

Follow the active shell and its faces to the physical solid. Join the
physical atom to the selected configuration's linked row and the
portable body's actual producing feature.

[Guarded assigned material evidence](../../../../../re/solidworks/records/SdkAssignedPartRead2026.md)
