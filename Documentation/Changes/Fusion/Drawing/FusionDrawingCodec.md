# Typed Fusion drawing documents

Kit adds a reader, a writer and an author for Fusion drawing documents under `convert.formats.Fusion.DrawingCodec`.

| API                                                     | Result                                                   |
| ------------------------------------------------------- | -------------------------------------------------------- |
| `ReadDrawing(DataValue, InflateZstd=None)`              | `FusionDrawing` from a modern or historical F2D          |
| `EmitDrawing(Value, CompressZstd=None)`                 | F2D bytes from a `FusionDrawing`                         |
| `ReadDrawBundle(DataValue, InflateZstd=None)`           | `DrawingBundle` from a drawing-root F3Z                  |
| `EmitDrawBundle(Value, CompressZstd=None)`              | F3Z bytes from a `DrawingBundle`                         |
| `RouteBundle(DataValue, InflateZstd=None)`              | `DrawingBundle` for an F2D root, else `FusionBundle`     |
| `ReadInventory(Content)`                                | `DwgInventory` with the DWG header, pages and classes    |
| `Dwg.ReadDwgFile(Content)`                              | Typed `DwgFile` with every section and object            |
| `Dwg.EmitDwgFile(DwgModel)`                             | DWG bytes from a `DwgFile`                               |
| `Dwg.Author.AuthorDwg(Draft)`                           | New DWG bytes from a `DwgDraft`                          |
| `Author.BuildDrawing(SpecValue, Database)`              | New `FusionDrawing` from a `DrawingSpec` and its DWG     |
| `Author.BuildBundle(SpecValue, Drawing, DesignData)`    | New drawing-root `DrawingBundle` with the referenced design |
| `Author.MakeIdentity()`                                 | Fresh document, version and lineage identities           |
| `Author.CheckSpec(SpecValue, Database)`                 | Raises `ValueError` for an inconsistent drawing spec     |

## Behavior

`FusionDrawing` holds typed root and asset manifests, both entity segments, the sheet layout and the nine automation settings.
It also holds images, properties, component references, the historical redirection table and the exact entry layout.
The modern segments decode to typed entity records through a native drawing vocabulary of 14 class schemas.
The historical segment keeps framed records, because its class profiles are older than the reflected schemas.

The embedded DWG is a `DrawingDatabase` with its member name and bytes.
The reader requires that name to equal `ExtFileSerializer.persistedFileName` in the drawing segment.
`ReadDwgFile` decodes those bytes into header variables, classes, objects and every other section.
`EmitDwgFile` writes them back from the typed values.
The [Open Design Alliance DWG specification](https://www.opendesign.com/files/guestdownloads/OpenDesign_Specification_for_.dwg_files.pdf) is the format reference.

| DWG                  | Bytes   | Objects | Fully typed | Typed common data only | Re-emission   |
| -------------------- | ------- | ------- | ----------- | ---------------------- | ------------- |
| A0 views control     | 126,690 | 1,958   | 1,891       | 67                     | Byte for byte |
| A1 dimension control | 129,413 | 1,993   | 1,920       | 73                     | Byte for byte |
| A2 automatic control | 146,068 | 2,133   | 2,066       | 67                     | Byte for byte |
| Historical example   | 110,873 | 900     | 865         | 35                     | Byte for byte |

The objects with typed common data only are AutoCAD Mechanical objects in the controls.
In the historical example, they are its `ACDBIDWSTREAM`, `ACDBIDWVERSION` and `ACDBSYNERGYMAPPINGS` objects.

The [data model section](../../../../re/Fusion/Reconstruction/Drawings/DataModelSection.md) describes the members, manifests, classes, DWG objects and joins.

## DWG authority

The DWG is the authoritative store of sheets, views, view curves and annotations.
Fusion does not regenerate it from the segments.
On open, Fusion gives the drawing engine the embedded DWG and a SAB export of the referenced body.
The engine shows the view curves that the DWG stores.
It recomputes them when `updateAllReferences()` updates an out-of-date reference.

Native removal variants define the minimal state of a drawing.
Fusion needs the DWG member, a view rep object for each view, contiguous section ids and handles that name present objects.
It does not need the stored view curves, the title block, the border, AutoCAD Mechanical objects or the data-store section.
The [data model section](../../../../re/Fusion/Reconstruction/Drawings/DataModelSection.md) lists each variant.
The [section id gotcha](../../../Gotchas/Conversion/Fusion/Drawing/FusionDrawingSectionIds.md) records the section rule.

## Authoring

`AuthorDwg` builds a new DWG from a `DwgDraft` without any source DWG bytes.
The draft names the sheet, the title block texts, the views, the view source and the dimensions.
Kit writes every object from typed values and an ISO standard of typed rows.
The caller supplies the fingerprint and version GUIDs and the save moment.
The view blocks stay empty, because Fusion recomputes view curves on a reference update.

`BuildDrawing` builds the F2D members around that DWG from a `DrawingSpec`.
`BuildBundle` builds the drawing-root F3Z with the referenced design.

Fusion 2706.1.17 did not finish opening any drawing with a Kit-authored DWG.
The open waits without a dialog until Fusion is stopped.
Two parts of the authored DWG cause the wait.

| Cause                                   | Evidence                                                    |
| --------------------------------------- | ----------------------------------------------------------- |
| Four header values after the handles    | Zero, Kit-chosen and foreign values each stalled an otherwise Fusion-saved DWG. With the saved values kept, a change to one header variable also stalled it |
| Missing Autodesk trusted-file text      | The open stalled when neither AppInfo nor `AcDb:AppInfoHistory` carried the text, and opened when AppInfo carried it next to Kit's product entry |

The four values depend on the header variables, both data and strings.
They do not cover the objects, the other sections or the F2D members.
No unkeyed CRC, Adler, digest or seeded generator reproduces them in 31 Fusion saves.
The trusted-file text states that an Autodesk application saved the file.

The [header tail gotcha](../../../Gotchas/Conversion/Fusion/Drawing/FusionDrawingHeaderTail.md) and the [authored shell gotcha](../../../Gotchas/Conversion/Fusion/Drawing/FusionDrawingAuthoredShell.md) record the bisection runs.
Kit does not copy Fusion-written header values into an authored file.
Kit never writes the trusted-file text.
Kit therefore has no rule that makes Fusion 2706.1.17 open an authored DWG.

The F2D author works on its own.
`N2AuthoredF2d` put Kit-built members around a Fusion-saved DWG, and it opened with 3 views and 1 dimension.

## Verification

`ReadDrawing` and `EmitDrawing` reproduce these inputs byte for byte.

| Input                          | Bytes   | SHA-256 prefix |
| ------------------------------ | ------- | -------------- |
| A0 views control F2D           | 123,711 | `1914355f`     |
| A1 dimension control F2D       | 127,179 | `9a13d8b7`     |
| A2 automatic dimension F2D     | 140,651 | `f38fec3f`     |
| Historical example F2D         | 103,817 | `33589d0e`     |
| Historical example F3Z bundle  | 200,292 | `4e67c7a5`     |

The tests in `tests/convert/formats/FusionCodec/Drawings` use normalized fixtures without the captured DWG.
They cover the package, parts, manifests, bundles, the DWG inventory, the typed segment facts and the authored DWG.

Native runs in Fusion 2706.1.17 gave these results.

| Check                                   | Result                                                        |
| --------------------------------------- | ------------------------------------------------------------- |
| Kit-emitted A1 drawing opens            | Same sheet, views, curves and dimension as the saved control  |
| Model edit from 40 mm to 60 mm          | Base view width 160 mm before and 240 mm after the update     |
| Reference after `updateAllReferences()` | Version 2, not out of date                                    |
| Kit-built F2D around a Fusion-saved DWG | Opened in 4.3 s with views of 5, 4 and 4 curves and 1 dimension |
| Kit-modified DWG with Fusion header values | Opened in 3.3 s to 6.1 s with 3 views and 1 dimension      |
| Same, with one header variable changed  | Open had not finished after 61 s                              |
| Same, with no trusted-file text left    | Open had not finished after 61 s                              |
| Kit-authored DWG                        | Open had not finished when stopped after 121 s to 602 s       |
| Authored view recompute and model edit  | Not run, because no authored drawing opened                   |
| Fusion save and reopen after an edit    | Not run, because the Personal license kept every upload read-only |

The [acceptance report](../../../../re/Fusion/Reconstruction/Drawings/NativeAcceptance.json) records every run with normalized names.
