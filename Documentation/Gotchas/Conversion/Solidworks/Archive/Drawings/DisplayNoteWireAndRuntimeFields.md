# Display-note wire fields differ from runtime storage

The note object stores several justification fields as native integers, a vector through a runtime pointer, and a 64-bit bitset. Those C++ shapes do not describe their wire framing: the justification words are `u16`, the vector is three embedded doubles without a presence flag, and the bitset is a signed count followed by ordered `u32` chunks. Current store writes count two. The string maps are typed object tags with schema zero, not inline presence-governed maps.

Native load also replaces/normalizes some vectors, doubles, justifications and text flags. Preserve their actual wire values separately. Do not serialize a normalized runtime view and call the resulting data lossless, or copy a saved state into a new constructor.

A note inside the ordinary view inherits archive condition `0x40`. Restricting every note to condition zero rejects valid framing before its first field. Admit only the independently proved zero/`0x40` profile, retaining the special context guards. Actual concrete note-data `+0x4b8/+0x4c0` dispatch must also be bound; a base layout name does not prove the concrete vtable entry.

The [complete source record and preserved partial observations](../../../../../../re/solidworks/records/DrawingDisplayNoteGrammar2026.md) bind the current build and next wrapper boundary. The attached note's COM annotation coordinates remain a distinct owner from these wire points.
