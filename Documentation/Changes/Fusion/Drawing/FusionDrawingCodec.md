# Typed Fusion drawing documents

Kit adds a reader and a writer for Fusion drawing documents under `convert.formats.Fusion.DrawingCodec`.

| API                                                     | Result                                                   |
| ------------------------------------------------------- | -------------------------------------------------------- |
| `ReadDrawing(DataValue, InflateZstd=None)`              | `FusionDrawing` from a modern or historical F2D          |
| `EmitDrawing(Value, CompressZstd=None)`                 | F2D bytes from a `FusionDrawing`                         |
| `ReadDrawBundle(DataValue, InflateZstd=None)`           | `DrawingBundle` from a drawing-root F3Z                  |
| `EmitDrawBundle(Value, CompressZstd=None)`              | F3Z bytes from a `DrawingBundle`                         |
| `RouteBundle(DataValue, InflateZstd=None)`              | `DrawingBundle` for an F2D root, else `FusionBundle`     |
| `ReadInventory(Content)`                                | `DwgInventory` with the DWG header, pages and classes    |

## Behavior

`FusionDrawing` holds typed root and asset manifests, both entity segments, the sheet layout and the nine automation settings.
It also holds images, properties, component references, the historical redirection table and the exact entry layout.
The modern segments decode to typed entity records through a native drawing vocabulary of 14 class schemas.
The historical segment keeps framed records, because its class profiles are older than the reflected schemas.

The embedded DWG is a `DrawingDatabase` with its member name and bytes.
The reader requires that name to equal `ExtFileSerializer.persistedFileName` in the drawing segment.
Kit does not decode or write DWG objects.

The [data model section](../../../../re/Fusion/Reconstruction/Drawings/DataModelSection.md) describes the members, manifests, classes and joins.

## DWG authority

The DWG is the authoritative store of sheets, views and annotations.
Fusion does not regenerate it from the segments.
On open, Fusion gives the drawing engine the embedded DWG and a SAB export of the referenced body.
The engine recomputes view curves from that body, so a model edit updates the views.

Native runs in Fusion 2706.1.17 tested this with altered packages.

| Variant          | Package change                       | Fusion result                                      |
| ---------------- | ------------------------------------ | -------------------------------------------------- |
| `P4ViewsControl` | None, A0 control                     | Opened with 3 views and 0 dimensions               |
| `P2NoDwg`        | A1 control without its DWG member    | Error dialog `Cannot find the specified drawing file` |
| `P3SwappedDwg`   | A1 segments with the A0 DWG          | No drawing engine session within 207 seconds      |
| `P5ReverseSwap`  | A0 segments with the A1 DWG          | Opened with 3 views and the 1 dimension of the A1 DWG |

Kit therefore does not author drawings from typed values.
A new drawing needs DWG view and annotation objects, and Kit does not decode or write DWG objects.
`EmitDrawing` writes the DWG member as the bytes that `ReadDrawing` returned.

## Verification

`ReadDrawing` and `EmitDrawing` reproduce these inputs byte for byte.

| Input                          | Bytes   | SHA-256 prefix |
| ------------------------------ | ------- | -------------- |
| A0 views control F2D           | 123,711 | `1914355f`     |
| A1 dimension control F2D       | 127,179 | `9a13d8b7`     |
| A2 automatic dimension F2D     | 140,651 | `f38fec3f`     |
| Historical example F2D         | 103,817 | `33589d0e`     |
| Historical example F3Z bundle  | 200,292 | `4e67c7a5`     |

The tests in `tests/convert/formats/FusionCodec/Drawings` use normalized fixtures without the DWG.
They cover the package, parts, manifests, bundles, the DWG inventory and the typed segment facts.

Native runs in Fusion 2706.1.17 gave these results.

| Check                                   | Result                                                        |
| --------------------------------------- | ------------------------------------------------------------- |
| Kit-emitted A1 drawing opens            | Same sheet, views, curves and dimension as the saved control  |
| Model edit from 40 mm to 60 mm          | Base view width 160 mm before and 240 mm after the update     |
| Reference after `updateAllReferences()` | Version 2, not out of date                                    |
| Fusion save and reopen after the edit   | Not verified, because the Personal license kept files read-only |
| New drawing authored by Kit             | Not supported, because Kit does not write DWG objects         |

The [acceptance report](../../../../re/Fusion/Reconstruction/Drawings/NativeAcceptance.json) records every run with normalized names.
