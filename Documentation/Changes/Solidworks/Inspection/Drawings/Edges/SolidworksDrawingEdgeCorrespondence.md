# Native drawing-to-part edge correspondence probe

PR #121 adds a narrow research retry after both original drawing controls failed a direct comparison between their view-edge body and underlying part body. The new helper uses the actual part extension for reverse mapping, the actual view for forward mapping and a native round trip, then requires exact edge/body membership within the part domain. The original view edge remains the annotation owner.

The exact installed type-library capture and current official 2026 documentation bind all four relevant API shapes and directions. The freezer preserves both earlier failures, all case inputs, camera-facing geometry and existing annotation/persistence checks.

Two host verifies and three custody or wrong-cap refusals pass. The two original native controls confirm the round trip and exact part-body membership. The depth-aware successor completes the note lifecycle in both controls and the generated linked pair. [Evidence and commands](../../../../../../re/solidworks/records/DrawingEdgeCorrespondence2026.md) · [Domain-identity gotcha](../../../../../Gotchas/Conversion/Solidworks/Oracle/Drawings/DrawingBodyIdentityNeedsNativeCorrespondence.md)
