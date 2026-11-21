# Fresh and native-saved thin end thickness differ

On SOLIDWORKS 2026 SP05.2 the `moThinSpec_c` constructor stores `-2.0` into the inactive end-thickness field `f30` at `sldmodu.dll` address `0x4c6eef29`. The exported setter at `0x4b34fc90` is a direct assignment and the modern serializer writes the retained value. Each disclosed native thin boss saves `1e-7` even though cap ends are disabled. The producer of that later value is unresolved.

Use the explicit initializer for the bounded cold trial and measure the actual rebuild and later save. Keep the live wall drivers on `f08` and `f10`. The end-thickness scalar does not stand in for either wall value.

[Pinned build and source evidence](../../../../../../re/solidworks/records/ThinRevolveWireOwners2026.md).
