# Explicit display inputs for a signed angle-distance chamfer

The internal SOLIDWORKS 2026 chamfer composer accepts a
`ChmfViewInput` on its typed `ChmfPlan`. Supply the ordered annotation
catalog, the name of the shared driver view, the D1 text station and signed
clearance, the local D2 text point, the witness length, design intent and
both leader values. These are independent of the actual D1 distance and
D2 angle. The catalog and live driver chains receive their identities
from the generated graph.

The view can align with both oriented stock axes or reverse both together.
The D2 text point must lie on one of the two proven exterior branches.
An absent input keeps the measured default presentation. Public writing
continues to require the exact measured archive and its original save event.
The new composer covers a portion of the saved source display state.
Intact saved-source transfer still requires the original stock scope and
warm result and rollback lifecycle.

Four disclosed native sources and eight guarded model processes verify
the bound views, driver and edge roles and witness values. Each guarded
process makes zero external accesses. The source workers preserve the
original active partition and both live parameters. No new native
qualification was performed.

- [Source and construction evidence](../../../../../re/solidworks/records/ChamferSavedDisplays2026.md)
- [Public adapter guide](../../../../Reference/Adapters/Solidworks.md#writing-one-angle-distance-edge-chamfer)
- [Angular text station gotcha](../../../../Gotchas/Conversion/Solidworks/Archive/Dimensions/ChamferAngleStationFollowsBothWitnesses.md)
