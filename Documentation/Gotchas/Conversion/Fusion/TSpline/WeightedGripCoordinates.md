# Grip weights scale the stored grip coordinates

## Expectation

A rational spline keeps its shape when every weight gets the same factor. A T-spline cage with weight 2 on every grip should convert to the unit-weight body.

## Actual behavior

Fusion 2706.1.17 converted the box primitive cage with weight 2 on all 26 grips into a smaller solid. The probe kept every TSM grip coordinate and changed only the weights.

| Cage | Grip weights | Form health | Solid | Area (cm²) |
| --- | --- | --- | --- | --- |
| Box primitive | All 1 | 0 | Yes | 23.560443509000663 |
| Box primitive | All 2 | 0 | Yes | 5.890110877250168 |
| Box primitive | Grip 0 at 2, others 1 | 0 | Yes | 24.28421510514164 |

The uniform area is a quarter of the unit area within 2e-15 cm². Fusion therefore divides the stored coordinates by the weight, so each TSM coordinate is a weighted, homogeneous value. Every cage dimension halves.

Kit cannot read any of the seven weighted archives. `ReadDocument` refuses each one with `Unsupported Fusion journal qualified field`. Unit-weight archives of the same box read without this error.

## Workaround

Refuse grip weights other than 1. `StencilKey` includes the weights, so no stencil table matches a weighted cage. `ConvertGrid` refuses weights as well. A future weighted converter must divide the TSM coordinates by the weight. It must also read the converted cache of a weighted cage first.

## Evidence

- [Probe preparation](../../../../../re/Fusion/LocalOracle/FormDocuments/Stencil/Preparation.json)
- [Probe results](../../../../../re/Fusion/LocalOracle/FormDocuments/Stencil/Probe.json)
- [Weight probe](../../../../../re/Fusion/Reconstruction/FormDocuments/Stencil/WeightProbe.json)
