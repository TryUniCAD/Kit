# A saved Kit root ends its Design stream with padding

## Expectation

Each record of a Design `BulkStream.dat` ends where the next record starts.
The last record ends at the end of the stream.

## Actual behavior

Fusion saved the uploaded Kit root `KitAsmRoot` as version 2.
Each Fusion export of that version ends the Design stream with 10 bytes after the last record.
The last record is the continuation of a new `VisualAnalyses` record, which Fusion added on save.
That continuation has 5 bytes of fields, as in native designs.

| Export | Design stream bytes | Last 10 bytes |
| --- | --- | --- |
| `AcceptedKitAsmRoot.f3d` | 17,946 | `0000000000000000c7cb` |
| `ReexportFirstKitAsmRoot.f3d` | 17,946 | `35003600590048004400` |
| `ReexportSecondKitAsmRoot.f3d` | 17,946 | `35003600590048004400` |

The last two exports came from one opened document.
The bytes differ from the first export, so they are not record data.
The second value is the UTF-16 text `56YHD`.
In the native controls, the `VisualAnalyses` continuation is not the last record and has no extra bytes.

`ReadDocument` raises `Unexplained trailing Fusion entity payload bytes` for these exports.
Fusion itself opened, updated, saved and opened the root again without errors.

## Workaround

None in Kit.
Kit keeps the strict reader, because it cannot tell padding from unknown fields.
Use the Fusion API, not a Fusion export, to inspect a saved Kit root.

## Evidence

- [Assembly authoring acceptance](../../../../../re/Fusion/LocalOracle/LinksConfigs/AsmAcceptance.json), key `fusion_exports`
- [Export script](../../../../../re/Fusion/LocalOracle/LinksConfigs/ReexportAsmRoot.py)
- [Assembly authoring change](../../../../Changes/Fusion/Assembly/FusionAssemblyAuthoring.md)
