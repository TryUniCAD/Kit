# Knot intervals set the converted parameters but not the jump lists

## Expectation

A TSM edge knot interval only spaces the T-spline parameters. Fusion would store the same converted body for every interval, or Kit could derive the body from the unit body. Kit refused every interval other than 1.

## Actual behavior

Fusion 2706.1.17 imported and converted a 4 × 4 plane grid and the box primitive with other intervals. All 11 imports had Form health 0, and zero documents stayed open.

| Cage | Intervals | Converted knots | Kit result |
| --- | --- | --- | --- |
| Plane 4 × 4 | All 1 | 0, 1, 2, 3, 4 | Equal |
| Plane 4 × 4 | All 2 | 0, 2, 4, 6, 8 | Equal |
| Plane 4 × 4 | All 0.5 | 0, 0.5, 1, 1.5, 2 | Unreadable patch program |
| Plane 4 × 4 | Column 1 at 2 | U: 0, 1, 3, 4, 5 | Refused |
| Plane 4 × 4 | Column 0 at 2 | U: 0, 2, 3, 4, 5 | Refused |
| Plane 4 × 4 | Row 2 at 3 | V: 0, 1, 2, 5, 6 | Refused |
| Plane 4 × 4 | Column 1 at 2 and row 2 at 0.5 | V: 0, 1, 2, 2.5, 3.5 | Unreadable patch program |
| Plane 4 × 4 | One edge at 2 | U: 0, 1, 2.0588235294117645, … | Unreadable TSM |
| Box | All 1 | 0, 0.25, 0.5, 1, 1.5, 1.75, 2 | Equal |
| Box | All 2 | 0, 0.5, 1, 2, 3, 3.5, 4 | Refused |
| Box | One edge at 2 | 0, 0.2586206896551724, … | Unreadable TSM |

The knots are the running sums of the column and row intervals. The poles stay the grips, within 2.2e-15 cm of the unit conversion. Each patch cell and progenitor window spans its intervals. The patch program then holds values such as `0.5` and `-2.5`, and Kit's `PatchCell` holds integers.

An interval that differs from its grid row or column is inconsistent. Fusion rewrote such cages on import. It saved some intervals as 1.0588235294117645, moved grips and added `106ek` and `50000grip` TSM records.

The jump lists do not follow the parametric rule of the [discontinuity gotcha](ConvertedDiscontinuityLists.md). The plane is flat, so each boundary curve is a straight line. With mixed intervals, its third derivative jumps by 0.16 to 0.67 at interior knots. Each jump lies along the curve direction within 5.6e-17. Fusion stored empty lists. The kernel routine `test_discontinuity` at `0x201410` in `libASMkern232` compares cross products of the left and right derivatives. Its tolerances come from `get_resnor`. The test is therefore geometric, and a jump along the tangent is no discontinuity.

## Workaround

`ConvertGrid` accepts one whole-number interval c from 1 to 4096 on every edge. It scales the knots, patch cells, pcurves and progenitor windows by c. It computes the jump lists on the unit-parameter surface and scales their knots by c. A uniform scale changes no geometry, so the verified unit rule still holds.

Fusion accepted two warped grids that `EmitFormDoc` wrote with intervals 2 and 3. Each Kit document equalled the Fusion conversion of its TSM within 2.7e-15 cm, and the jump lists were equal. Both documents passed the edit, save and reopen stages.

| Cage | Error |
| --- | --- |
| Grid with mixed intervals | `Fusion grid conversion needs one knot interval for every edge` |
| Grid with a fractional or larger interval | `Fusion grid conversion needs a whole-number knot interval` |
| Stencil layout with any other interval | `Fusion Form stencil conversion needs unit knot intervals` |

Mixed intervals need the geometric jump test, and no curved local archive tests it. Fractional intervals need a non-integer patch program. Stencil layouts need the body shapes to scale, and no table covers that.

## Evidence

- [Interval check](../../../../../re/Fusion/Reconstruction/FormDocuments/IntervalCheck.json)
- [Interval probe](../../../../../re/Fusion/LocalOracle/FormDocuments/Intervals/Probe.json)
- [Interval preparation](../../../../../re/Fusion/LocalOracle/FormDocuments/Intervals/Preparation.json)
- [Interval document acceptance](../../../../../re/Fusion/LocalOracle/FormDocuments/IntervalDocuments/NativeAcceptance.json)
- [Kernel notes](../../../../../re/Fusion/External/ReverseEngineer/README.md)
