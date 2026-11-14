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

## Workaround

Do not infer the face-to-surface map from planarity or from list position. The reader requires the
surface count to equal the face count and rejects the five pooled parts, which is the honest
behavior. The map must come from the face record's own object reference.

## Evidence

- `re/catia/Brep.md`
- `src/convert/adapters/catia/NativeBrep.py`
