# Fillet selection uses a different handle mode

## Expectation

A known mode-1 rectangular stock reference can initialize a fillet's selected edge using the ordinary downstream constructor's zero handle.

## Observed behavior

That constructor has a zero `f70` with `fe8=0x300`. All four disclosed SOLIDWORKS 2026 SP05.2 fillet selections instead have `fe8=0x200` and a varying nonzero `f70`. Their separately measured prior edge transmit slots also differ from the saved handle. [Downstream constructor](../../../../../../re/solidworks/records/DownstreamPrismEdgeConstructors2026.md#constructor-and-retention) · [Fillet observations](../../../../../../re/solidworks/records/EdgeFilletColdPlan2026.md#model-owners-and-unresolved-construction)

## Workaround

Keep selection incidence and saved handle state separate. Require evidence from the actual fillet constructor or a controlled native contrast before emitting a fresh handle in this mode.
