# The full ellipse sketch seam differs from the solid rim seam

## Expectation

A full saved ellipse and its extruded cap rim appear to use the same seam.

## Actual behavior

The ordinary SOLIDWORKS 2026 sketch stores a separate point for both segment endpoints. The point owns a mapped ellipse handle, and its observed phase is approximately 17 degrees for both disclosed shapes and their edited saves. The COM-observed full-period cap rim starts at the major point, at 0 degrees.

## Workaround

Read the sketch seam from the actual `sgSegment` endpoint indices and resolve its `sgEllipseHandle`. The cap rim trim retains its own parameterization. A source constructor needs independent evidence for the sketch seam producer. [Archive and native measurements](../../../../../../re/solidworks/records/EllipseBlindBossArchive2026.md#seam-rule-and-remaining-authority)
