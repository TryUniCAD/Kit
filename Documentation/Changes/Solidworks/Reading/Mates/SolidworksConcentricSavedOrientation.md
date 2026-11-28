# Read saved concentric wrapper orientation

The normal SOLIDWORKS assembly reader accepts the measured ordinary solved concentric profile when the selected wrappers and actual child cylinder store opposite axis directions. It validates both unit axes component by component along the same carrier, applies the rigid occurrence transform to each signed wrapper direction, and checks the ordered world directions against the authored alignment. The entity exposes the signed world vector as `stored_axis`.

Read with `convert.open_document(path)` and require the `solidworks.typed_mates_semantics` status to be `admitted`. The profile requires two direct rigid occurrences of the same real saved cylinder. The wrapper directions must agree in the child coordinate system. Pre-solve files and mismatched directions, positions, radii or owners still return `unsupported`.

Default and metadata-only public readback matched the disclosed native-saved radial pair and its fresh reopen observation. The aligned, aligned/locked and rotated anti-aligned controls kept identical public documents. Held-out qualification and full source-derived assembly construction remain open. [Usage](../../../../Reference/Adapters/SolidworksConcentricReading.md) · [Host evidence](../../../../../re/solidworks/records/ConcentricSavedAxis2026.md)
