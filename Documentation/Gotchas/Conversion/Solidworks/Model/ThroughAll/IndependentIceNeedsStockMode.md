# An independent ICE producer needs the stock operation

## Expectation

The common extrusion binder can select the operation from the concrete feature class when composing two independent solid stocks.

## Actual behavior

The binder infers a cut for `moICE_c` and sets `f810 = 1` with the additional cut flags. The disclosed `MovingStock` uses `moICE_c` with `f810 = 0` and the same basic extrusion flags as the first stock. It has its own blind depth, profile and output atom. [Binder](../../../../../../src/convert/adapters/solidworks/Archive/Construction/Extrusion/BindExtrusionMut.py#L10) · [Disclosed typed roles](../../../../../../re/solidworks/records/ThroughAllMultiStockArchive2026.md)

## Workaround

Use the authored operation to distinguish a second solid creation from a cut. Preserve the base flags, bind the actual profile and sole D1, and allocate a separate atom for that producer. The research graph reads back this mode and refuses the same class with the cut operation substituted. [Guarded construction and refusal evidence](../../../../../../re/solidworks/records/TwoStockColdOwnerGraph2026.md)
