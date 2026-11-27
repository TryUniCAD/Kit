# Exact circular top-rim geometry

`BuildRimFillet` builds an analytic neutral solid from body identity, profile radius, extrusion height and fillet radius in millimetres. It uses three circular junctions, two plane caps, one cylinder and an explicitly trimmed quarter torus. The result has four faces, three edges/vertices and six reciprocal edge uses. Its negative-X seam vertices match the recorded native sources.

`RimMoments` integrates radial slices to return volume, area, centroid height and radial/axial second moments. It does not sample a mesh, fit a cache or read a source file. Complete origin inertia follows from those moments. Finite dimensions require `0 < fillet < min(radius, height)` and must remain distinguishable at coordinate precision. These mathematical bounds do not extend native acceptance beyond the recorded source family.

The underlying torus is trimmed. A whole-face ring-torus qualification cannot substitute for this quarter-torus boundary. The [frozen derivation](../../../../re/Fusion/DecodedPromotion20261127/RimFilletGeometry/Rules.md) and [component evidence](../../../../re/Fusion/DecodedPromotion20261127/RimFilletGeometry/Verification.json) retain all carrier, topology, source attribute, snapshot and mass checks against 22 actual native archives. Public SDK documents also preserve every native seam point and agree with recorded API volume, area, centroid and bounds.

The cache proof first checks actual volume/area/centroid against independent geometry, then compares all six centroidal tensor components using the generic parallel-axis relation and unchanged cache tolerances. Raw origin diagonal checks remain. Eleven original uncoupled cross-term refusals are retained. A frozen additive hypothesis passes a separate six-source translated/principal-frame cohort and thirteen encoded mass counterexamples; the subsequent rim replay is explicitly post-exposure. No new native API inertia measurement is claimed.

[Read-only source admission](../Readers/FusionCircularRimReader.md) remains separate from native writing and target-application acceptance.
