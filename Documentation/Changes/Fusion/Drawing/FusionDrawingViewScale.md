# Drawing view scale is written in the DWG

## Problem

Kit had no recorded evidence that a view scale it writes reaches Fusion. The scale is not a drawing
member: it lives in the embedded DWG, in a `DRAWINGVIEW` field and in a `SCALE` object that must
agree.

## Change

The finding is recorded, with a control and a case that differ in one input, in the
[view scale gotcha](../../../Gotchas/Conversion/Fusion/Drawing/FusionDrawingViewScale.md).

`BuildViewScaleCase.py` rewrites `DRAWINGVIEW.ViewScale` and the matching `SCALE` object on
`D1FreshLayout`, re-emits the DWG, and rebuilds the F2D and the F3Z.
`BeginUploads.py` reads the plan file it writes.

## Behavior

| Case            | Change                       | First view scale | Open    |
| --------------- | ---------------------------- | ---------------- | ------- |
| `C19ControlRaw` | none, the source bytes       | `4.0`            | 4.9 s   |
| `C22ViewScale2` | `ViewScale` and `SCALE` to 2 | `2.0`            | 240.6 s |

Both opened in local Fusion 2706.1.17 with views `[5, 4, 4]`, one dimension and a 420 by 297 mm
sheet. The two views that refuse a scale read do so in the control as well.

No reader or writer code changes. The edit keeps the document's own header tail valid because the
checksum covers the header area and not the view objects.

## Verification

`C22ViewScale2` was built from `D1FreshLayout` by rewriting three `DRAWINGVIEW` objects and one
`SCALE` object, then re-emitting the DWG. The emitted DWG reads back with `ViewScale` `2.0` on all
three views, and Fusion reported `2.0` for the active sheet's first view.

The control is the untouched source bytes, opened through the same path, which reported `4.0`.

## Limits

Only the active sheet's first view reports a scale through the Fusion API, so the control covers one
view of thirteen.

The open took 240.6 s against 4.9 s, because Fusion regenerates the view geometry. A run that changes
a scale needs a stall budget above that, or it reports a stall for a file that is still working.
