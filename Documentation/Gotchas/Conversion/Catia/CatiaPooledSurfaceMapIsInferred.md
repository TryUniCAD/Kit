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

A plain index table is ruled out: every stream of `Reservoir` was scanned for a run of exactly
`FaceCount` 8-bit or 16-bit little-endian values below the pool size that covers at least 85% of the
pool, and no such run exists, so the reference is not an array of surface indices. A permutation
table is ruled out too: every exact part was scanned for a run of `n` 8-, 16-, or 32-bit
little-endian values that is a permutation of `0..n-1` (the shape the identity map would take), and
only the two six-face washers hit, at a relative offset of `-245`, which is a vertex-index run. The
reference must be per-edge, through the edge's PCurve, or carried by the tag-difference reference
encoding like the object references in the OSMX graph.

`RefineMap` sharpens the inferred map without changing its status. It places the handles without the
tessellation snap, then re-picks each plane face's pooled plane by the summed distance of the face's
handles from the plane through the surface center along the stored trim normal, and each cylinder
face's pooled cylinder by the summed radial distance. One probe handle rejects a surface farther
than `0.5`, and refinement runs two rounds only for pooled parts with at most 400 faces, because a
round costs a full corner placement and the two largest parts gain under 3%. That drops the
unsatisfied handles from 209 to 181 of 1431 on `Reservoir` and from 1923 to 792 of 2666 on
`Pedal_Body`. The map is still inferred.

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
