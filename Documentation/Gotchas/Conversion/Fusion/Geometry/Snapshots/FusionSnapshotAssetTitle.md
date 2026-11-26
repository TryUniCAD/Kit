# Saved snapshot projection uses the asset title property

The original constructor writes its title to the Design component and ACT assembly state. Its strict version-1 reader uses that authored title. Adding a generated snapshot selects the saved version-2 reader, which uses the asset's `documentName` property for the neutral configuration title. The generated snapshot archive initially passed complete native-state readback but projected a blank configuration title.

Write the authored title as `documentName` on the generated snapshot's asset. Keep the existing Design and ACT title bindings. Verify the public configuration title independently of native-state equality. The snapshot-free writer retains its existing default properties. See the [independent snapshot generator](../../../../../Changes/Research/Encoder/FusionGeneratedCuboidSnapshot.md).
