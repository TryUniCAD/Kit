# Read the concentric parameter count from the returned array

The registered SOLIDWORKS 2026 `IMateEntity2` type exposes a
zero-argument `GetEntityParamsSize` method. The first controlled
concentric call reaches that method through the generated COM binding
and returns a write-only-property exception. The same endpoint returns
an eight-value `EntityParams` array with the expected point, direction
and radius.

Validate the actual array length and all values. Keep the real selected
face, component identity and independent analytic geometry checks.
The corrected packet reuses the same sealed guest designs and passes
both controls for each of the five source cases.
[Measured source record](../../../../../../re/solidworks/measurements/2026/ConcentricMateSourceArchive01.json)
