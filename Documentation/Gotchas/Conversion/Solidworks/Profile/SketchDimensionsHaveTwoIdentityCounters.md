# Sketch dimensions have two identity counters

A driving sketch dimension has a value record and one or more display annotations. The value record uses the shared model persistent ID in `f50`. The local display handle connects the owning sketch to the value-array index in `ff8`. The display itself has an independent ID in `f58`, allocated from the model's next display ID at `fd44`.

Reusing the value ID for the display can collide with other model annotations. Allocate the value from the existing persistent ID allocator, then reserve a display ID from the actual model counter when inserting the display into the sketch list. The 2026 `sgSketch::addDisplayDim` path at `0x4c49b230) and the guarded rectangle integration are both recorded in the construction ledger. [Native rule and process verification](../../../../../re/solidworks/records/RectangleDimensions2026.md)
