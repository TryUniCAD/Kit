# Strict reading for Fusion-saved fixed-corner cuboids

Fusion's saved constrained rectangle can contain four horizontal and vertical rules plus a fixed corner. The reader now follows the stored line constraints, point references, dimension owners and parameter links for that profile. It preserves the separate fixed origin and the fixed rectangle vertex, including when both occupy the same position.

## Usage

Use the strict SDK reader or the existing `kit decode` command for a supported Fusion `.f3d` file. Persist the returned `CadDocument` with `to_json` and restore it with `CadDocument.from_json`. The JSON contains native-state contract version 2. That contract keeps the full decoded state, including the journal, snapshot, graphics and empty configuration sidecars.

The affected scope is a positive, axis-aligned XY cuboid with two directly driven rectangular dimensions and one plain, one-sided solid extrusion. The reader pairs each native dimension with its stored driver and axis independently of list order. The actual parameter names, values, expressions and references come from the file. The corner's fixed property stays on its actual sketch point. The reader preserves the actual corner and origin independently of coordinate equality. It retains along-line caption placement and axial extension coordinates in the typed state while validating the current operands, carrier and measured length.

## Limits

This profile remains read-only. The bounded research encoder admits only its qualified constructor profile. The native-state writer and research encoder still refuse edits and native output for the new saved fixed-corner branch. Fresh native evidence on reconstructed archives and the complete dependency rules for generated edits are pending.

Some Fusion-saved graphics bounds retain an earlier height. The reader keeps those graphics values and validates their links while using the typed solid and snapshot for current geometry. See the [display bounds gotcha](../../../Gotchas/Conversion/Fusion/Api/FusionSavedGraphicsBounds.md).

## Verification

The original strict reader refused 12 prior native controls, edits and restores at the five-rule boundary. The updated SDK reads those cases and preserves the complete `CadDocument` through JSON. Wire-level re-emission independently yielded complete typed-model equality in 12 of 12 cases. It produced different archive hashes, so previous Fusion measurements do not establish native acceptance for the emitted bytes.

The [local capture and replay tooling](../../../../re/Fusion/LocalOracle/SavedCuboidRoundTrip/README.md) prepares public-API captures and exact candidate/control requests. The [readiness report](../../../../re/Fusion/LocalOracle/SavedCuboidRoundTrip/Readiness.md) records why the native runs did not dispatch.

The [public boundary evidence](../../../../re/Fusion/SavedCuboidRoundTrip/PublicBoundaryEvidence.md) records 17 SDK integration checks and four fresh CLI decode checks. The [boundary harness](../../../../re/Fusion/SavedCuboidRoundTrip/PublicBoundaryCheck.py) persists the complete JSON and verifies the explicit public write refusal. The fixtures preserve the original receipt bytes through checkout to keep their SHA-256 bindings. See the [receipt line endings gotcha](../../../Gotchas/Packaging/ResearchReceiptLineEndings.md).

See the [source observations, exact sample hashes and audit procedure](../../../../re/Fusion/SavedCuboidRoundTrip/Findings.md). The [dimension edit and reopen receipt](../../../../re/Fusion/LocalOracle/DimensionAuthoring/NativeAcceptance.json) independently verifies the edited 19 × 29 × 37 mm solid and its 20.387 cm³ volume. See the [extension anchor gotcha](../../../Gotchas/Conversion/Fusion/Api/FusionStaleDimExtension.md). The saved 23 mm extension anchor survives JSON while the measured depth remains 29 mm. Product conversion acceptance and the broader Fusion reader and writer remain open.
