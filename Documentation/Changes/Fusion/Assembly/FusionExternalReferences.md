# Read and write external component references

`ReadDocument` and `EmitParsed` now read and write Fusion designs that contain external component references.
The typed model keeps every link structure that Fusion writes into an F3D archive.
The writer emits these structures again from the typed values.

## Typed link structures

| Structure | Location | Typed model | Content |
| --- | --- | --- | --- |
| Root link table | Root `Manifest.dat` | `RootManifest.Links`, `ManifestLink` | Link GUID, three local paths and named text properties |
| Root ancestry | Root `Manifest.dat` | `RootManifest.Ancestry` | Ordered GUID list before the link table |
| Root lineage | Root `Manifest.dat` | `RootManifest.Lineage` | Display name and lineage URN, or `None` for an export terminal |
| Asset link rows | Asset `Manifest.dat` | `AssetHeader.Links`, `AssetLink` | Link GUID, target asset, target snapshot, link word and physical GUID |
| Version contexts | Each `MetaStream.dat` | `MetaSegment.Contexts`, `MetaContext` | Token, link GUID, revision, version URN, asset and segment number |
| Cross-document reference | Entity payloads | `CrossRef` | Object number, context token and target class GUID |

The root link properties are `LineageId`, `LineageUrn`, `toDocDisplayName`, `URL` and `linkedAssetGUID`.
A link that existed at a cloud save also has `linkClassification` with the value `OriginalDesign`.
`linkedAssetGUID` equals the `AssetId` of the asset link row with the same link GUID.

Each segment has one version context for each link.
The Design and Browser segments use the same token for a link, with segment number 0.
The ACT segment uses a different token for the same link, with segment number 1.
Each `CrossRef` token in a segment equals one context token of that segment.

## Cross-document references

The observed reference form has 60 bytes.
The reader also accepts a 37-character class text, which gives 61 bytes.

| Offset (bytes) | Size (bytes) | Value |
| --- | --- | --- |
| 0 | 1 | Presence flag `01` |
| 1 | 8 | Object number in the target segment |
| 9 | 1 | Cross-document flag `01` |
| 10 | 8 | Version context token |
| 18 | 1 | Separator `00` |
| 19 | 4 | ASCII length, 36 |
| 23 | 36 | Target class GUID text |
| 59 | 1 | Terminator `00` |

cadmpeg describes a second inline-typed form of 51 bytes.
Kit did not find this form in 15 native controls, 1,004 study F3D files or the example1 bundle members.
`ReadRefMut` raises `ValueError` for that form.

## New native classes

| Class | Segment | Schema version | Source |
| --- | --- | --- | --- |
| `XRefManager` | Design | 2 | Fusion schema dump |
| `DcXRefPCIFeature` | Design | 3 | Fusion schema dump |
| `DcPlaceComponentInstance` | Design | 2 | Native catalog base chain |
| `DcAssemblyFeature` | Design | 0 | Native catalog base chain |
| `ACTRefdTable` | ACT | 1 | Fusion schema dump and ACT payload replay |

The graphics frame of an external instance has a third link flag, `RenderFrame.HasEmptyLink`.
`SelectabilityAttribute` links an `AlphaImageSelectionQualifier` that holds one optional image path.
A set link flag that a callback payload follows raises `ValueError`.

## Evidence

The [link control script](../../../../re/Fusion/LocalOracle/LinksConfigs/CreateLinkControls.py) made two parts, one subassembly and one root assembly in Fusion 2706.1.17.
The script exported each state, saved each design to the acceptance project and closed every document.

| Control | State | Links | Contexts in each segment | `CrossRef` count (Design, ACT, Browser) |
| --- | --- | --- | --- | --- |
| `R0_empty` | Empty root | 0 | 0 | 0, 0, 0 |
| `R1_part_a` | Part A at 30° about Z, translation (5, 2, 1) cm | 1 | 1 | 2, 2, 6 |
| `R2_grounded` | Part A grounded | 1 | 1 | 3, 2, 6 |
| `R3_nested` | Subassembly at 90° about X, translation (0, 6, 0) cm | 2 | 2 | 5, 4, 12 |
| `R4_joint` | Rigid as-built joint | 2 | 2 | 5, 4, 12 |
| `R5_saved` | Root after cloud save | 2 | 2 | 5, 4, 12 |
| `R6_out_of_date` | Part A version 2 exists | 2 | 2 | 5, 4, 12 |
| `R7_updated` | After `updateAllReferences` | 2 | 2 | 5, 4, 12 |
| `R8_updated_saved` | Root version 2 | 2 | 2 | 5, 4, 12 |
| `R9_archive` | Archive export of the saved root | 2 | 2 | 5, 4, 12 |
| `S0_inserted` | Part B at translation (1, 2, 0) cm | 1 | 1 | 2, 2, 6 |
| `S1_saved` | Subassembly after cloud save | 1 | 1 | 2, 2, 6 |

[`LinkEvidence.json`](../../../../re/Fusion/LocalOracle/LinksConfigs/LinkEvidence.json) records the native and sanitized SHA-256 values of all 14 fixtures.
For each fixture, the model read again from the Kit output equals the original model.
All members are byte-identical except `.protein` members and the part `.smb` and `.smbh` members.
The existing codecs regenerate these three member kinds.

## Tests

`tests/convert/formats/FusionCodec/Links` contains the new cases.
`LinkArchiveTests.py` replays the 14 fixtures and checks the link, context and token relations.
`LinkWireTests.py` checks synthetic root links, contexts, references, `Properties.dat` and `RedirectionsStream`.
The cases did not run locally.
They require Python 3.14 for ZIP method 93.

## Limits

Kit does not author a new assembly that references other designs.
The [data model draft](../../../../re/Fusion/Reconstruction/LinksConfigs/DataModelSection.md) lists the records that such an assembly needs.
The `ACTRefdTable` field split is an inference from the schema dump.
The fields are an entry map, a revision GUID, an asset, an asset GUID, a link name and a revision map.

## Related information

- [Dependency graph change](FusionDependencyGraph.md)
- [Configuration boundary](../Configuration/FusionConfigurationBoundary.md)
- [Link renewal gotcha](../../../Gotchas/Conversion/Fusion/Assembly/FusionLinkRenewal.md)
