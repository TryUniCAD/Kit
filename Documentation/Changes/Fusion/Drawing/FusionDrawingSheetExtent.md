# Drawing sheet extent comes from the DWG layout

## Problem

Kit wrote the drawing sheet extent into the drawing members, which is where the sheet name, size,
standard and units live. A drawing whose member said A1 still opened in Fusion as A3, so the member
is not the value Fusion uses.

The extent is duplicated. The `LAYOUT` object inside the embedded DWG carries `PaperWidth`,
`PaperHeight` and `PaperSize`, and Fusion reads the sheet from there.

## Change

The finding is recorded, with two controls that change one input each, in the
[sheet extent gotcha](../../../Gotchas/Conversion/Fusion/Drawing/FusionDrawingSheetExtent.md).

Two research builders reproduce the controls:

| Builder                | Change                                        |
| ---------------------- | --------------------------------------------- |
| `BuildSheetCase.py`    | the drawing member only, A3 to A1             |
| `BuildLayoutCase.py`   | the DWG `LAYOUT` object only, A3 to A1        |

`BeginUploads.py` reads the two plan files they write.

## Behavior

| Case            | Change                  | Fusion sheet_mm  |
| --------------- | ----------------------- | ---------------- |
| `C20SheetA1`    | member only             | `[420.0, 297.0]` |
| `C21LayoutA1`   | `LAYOUT` only           | `[841.0, 594.0]` |

Both opened in local Fusion 2706.1.17 with views `[5, 4, 4]` and one dimension.
The layout case opened in 4.9 s.

No reader or writer code changes. The layout edit keeps the document's own header tail valid because
the checksum covers the header area and not the layout objects.

## Verification

`C21LayoutA1` was built from `D1FreshLayout` by rewriting one `LAYOUT` object and re-emitting the DWG
with `EmitDwgFile`, then rebuilding the F2D and the F3Z. The emitted DWG reads back with
`841.0 x 594.0` and `ISO_full_bleed_A1_(841.00_x_594.00_MM)`, and Fusion reported the same extent.

`C20SheetA1` changed only the member and Fusion reported the old extent, which is what makes the
layout the authority rather than a coincidence.

## Limits

The corpus holds 247 Fusion-saved drawings and all are A3 Landscape, so a corpus comparison cannot
separate a read value from a constant. The two controls are the evidence.

A sheet change that keeps the member and the layout out of step is untested. Keep them equal.
