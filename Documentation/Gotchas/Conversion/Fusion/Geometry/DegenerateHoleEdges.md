# A degenerate edge has no curve

## Expectation

Every live edge points to a curve. A null curve slot looks like a broken reference.

## Actual behavior

Hole and loft-point members contain degenerate edges. Such an edge has a null curve, and its start vertex is also its end vertex. All 40 corpus records of this kind are plain `edge` records with the same field values.

| Field | Value in all 40 records |
| --- | --- |
| Start parameter | 1.0 |
| End parameter | 0.0 |
| Curve reference | Null |
| Reversed | `F` |
| Convexity | `unknown` |

The records occur in 33 members from the hole, hole placement, tapped hole, loft point, analytic and tool studies.

## Workaround

Accept a null curve on a live edge only when its start and end vertex slots are equal. Require a curve on every other live edge. Keep the parameters as stored, because the start parameter is larger than the end parameter.

## Evidence

Fusion 2706.1.17 reports the degenerate tapped-hole edge with a `None` geometry object. A native script must check `BRepEdge.geometry` before it reads `objectType`. The re-emitted tapped-hole archive equaled its native control within 1e-8 at every stage.

- [Corpus bounds summary](../../../../../re/Fusion/Reconstruction/ComplexGeometry/VerifyBounds.json)
- [Native acceptance](../../../../../re/Fusion/LocalOracle/ComplexGeometry/Bounds/NativeAcceptance.json)
