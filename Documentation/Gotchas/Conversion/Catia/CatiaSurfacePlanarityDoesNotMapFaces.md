# CATIA surface planarity does not determine the face-to-surface map

## Expectation

When a CATIA part has fewer surface records than faces, the surface list is the face list with
duplicate surfaces removed, in face order. A face is planar exactly when its trim record carries a
vector, and a surface is planar exactly when its kind is `0x32`, so the planarity sequences should
align and give the map.

## Observed behavior

The planarity sequences do align as a *subsequence* for all five pooled parts, but a subsequence
match is far weaker than an index match and does not survive a stronger test.

The stronger test asks for a monotone surjection: a non-decreasing map from faces to surfaces that
uses every surface and gives every face a surface of the same planarity class. Solving it as a path
problem (each face keeps the current surface or advances by one, planarity must match) gives:

| Part | Monotone surjection exists | Solutions |
| --- | --- | ---: |
| `Reservoir` | yes | 12600 |
| `Pedal_Body` | yes | 129679067468302852500 |
| `4784` | no | 0 |
| `4876` | no | 0 |
| `4876_1` | no | 0 |

So the surface list is not in face order for `4784`, `4876`, and `4876_1`, and even where a
monotone surjection exists it is wildly non-unique. Planarity cannot pick the map.

The missing surfaces are also not stored elsewhere. `MainDataStream` contains no `00 33 <kind>`
surface marker in any of the five parts, and the `SurfacicReps` header field at offset 18 is `2` for
`Reservoir` and `26` for the others, not the surface count. The trim record has no spare field for a
surface index, and no byte position in a surface record sums to the face count.

The pooling is also entirely among non-planar faces. The planar face count equals the plane-surface
count exactly in every pooled part, and the deficit equals the non-planar face count minus the
non-planar surface count:

| Part | Planar faces | Plane surfaces | Non-planar faces | Non-planar surfaces | Deficit |
| --- | ---: | ---: | ---: | ---: | ---: |
| `Reservoir` | 13 | 13 | 58 | 43 | 15 |
| `Pedal_Body` | 66 | 66 | 272 | 248 | 24 |
| `4784` | 91 | 91 | 325 | 179 | 146 |
| `4876` | 359 | 359 | 511 | 355 | 156 |
| `4876_1` | 359 | 359 | 511 | 355 | 156 |

So planes are never shared and cylinders, cones, spheres, and tori are. That narrows the map but
still does not determine it: matching planar faces to plane surfaces by normal and scoring candidate
planes by how many vertex-table points they contain is not unique (`Reservoir` 0 unique of 13,
`Pedal_Body` 22 of 66, `4784` 20 of 91), and the trim `counts` fields are not surface indices (all in
range but only 12 to 27 distinct values against 56 to 714 surfaces).

## Workaround

Do not infer the face-to-surface map from planarity or from list position. The reader requires the
surface count to equal the face count and rejects the five pooled parts, which is the honest
behavior.

The format does not store the reference anywhere a reference could live. The object headers are a
contiguous chain from offset 8 to 206 in `Reservoir` and cover only the three bodies. The 71 face
headers at 27035..27603 are eight bytes each, `30 04 04 ff ff e1 e1 e1`, and the three trailing
bytes are constant across all 71 rows; decoded as tag differences they are three `+56` steps and the
whole run decodes to `56, 112, 168, ..., 11928`, a degenerate sequence rather than a tag array. The
trim records are fully consumed by the prefix, kind, three counts, `ff`-prefixed total, optional
vector, lengths, and handles, with no spare field.

So the remaining possibility is that the writer deduplicates surfaces and the reader re-derives the
map geometrically. That is why the pooled parts have fewer surfaces than faces, and why the planar
faces still correspond one-to-one with the plane surfaces.

## Evidence

- `re/catia/Brep.md`
- `src/convert/adapters/catia/NativeBrep.py`
