# Convert neutral blank drawings from the command line

`kit convert layout.json layout.SLDDRW` sends an authored standalone blank drawing through the ordinary native SOLIDWORKS writer. The destination suffix selects it automatically. `--to solidworks.slddrw` selects the same route explicitly.

The general portability check accepts a typed drawing sheet's own editable content as layout intent. Geometry and assemblies continue through their existing history checks. The SOLIDWORKS writer applies the same standalone ANSI A admission to both command routes. The command checks conversion policy before publishing output and reports the actual destination format.

Process coverage exercises suffix selection, explicit format selection, layout readback and refusal of unsupported paper with an existing destination. The writer's [held-out native verification](../../../../../../re/solidworks/measurements/2026/SdkPublicBlankDrawingHeldout01.json) covers open, rebuild, scale edit, save and fresh reopen. [Adapter guide](../../../../../Reference/Adapters/Solidworks.md#writing-standalone-blank-drawings)
