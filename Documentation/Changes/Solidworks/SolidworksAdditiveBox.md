# Additive box primitives

## Behavior

A standalone `PartDesign::AdditiveBox` with an identity placement and only the principal
default planes now lowers to the recovered rectangle-pad program. Two real property
schemas are accepted:

- FreeCAD 1.0.2 and 1.1.4, which include `FuzzyTolerance = -1` and
  `AttacherEngine = Engine 3D`
- FreeCAD 0.21.2, which omits both properties and may carry `Refine = False`

Every recognized pad property is validated exactly: `Length`, `Width`, and `Height` must be
positive lengths, `MapMode` must be `0`, `MapPathParameter` must be `0`, `MapReversed` must
be false, `Visibility` must be true, `Refine` must be a boolean, `AttacherType` must be
`Attacher::AttachEngine3D`, `Label` must equal the feature name, and `Label2` must be
empty. `Suppressed`, when present, must be false. Unknown properties decline native
encoding instead of being dropped.

The source B-rep must remain the exact eight-vertex, twelve-edge, six-face box at the
origin, so the emitted sketch and pad match the authored solid.

## Usage

No option is required. A document read from a real FCStd file flows through
`write_document(..., allow_carrier=False)` and reports vendor-loadable,
application-usable, near-lossless, self-contained output.

## Limitations

- the placement must be identity; a translation or rotation still declines native encoding
  because the recovered box program fixes the sketch to the model origin
- only the principal default planes are allowed; a custom datum plane is rejected
- the B-rep must be the exact origin box; a translated or otherwise modified solid is
  rejected
- the output is classified `native-metadata-with-kit-neutral` rather than `native-exact`
  because the B-rep is rebuilt from the feature instead of carried as a native B-rep
  payload
- SOLIDWORKS acceptance of these specific fixtures was not re-run in this session; the
  earlier oracle evidence for the box program still applies to the same rectangle-pad
  program

## Verification

`tests/convert/solidworks/core/SolidworksCorpusTests.py` adds `TestAddBox`, which opens
`re/solidworks/examples/FreeCAD/AdditiveBox-1.1.4.FCStd` and
`AdditiveBox-0.21.2.FCStd` through the public reader, requires native preflight to accept
them, writes each with `allow_carrier=False`, requires vendor-loadable,
application-usable, near-lossless, self-contained output, then decodes the emitted native
model and requires a `(0, 0, 20, 30)` rectangle and a `10 mm` pad.

The fixtures are copied from the cadmpeg FreeCAD corpus under the Apache License 2.0; the
attribution is in [the fixture notice](../../../re/solidworks/examples/FreeCAD/NOTICE.md).
They are read/write inputs only and are not donor streams for generated output. The
identity-placement limitation for translated boxes remains recorded in
[Box placement lowering](../../Gotchas/Conversion/SolidworksBoxPlacementLowering.md).
