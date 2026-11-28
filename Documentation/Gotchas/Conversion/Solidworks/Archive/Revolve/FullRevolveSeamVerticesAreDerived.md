# Full revolve seam vertices are derived

The full native annular revolve exposes four public B-rep vertices, but its complete active partition transmits zero VERTEX and POINT records. Each native closed circle has a null endpoint vertex and its own actual edge/curve owner. The existing decoder creates one deterministic seam vertex per edge at circle parameter zero.

A prism's fixed six-face, four-fin-loop and eight-native-vertex checks cannot qualify that body. Adding CIRCLE/CYLINDER declarations alone does not repair the ownership proof. Conversely, inventing native vertex IDs from the public count incorrectly turns derived seam geometry into transmitted native data.

Keep the native zero-vertex inventory. Verify all actual faces, loops, fins, edges and analytic carriers, then independently check the existing edge-derived seam IDs, both endpoint associations and `centre + radius * x_axis`. Preserve the distinction in provenance and public binding.

[Source and schema evidence](../../../../../../re/solidworks/records/SdkRevolveBodyNames2026.md) · [Guarded process receipt](../../../../../../re/solidworks/measurements/2026/SdkRevolveBodyNamesProcess01.json)
