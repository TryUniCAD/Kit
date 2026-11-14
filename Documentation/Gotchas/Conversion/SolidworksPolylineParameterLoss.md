# Polyline parameter loss

## Expectation

A native writer that proves one valid sketch and blind extrusion can also claim the source document's parameter capability without checking every source parameter.

## Actual behavior

`WriteDimensions` retains serializable length parameters and filters other values. `BuildPolyTree` previously saw only that filtered representation, while `FinishProofMut` could grant parameter and history capabilities from the geometry. Unsupported source parameters could therefore disappear while the public write continued.

The existing FreeCAD pad projection is different: its recognized `freecad_path` properties are validated by `FreecadExtrusion` and describe its established pad options. Its subset check accepted an additional property, and `FinishSingleMut` retained only the generated `D1`. The first non-length guard still admitted an extra length with a unique `freecad_path`, so an extra `CustomLength` exposed a separate loss path.

## Workaround

Inspect every original source parameter while the three-line candidate is being selected, before length-only serialization. `HasPolyLoss` admits only native `D1` length or a recognized, non-expression FreeCAD pad property on the extrusion. Other owners, extra lengths, sketch dimensions, non-length values, and expressions decline native encoding. Both native preflight and native encoding pass the original neutral document to this guard.

Public integration coverage adds `CustomCount` to the sketch and extrusion, then adds `CustomLength` to the extrusion. Every case requires `HasVendorPartEncoding == False` and an `ApplicationUsabilityError` from `write_document(..., allow_carrier=False)`. The unchanged baseline controls continue to exercise recognized FreeCAD metadata and exact native length recovery.

See [the guard](../../../../src/convert/adapters/solidworks/core/PolylineParameters.py), [the integration coverage](../../../../tests/convert/solidworks/resolved/SolidworksPolylineThreeTests.py), and [the native change record](../../Changes/Solidworks/SolidworksThreeLineNativeHistories.md).
