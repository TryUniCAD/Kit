# Equal solids can belong to different FreeCAD shape owners

A one-Pad body can carry separate `Body.Shape`, `Pad.Shape` and `Pad.AddSubShape` members. The three C130 members have different hashes and the same solid boundary. Moving one member to another role preserves a geometric comparison but changes its source owner. `Sketch.Shape` in the same file is a placed wire with its own lineage.

Validate each saved member against the exact original archive and its owning object and property before comparing its topology. Generate the target body from the editable sketch and Pad. Report source lineage separately until the target preserves the required identity and edit behavior.

[Source roles and wrong-member comparison](../../../../../re/solidworks/records/SdkC130SourceOwners2026.md)
