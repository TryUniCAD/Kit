# Fresh chamfer saved options use a present empty array

The ordinary chamfer archive retains its `f8c8` array even when a first successful operation has produced no saved options. The exact SOLIDWORKS 2026 SP05.2 kernel selects current context-derived options at count zero and records six words only after the operation succeeds. Already populated options follow a different override path.

Use the present empty typed array when constructing a fresh chamfer. Keep the typed shape, mode and selected owner intact. Source-save words belong to that earlier native calculation. [Exact build and array evidence](../../../../../../re/solidworks/records/ChamferColdOwners2026.md#saved-options-array-starts-empty)
