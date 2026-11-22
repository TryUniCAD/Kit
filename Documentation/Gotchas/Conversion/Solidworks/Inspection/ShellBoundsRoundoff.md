# The saved shell uses one corner tolerance

The saved Parasolid vertices and the linked sketch and extrusion can place
a computed corner at adjacent floating-point coordinates. An exact extrema
check can reject an otherwise valid shell before its existing per-corner
rounding check runs.

Use the one-to-one check of all sixteen expected corners and its common
coordinate-scale tolerance to establish the entire extent. Then check
the actual loop ownership, planar and straight carriers, and signed
moments. The [shared process proof](../../../../../re/solidworks/measurements/2026/SdkOpenShellReaderParts01.json)
checks a translated shell with a four-step difference on one axis and
keeps the refusal for a genuine solid beyond the rounding budget.
