# Typed prism history in Fusion documents

`DocumentCodec.ReadDocument` now dispatches qualified solved history parts to the cylinder or rectangular-prism codec. `DocumentBody.History` is the explicit union `HistoryModel | PrismHistory`. `EmitParsed` selects the matching complete serializer and preserves typed prism carrier frames, tags, identity and journal state.

History dispatch requires a `Breps.BlobParts/BREP.*.smbh` member, a bounded payload and exactly two top-level roots. The two accepted initial inventories are the cylinder profile's 35 records and the prism profile's 102 records. Each selected codec then validates its complete topology, attributes, history and EOF. Unsupported inventories fail; a decoding error does not trigger an alternate parser or raw-byte fallback.

Design segment reading now selects exact class/version/base declarations from the packaged native entity catalog using the archive's own metadata. This supports the rectangle's `Line3D` records and nonempty adjacent source-tag sets without adding source object values to the authoring vocabulary. ACT and browser segments retain their existing qualified schemas. Unknown versions, missing class declarations and incompatible references continue to fail.

The minimal authored document envelope and complete ordinary native archives remain distinct supported boundaries. The native rectangle source also contains a `.smb` snapshot, a material package, two configuration members and nested OGS graphics members. Those parts are not silently omitted or retained as opaque payloads. The complete native archive remains rejected by the strict container or document reader. See [native document auxiliary parts](../../Gotchas/Conversion/Fusion/FusionNativeAuxiliaryParts.md).

## Verification

Remote compatibility coverage reads both emitted history kinds through ZIP and document-part boundaries, reserializes their typed results, checks rejection of snapshot/material parts and exercises the native rectangle Design streams with metadata-selected schemas. The native Design case checks 303 physical records, 269 primary records and four `Line3D` entities before exact stream reserialization. Existing authored document cases retain their complete read/edit/emit coverage.

The prism history serializer itself has independent native acceptance: both canonical re-emission and independently authored history opened with volume 30 cm³ and topology 6/12/8, rolled back to no body, restored, accepted a 25→37 mm edit with volume 44.4 cm³, and saved/reopened. [NativeAcceptance.json](../../../re/Fusion/LocalOracle/PrismHistory/NativeAcceptance.json) records those history boundaries. It does not establish whole native rectangle-container conversion or acceptance of a newly authored rectangle Design graph.

All nine scoped Python modules passed Black formatting, repository steering compliance, mypy, Ruff and Pyright. No local tests, product execution or native calls were performed for this integration. Remote and native document acceptance remain separate evidence.
