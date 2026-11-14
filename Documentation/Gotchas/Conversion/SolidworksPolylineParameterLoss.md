# Polyline parameter loss

## Expectation

A native writer that proves one valid sketch and blind extrusion can also claim the source document's parameter capability without checking every source parameter.

## Actual behavior

`WriteDimensions` retains serializable length parameters and filters other values. `BuildPolyTree` previously saw only that filtered representation, while `FinishProofMut` could grant parameter and history capabilities from the geometry. Unsupported source parameters could therefore disappear while the public write continued.

The existing FreeCAD pad projection is different: its recognized `freecad_path` properties are validated by `FreecadExtrusion` and describe its established pad options. Its subset check accepted an additional property, and `FinishSingleMut` retained only the generated `D1`. The first non-length guard still admitted an extra length with a unique `freecad_path`, so an extra `CustomLength` exposed a separate loss path. Its allowlist also named `FuzzyTolerance` while the projection did not validate that value, so nonzero tolerance could vanish.

The same candidate check also compares the bound depth parameter with the extrusion definition in a supported length unit, requires driving roles, and rejects nonzero offsets or draft settings plus more than one configuration. A stale depth or driven parameter otherwise leaves `FinishSingleMut` and capability proof looking at a rewritten `D1` rather than the intended edit.

An unset definition field is not authored intent. The native reader leaves `offset`, `second_offset`, `draft_angle`, `second_draft_angle`, and `second_length` as `None` because the blind-pad encoding stores only the depth, so treating `None` as loss rejected every document this writer had just produced. Only a present value that differs from the native default is a loss.

The projection now requires the exact complete pad-property set and validates every value exactly. The measured FreeCAD default is `FuzzyTolerance = -1`, not the synthetic zero; the source feature name and empty `Label2` are the only accepted labels. A tolerance differing from `-1` by `5e-11` is rejected even though ordinary approximate numeric comparison would accept it. The same exact path covers the extrusion definition and pad parameter, including an `Offset` of `5e-11` on both. Owner checks alone cannot establish that a recognized property's value is representable.

## Workaround

Inspect every original source parameter while the three-line candidate is being selected, before length-only serialization. `HasPolyLoss` admits only native `D1` length or a recognized, non-expression FreeCAD pad property on the extrusion. Other owners, extra lengths, sketch dimensions, non-length values, and expressions decline native encoding. Both native preflight and native encoding pass the original neutral document to this guard.

Public integration coverage adds `CustomCount` to the sketch and extrusion, adds `CustomLength` to the extrusion, sets `FuzzyTolerance` to `-1 + 5e-11`, sets a custom `Label2`, and sets `Offset` to `5e-11` on both the pad parameter and extrusion definition. Additional cases introduce a stale FreeCAD `Length`, an unsupported length unit, a driven `Length` role, and a second configuration. Every case requires `HasVendorPartEncoding == False`; the default public `write_document` then raises `SldprtFormatError` even though `allow_carrier` defaults to true. The unchanged baseline controls use the measured `-1` tolerance and default labels, and still exercise exact native length recovery.

See [the guard](../../../../src/convert/adapters/solidworks/core/PolylineParameters.py), [the integration coverage](../../../../tests/convert/solidworks/resolved/SolidworksPolylineThreeTests.py), and [the native change record](../../Changes/Solidworks/SolidworksThreeLineNativeHistories.md).
