# Additive box primitives

## Behavior

A standalone `PartDesign::AdditiveBox` with an identity placement and only the principal
default planes now lowers to the recovered rectangle-pad program. The FreeCAD 1.0.2 and
1.1.4 schema is accepted when it carries `FuzzyTolerance = -1`,
`AttacherEngine = Engine 3D`, and `Refine = True`.

The FreeCAD 0.21.2 variant that omits the tolerance and attacher engine and uses
`Refine = False` is rejected. `Refine = False` is an authored cleanup choice that the
recovered rectangle-pad program does not serialize, so accepting it would drop intent.

Every recognized pad property is validated exactly: `Length`, `Width`, and `Height` must be
positive lengths, `MapMode` must be `0`, `MapPathParameter` must be exactly `0`,
`MapReversed` must be false, `Visibility` must be true, `Refine` must be true,
`AttacherType` must be `Attacher::AttachEngine3D`, `Label` must equal the feature name, and
`Label2` must be empty. `Suppressed`, when present, must be false, and `FuzzyTolerance`,
when present, must be exactly `-1`. Every parameter must be driving, because the native
pad writes driving dimensions. Unknown properties decline native encoding instead of being
dropped.

The source B-rep must remain the exact eight-vertex, twelve-edge, six-face box at the
origin, so the emitted sketch and pad match the authored solid. Validation lives in
`src/convert/adapters/solidworks/core/BoxFaces.py`: every edge must be an axis-aligned
line, every face an axis-aligned plane, and the two face offsets on each axis must be `0`
and the authored dimension within the same `1e-9` geometry tolerance as the vertex check. A
curved face, a shifted planar face, a face moved from `Length` to `-Length`, or a displaced
edge curve is rejected even when the eight corners are unchanged. Each edge curve must also
lie on its two referenced vertices, every B-rep body must have an identity transform, and
the region must be solid, so an open shell is rejected.

## Usage

No option is required. A document read from a real FCStd file flows through
`write_document(..., allow_carrier=False)` and reports vendor-loadable,
application-usable, near-lossless, self-contained output.

## Limitations

- the placement must be identity; a translation or rotation still declines native encoding
  because the recovered box program fixes the sketch to the model origin
- only the exact principal default planes are allowed; a custom datum plane or a default
  plane rotated about its normal is rejected so the authored frame is not replaced by
  canonical axes
- the B-rep must be the exact origin box; a translated or otherwise modified solid is
  rejected
- the output is classified `native-metadata-with-kit-neutral` rather than `native-exact`
  because the B-rep is rebuilt from the feature instead of carried as a native B-rep
  payload
- SOLIDWORKS accepted the 1.1.4 output: `OracleDrive.vbs` edited `D1@Boss-Extrude1` to
  13 mm, rebuilt, and measured 7800 mm3 and 2500 mm2, matching 20 x 30 x 13 exactly

## Verification

`tests/convert/solidworks/core/SolidworksCorpusTests.py` adds `TestAddBox`, which opens
`re/solidworks/examples/FreeCAD/AdditiveBox-1.1.4.FCStd` through the public reader,
requires native preflight to accept it, writes it with `allow_carrier=False`, requires
vendor-loadable, application-usable, near-lossless, self-contained output, then decodes
the emitted native model and requires a `(0, 0, 20, 30)` rectangle and a `10 mm` pad.
`TestAddBoxNo` opens `AdditiveBox-0.21.2.FCStd`, requires native preflight to reject it,
and requires the public writer to raise `ApplicationUsabilityError`. `TestBoxPlane` rotates
the first principal plane of the 1.1.4 fixture about its normal and requires the same
rejection. `TestBoxDriven` changes the bound `Length` role to driven, `TestBoxCurved` replaces one
planar face with a cylinder, and `TestBoxShift` moves a face off its box offset and then
flips the opposite face from `Length` to `-Length`, `TestBoxFrame` gives the body a
nonidentity transform, and `TestBoxShell` opens the region; all require the same rejection.

SOLIDWORKS Design Premium 2026 SP5.2 in Parallels opened the generated 1.1.4 output,
rebuilt it after a depth edit to 13 mm, and measured volume 7800 mm3 and area 2500 mm2,
which is exactly 20 x 30 x 13. The run is recorded in
[recent oracle runs](../../../re/solidworks/records/RecentOracleRuns.md) and uses
`re/tooling/harness/OracleDrive.vbs`.

The fixtures are copied from the cadmpeg FreeCAD corpus under the Apache License 2.0; the
attribution is in [the fixture notice](../../../re/solidworks/examples/FreeCAD/NOTICE.md).
They are read/write inputs only and are not donor streams for generated output. The
identity-placement limitation for translated boxes remains recorded in
[Box placement lowering](../../Gotchas/Conversion/SolidworksBoxPlacementLowering.md).
