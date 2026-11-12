# Fusion metadata header semantics

## Behavior

Static native analysis identifies previously positional metadata header fields.
The [header model](../../re/Fusion/Reconstruction/HeaderGrammar/HeaderModel.md) explains the fields and their persistence methods.

`MetaHeader.HeaderWords` holds one little-endian 64-bit saved software version.
Its construction is `(major << 50) | (minor << 38) | build`.
The controlled words `(17, 709361728)` represent Fusion version `2706.1.17`.
Major and minor fields use 14 and 12 bits. Newly constructed build values use 32 bits.

The wide UUID called `Namespace` represents the segment's `currentVersion`.
The storage identifier fields represent segment type, add-in, and neutron type.
The following word counts ancestry UUIDs. Each ancestry entry uses counted UTF-16 text.
The native save method and `isDescendedFrom` traverse the same ancestry vector.

The [manifest analysis](../../re/Fusion/Reconstruction/HeaderGrammar/ManifestNative.json) also identifies document identity and current-version UUIDs.
The observed value 5 before segment declarations is the next segment ID, not a format constant.
Per-module version maps contain persisted migrator numbers.

## Evidence and limits

[NativeHeader.json](../../re/Fusion/Reconstruction/HeaderGrammar/NativeHeader.json) records source digests, addresses, and bounded disassembly excerpts.
`InspectHeader.py` regenerates these observations without loading vendor libraries.
This addition interprets existing fields. It does not expand production header support.
Current production framing admits the observed empty-ancestry profile only.
No local automated tests ran for this documentation and research addition.

See the [universal binary disassembly gotcha](../Gotchas/Conversion/FusionUniversalDisassembly.md).
