# Native thin-revolve edits can add a radius display

The four disclosed SOLIDWORKS 2026 SP05.2 thin boss sources save `moThinSpec_c.f48` as null. After editing the active angle and wall drivers, their native saves allocate an `f48` radial display. Its local `ThreeDRadiusDim_c` and zero `D7` length are absent from the native editable driver inventory. The thin-spec add-bends switch stays zero.

Keep the radial branch when decoding an edited save. Identify editable angle and wall ownership from the actual end specification and thin specification references, with the native feature's active wall mode. The classname `moRevolvedRadiusDim_c` belongs to a different archive owner and did not occur in this branch.

[Hash-bound source and re-emission evidence](../../../../../../re/solidworks/records/ThinRevolveWireOwners2026.md).
