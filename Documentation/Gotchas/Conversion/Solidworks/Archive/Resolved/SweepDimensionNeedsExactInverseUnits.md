# Sweep driver millimetres must invert the writer's scale

The measured cold SweepArcNear Section driver stores `0.008642` metres in
`moLengthParameter_c.f58`. The portable projection multiplies it by 1000,
which produces `8.642000000000001` millimetres. The existing sweep writer
divides by 1000. That pair of operations recovers the original stored double.

Dividing the metre value by `0.001` instead would display `8.642` here.
Dividing that result by 1000 gives `0.008641999999999999` metres and changes
the measured archive. Keep the exact typed driver with the geometry and verify
the complete regeneration after neutral JSON serialization.
[Archive and driver evidence](../../../../../../re/solidworks/records/SdkColdSweepReadback2026.md)
