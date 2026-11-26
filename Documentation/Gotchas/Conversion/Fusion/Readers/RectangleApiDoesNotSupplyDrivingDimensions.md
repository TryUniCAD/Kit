# Rectangle API coordinates do not supply driving dimensions

## Expectation

A rectangular profile authored through the Fusion API can appear to contain explicit driving width and height dimensions.

## Observed behavior

All 48 discovery variations in PR #263 had zero native geometric constraints and zero native linear dimensions.
Their authoring program supplied corner coordinates through `addTwoPointRectangle`, then created an extrusion.
The new [native controls](../../../../../re/Fusion/RectangleRecovery/README.md) confirm that a valid unconstrained profile can still have editable extrusion depth.
The previous reverse and YZ projection guards required the separately proved constrained profile.

## Workaround

Read the actual native constraint and parameter collections.
Preserve their absence when projecting an unconstrained source.
Use explicit constraints and named driving dimensions when authoring a fully constrained control.
Do not infer nonexistent dimensions from corner coordinates or remove geometry checks to admit a source.
