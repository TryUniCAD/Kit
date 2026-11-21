# Sketch and profile runtime offsets

The sketch builder and profile builder both expose fields named after native offsets. Reusing an offset name does not identify the same runtime field or owner.

`sgSketch::update` at `sldmodu!0x4c549ab0` reads `+0x388` and `+0x3e0` from its actual `sgSketch` object. The sketch constructor at `0x4c495450` initializes both pointers to null, with stores at `0x4c495e8c` and `0x4c495ee9`. The separate `moProfileFeature_c` constructor at `0x4c0ca780` initializes its own `+0x3e0` as the integer `100000`. A hook that substitutes the profile pointer reads a different structure and cannot characterize the sketch's solver branch.

Record the runtime object role and base pointer beside every observed offset. Update's argument zero is the sketch. The solver-commit wrapper at `0x4c5195d0` instead stores that sketch pointer at wrapper `+8`. Sketch `+0x138` points to the profile; it is a separate observation base. Read sketch runtime `+0x388` and `+0x3e0` from the sketch, and label any profile fields separately.

The [construction ledger](../../../../../re/solidworks/records/ProfileConstruction2026.md#local-update-branch-and-stamp-boundary) records the binary identity, constructor stores and static branch proof. These facts classify observation locations; they do not establish successful generated-file loading.
