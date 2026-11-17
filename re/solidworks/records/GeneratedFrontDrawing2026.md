# Generated ordinary front drawing trial

The research builder emits a version-4 SLDDRW and its SLDPRT from one authored request. The drawing carries one unformatted ANSI A sheet and one explicit 1:1 front view of the generated rectangular blind boss. The view, references and both drawing headers come from the same typed drawing graph. The seven package roles follow the generated blank drawing. This candidate inherits the blank UI state and derives the cosmetic-thread presence field. [Complete view object](DrawingAbsoluteViewFields2026.md) · [Blank drawing ancestry](GeneratedBlankDrawing2026.md) · [Candidate receipt](../measurements/2026/GeneratedFrontDrawingCandidate01.json)

## Drawing indexes

| Stream field | Source and wire rule | Evidence |
| --- | --- | --- |
| `swXmlContents/KeyWords`, `View.Name` | The generated view's node name. | `moCadDissecterHelper_c::CollectKeywordStream` in `sldmodu.dll` at `0x4cac4640` selects the view callback through vtable slot `0x3e8` at `0x4cac47ff`. `moDrView::SerializeXmlData` at `0x4c98aa10` makes the name call at `0x4c98aac0` and exports it at `0x4c98acfc`. |
| `View.Description` and `View.id` | Selected model configuration name and local configuration ID. Both are taken from the actual generated part through the internal reference. [Keyword ID gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Drawings/DrawingViewKeywordIdIsConfigurationId.md) | Resolved model `0x4c98ab14–0x4c98ab37`, selected configuration methods at `0x4c98ab5a` and `0x4c98abf5`, text and decimal publication at `0x4c98ad48–0x4c98ad82`. |
| `View` text | Referenced part stem with the native lowercase `.sldprt` suffix. The same text and attributes go in the top-level catalogue and its owning sheet. | Model type getter at `0x4c98ab7c`, part suffix literal at `0x4cdd2220` and publication at `0x4c98ad22`. Both ordinary disclosed drawings agree in the two XML locations. |
| `docProps/ISolidWorksInformation.xml`, `SW-Config-Model-View-Sheet-List` | One model view token `1:@@<configuration name>@<local configuration ID>@<absolute linked part path>@<view name>@<sheet name>`. | `slddrwu.dll` enumerates actual view links from `0x3defe090`. `0x3defe491` and `0x3defe4b9` obtain the configuration identity. The property value is published at `0x3defecb7–0x3defecfd`. The two locked disclosed drawings have matching token and typed Definition values. |

The two DLLs come from SOLIDWORKS SP05.2 build `34.5.2.0604`. Their SHA-256 hashes are `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e` for `sldmodu.dll` and `61c8481374431866f97416ce5109329f9c38e7e85b56a9f95d41bdf3122cdc47` for `slddrwu.dll`. The drawing model archive version remains 19000. Other releases require their own format and application qualification. [Adjacent-release procedure](AdjacentReleaseQualification.md)

The generated `Contents/Definition` has an empty detailing edge map. Both disclosed front drawings separately opened, edited, saved and reopened without that map. Their saved derivatives retained the omission. The generated pair has no projected-edge cache or packaged display indexes. The native trial includes a reduced control with this exact seven-role stream inventory and the same map omission to measure those dependencies together. [Native edge omission receipt](../measurements/2026/DrawingFrontDetailingMapOmission01.json) · [Disclosed source lock](../v2026/heldout/DrawingSourceLock01.json)

## Reproduce the offline build

The stdin request supplies the authored drawing, part and view fields used by the [complete view record process](DrawingAbsoluteViewFields2026.md). Both file identities use absolute Windows paths and authored file stems. The script returns one JSON report with hashes, stream extents and the two base64 artifacts. Save it to a private location outside the checkout.

```sh
uv run --isolated --frozen --extra dev --python 3.11 python -B \
  re/tooling/sw2026/DrawingFrontBundleProcess.py < /private/authored-front-drawing.json
```

Both authored requests passed the full SDK `open_document` inspection with `strict=False`, using the generated container and native metadata. The typed decode re-encoded Definition and Header2 exactly. The readback verified the part link and configuration against the generated child's actual configuration manager. The default strict drawing route rejected the frozen trial file. View and configuration names containing the index delimiter failed before output. The earlier generated blank with the cosmetic-thread correction retained its exact container SHA and all seven stream hashes.

## Native trial packet

```sh
uv run --isolated --frozen --extra dev --python 3.11 python -B \
  re/tooling/sw2026/PrepareGeneratedFrontDrawing.py /private/disclosed-source-lock \
  /private/authored-front-drawing.json /private/unused-packet \
  --windows-directory '\\Mac\Home\Documents\unused-packet\GeneratedInput'
```

The private preparer repeats the guarded build on the final encoded paths and requires identical output. It checks the disclosed D01 source and its native author and reopen receipts by hash. Its native control reduction retains the seven package roles and changes only the typed detailing map inside Definition. The private manifest records each file hash, expected observations from the authored geometry, source lock and tool identities. `Tools/InspectGeneratedFrontDrawing.py` accepts that manifest and its `--packet-sha256` and `--tools-sha256` arguments. `--verify-only` validates custody without starting a native session.

The guest measures clean open and rebuild, one live sheet and view, sixteen live feature-tree rows, view orientation and transform, model resolution and shape measurements. It edits the view position, checks translation and outline, saves and opens the derivative in a fresh process. The pristine control brackets the reduced and generated lanes. A held-out test awaits a qualified generated result. [Offline construction and frozen input hashes](../measurements/2026/GeneratedFrontDrawingCandidate01.json)

## Native result

Seven distinct pinned SOLIDWORKS processes measured the frozen pair and controls. The generated drawing opened with zero errors and warnings. It resolved the independently generated part and retained the named sixteen-row tree through the forced rebuild and view movement. The native body measured `2.304e-6 m³`, surface area `0.001248 m²` and centre of mass `(0.012, 0.008, 0.003) m`. Moving the view centre from `(0.08243, 0.09372) m` to `(0.085161, 0.091981) m` produced the independently expected outline and transform. The child, configuration and input hashes remained stable. [Native trial receipt](../measurements/2026/GeneratedFrontDrawingNative01.json)

The generated pair reached `SaveAs3` with the edited geometry and no rebuild problems. Native save returned `[false,1,0]` and left a zero-byte target. Fresh reopen was unavailable for the generated derivative. The reduced native lane and both bracketing controls completed clean edit, save and fresh reopen. The same generic error was observed in the earlier generated blank. The two failures still require localization inside the shared native save path. [Shared native save path](DrawingSaveBoundary2026.md)

The reduced native input started with the generated drawing's seven logical roles and no detailing buckets. Its saved derivative has 28 roles and a regenerated bucket with four edge entries. Its Definition and Header2 re-encode exactly. The full-package isolated edge-map omissions retained zero buckets on native save. The combined omission therefore changes regeneration behavior, with no assignment to a particular omitted stream. [Regeneration gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Drawings/DrawingDetailingMapRegenerates.md) · [Isolated map omission](../measurements/2026/DrawingFrontDetailingMapOmission01.json)
