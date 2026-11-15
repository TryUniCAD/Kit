# CATIA pooled surface map is inferred, not decoded

## Expectation

A CATIA V5 part stores one surface per face, so the surface list in `SurfacicReps` can be zipped
with the face list in `MainDataStream`.

## Actual behavior

Five corpus parts (`4784`, `4876`, `4876_1`, `Pedal_Body`, `Reservoir`) have fewer surfaces than
faces: 270/416, 714/870, 714/870, 314/338, and 56/71. The surfaces are pooled, and several faces
share one surface. The face-to-surface reference is not in the face record, the body record, the
trim chain, the face-outer-bound run, the `42 ff` block, the `60`/`54` tail, or any of the twelve
`MainDataStream` regions. It is carried by the edge's `CATPCurveEquation`, whose Stream writes the
surface as its first object, but the PCurve record is not located in `MainDataStream` or
`SurfacicReps`, and the concrete function class is caller-supplied, so the record has no fixed
signature.

The reader therefore infers the map from the `00 33 37` edge records: a plane face is matched to the
plane surface with the same offset along the trim normal as the edge circle centers, a cylinder face
is matched to the cylinder surface with the edge circle radius, and the remaining faces take the
least-used surface whose kind is compatible with the trim kind. The inferred map is total, so all 27
corpus parts decode, but it is not the stored map.

## Workaround

Treat the five pooled parts as approximate. The reader emits
`catia.brep.native_surface_map_heuristic` for them. Do not use their decoded geometry as a
ground-truth control, and do not claim lossless conversion for them. The exact map needs the PCurve
record or a controlled corpus generated through the vendor API.

## Evidence

- `src/convert/adapters/catia/NativeBrep.py` `AssignSurfaces` and `ParseEdgeCircles`.
- `re/catia/Brep.md` sections on the `60`/`54` tail, the `42 ff` block, the staircase negative
  result, and the PCurve Stream.
- `Documentation/Changes/Catia/CatiaNativeBrep.md` limits and verification.
