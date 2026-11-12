# Thread faces carry two feature attribute layouts

## Expectation

The `ATTRIB_CUSTOM-attrib` families are the generic tag, sketch, timestamp and tracking families. A journal with another family looks unsupported.

## Actual behavior

Thread and tapped-hole faces carry the `FDM_feature_attrib_def` family. After the family name, the payload is `(4,2)`, `(4,2)`, a data name, `(4,3)`, a feature tag, flags, a layout count and a type code. The data name sets the layout count and the tail.

| Data name | Layout count | Type code | Tail | Records |
| --- | --- | --- | --- | --- |
| `feature_data` | 2 | 1902 | None | 7 |
| `thread_face_data` | 6 | 1901 | Three points and a long | 21 |

All 28 records are live and owned by faces. The flags value is 2097152 in every record. The feature tags 303, 304 and 306 match feature identifiers in the generic tags of the same journals.

Split-face, draft and parting-line draft members hold 17 `no_merge_attribute-st-attrib` records. Each has only the common attribute head of five tokens. The 16 live records are owned by edges.

## Workaround

Read the family with `FeatureAttrib` and `NoMergeAttrib`. Reject a data name outside the two known layouts. Reject a thread layout without its three points and tail, and reject a plain layout with them.

## Evidence

Fusion 2706.1.17 opened both re-emitted thread archives and rebuilt them after a driving parameter edit. The NURBS thread faces moved by the expected length.

| Archive | Parameter edit | Thread extent (cm) | Thread face area (cm²) | Helix edge length (cm) |
| --- | --- | --- | --- | --- |
| `ModeledThread` | `d1` 20 mm to 30 mm | 2.0 to 3.0 | 8.979 to 13.469 | 160.318 to 238.225 |
| `TappedHole` | `d7` 10 mm to 8 mm | 1.0 to 0.8 | 4.559 to 3.647 | 85.455 to 69.278 |

- [Corpus bounds summary](../../../../../re/Fusion/Reconstruction/ComplexGeometry/VerifyBounds.json)
- [Acceptance preparation](../../../../../re/Fusion/LocalOracle/ComplexGeometry/Bounds/Preparation.json)
- [Native acceptance](../../../../../re/Fusion/LocalOracle/ComplexGeometry/Bounds/NativeAcceptance.json)
