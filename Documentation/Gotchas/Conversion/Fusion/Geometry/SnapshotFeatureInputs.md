# The snapshot member of a feature archive is not the final body

## Expectation

An archive with one `.smbh` history and one `.smb` snapshot stores the final body twice. The snapshot equals the current state of the history.

## Actual behavior

In the four fillet archives below, the `.smb` snapshot holds the bodies before the fillet and planar sheet bodies. Fusion 2706.1.17 imported these byte-exact snapshots with these results.

| Archive | Final body in the design | Bodies in the snapshot |
| --- | --- | --- |
| `fillet_chord.f3d` | 7 faces, 51.80932 cm², 1 NURBS face | 6-face box of 52.0 cm² and 24.0 cm³, two sheets |
| `fillet_curvature.f3d` | 7 faces, 51.729132 cm², 1 NURBS face | 6-face box of 52.0 cm² and 24.0 cm³, two sheets |
| `rule_asymmetric.f3d` | 31 faces, 96.59657 cm², 20 NURBS faces | Two boxes of 24.0 cm² and 82.0 cm², four sheets |
| `one_quarter.f3d`, variable fillet | 7 faces, 51.670676 cm², 1 NURBS face | 6-face box of 52.0 cm² and 24.0 cm³, two sheets |
| `solid_aligned.f3d`, solid sweep | 15 faces, 220.613782 cm², 3 NURBS faces | Eight bodies, including a 9-face sweep body of 8.613782 cm² and a 6-face body of 212.0 cm² |

The four fillet snapshots contain no complex records. The loft and rail sweep snapshots contain the final body and extra planar sheets.

`EmitStateSmb` writes the current state of a history. For all 62 corpus history archives with complex records, that state differs from the archive snapshot. Kit did not open these states in Fusion.

## Workaround

Do not use the `.smb` snapshot as the final body of a feature archive. Read the `.smbh` history and use `EmitStateSmb` for the current state. Do not use a snapshot import to test a fillet surface codec, because the snapshot has no fillet surface.

## Evidence

- [Native acceptance](../../../../../re/Fusion/LocalOracle/ComplexGeometry/NativeAcceptance.json), section `geometry`
- [State comparison](../../../../../re/Fusion/Reconstruction/ComplexGeometry/VerifyStates.json)
- [Native coverage](../../../../../re/Fusion/Reconstruction/ComplexGeometry/NativeCoverage.json)
- [Complex geometry change entry](../../../../Changes/Fusion/Geometry/FusionComplexGeometry.md)
