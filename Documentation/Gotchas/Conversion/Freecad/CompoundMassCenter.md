# Compound shapes do not expose a direct center of mass

Expected behavior: every non-null FreeCAD `Shape` exposes `CenterOfMass`.

Observed behavior: opening the public GA3D printer source in FreeCAD 1.1.4
produced a `Part.Compound`. Accessing `CenterOfMass` raised `AttributeError`,
although the compound contains measurable solids. The first native source
capture stopped before writing its screenshot.

Workaround: inspect each native solid's volume and center, sum the volumes,
and compute the compound center as the volume-weighted average. Report a null
center for a shape with no positive solid volume. Keep this geometric measure
separate from material-weighted mass properties. The capture must record errors
and terminate its goal-owned application after a failed observation.

The [public acceptance record](../../../../re/solidworks/records/PublicAssemblyAcceptance2026.md)
tracks source identity and the pending target comparison. Native source
inspection does not convert the source or establish target acceptance.
