# Pattern reversal cannot mirror its direction datum

## Expectation

A 45° plane about the intersection of Right and Top looked sufficient to supply positive X and Y travel to the disclosed one-direction pattern.

## Actual behavior

On SOLIDWORKS 2026 build 34.5.2.0604, the actual plane selected at mark 0 with the negative-Z hinge at mark 1 produced the through-origin normal `(1,-1,0)/√2`. The planned `(1,1,0)/√2` is orthogonal to that normal. Pattern reversal changes the sign of the travel vector. The failed source attempt reached this frame guard before pattern creation or a native save. [Measured source setup](../../../../../../re/solidworks/measurements/2026/LocalLinearPatternEnvelopeSetup01.json)

## Workaround

Check the actual plane origin and both vector signs against the selected model-space direction before creating the pattern. If the intended direction is on another normal line, choose the corresponding datum rotation or freeze a new geometry prediction before running the trial. [Directed hinge orientation](ObliquePlaneFlipDependsOnDirectedHinge.md) · [Pattern envelope contrast](../../../../../../re/solidworks/records/LocalLinearPatternEnvelopeContrast2026.md)
