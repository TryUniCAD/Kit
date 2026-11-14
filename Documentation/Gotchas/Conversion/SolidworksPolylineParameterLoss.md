# Polyline parameter loss

## Expectation

A native writer that proves one valid sketch and blind extrusion can also claim the source document's parameter capability without checking every source parameter.

## Actual behavior

`WriteDimensions` retains serializable length parameters and filters other values. `BuildPolyTree` previously saw only that filtered representation, while `FinishProofMut` could grant parameter and history capabilities from the geometry. A three-line sketch or extrusion with an unsupported non-length value could therefore produce a native file with that value missing even though the public write did not decline.

The existing FreeCAD pad projection is different: its recognized `freecad_path` properties are validated by `FreecadExtrusion` and describe its established pad options. A new property outside that recognized schema was accepted by the old subset check and discarded.

## Workaround

Inspect original owner-bound parameters while the three-line candidate is being selected, before length-only serialization. `HasPolyLoss` declines any non-length value on the sketch or extrusion unless it is a recognized, non-expression FreeCAD pad property. Both native preflight and native encoding pass the original neutral document to this guard, so neither path can bypass it.

Public integration coverage adds `CustomCount` to each owner in turn. Both cases require `HasVendorPartEncoding == False` and an `ApplicationUsabilityError` from `write_document(..., allow_carrier=False)`. The unchanged baseline controls continue to exercise recognized FreeCAD metadata and exact native length recovery.

See [the guard](../../../../src/convert/adapters/solidworks/core/PolylineParameters.py), [the integration coverage](../../../../tests/convert/solidworks/resolved/SolidworksPolylineThreeTests.py), and [the native change record](../../Changes/Solidworks/SolidworksThreeLineNativeHistories.md).
