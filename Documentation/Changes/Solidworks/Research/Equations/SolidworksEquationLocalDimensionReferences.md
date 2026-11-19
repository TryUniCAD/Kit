# Generate local dimension references for a SOLIDWORKS equation

The research builder creates a width-to-depth equation on an origin-anchored rectangular blind boss.
Each operand owns a separate dimension reference bound to its local part.
The corresponding sketch or feature still owns the original driving dimension.

Run [the builder](../../../../../re/tooling/sw2026/equations/BuildWidthDepthPart.py) from the checkout with `src`, `re/tooling/sw2026` and the checkout on `PYTHONPATH`.
Supply the neutral rectangular part, authored settings, rectangle dimensions and equation identifiers as JSON on standard input.
The builder writes the generated part to standard output and the construction receipt to standard error.
The current profile admits one local depth equal to half of the sketch width and uses printable ASCII dimension names.

Four guarded builds reproduce two ten-stream files with zero input reads after initialization.
Both Config-0 and ResolvedFeatures round-trip exactly with their linked map.
One candidate opens and rebuilds with one solid and an enabled equation.
The rebuild after the live width edit fails, and the recovery control passes.
The same-model plain part also loses its COM interface during post-edit observation.
The [research record](../../../../../re/solidworks/records/PartEquationConfig2026.md#local-dimension-reference-handles) links the constructor and native evidence.
The edit lifecycle, public equation writing and held-out acceptance remain open.
