# Present sketch caches can have no saved records

A nonzero drawing view `has_fb50` does not imply populated sketch-cache records or annotations. The native serializer stores pointer presence separately from the saved record count.

The exact 2026 native helper emits zero when the record container is absent and filters internal records before counting. Both disclosed original drawing views have a present cache and exactly `fb50 = {n: 0}`. Treating pointer presence as a populated-cache test rejected understood saved state. Treating saved count zero as absent would erase source state.

Retain presence and saved count separately on the actual view. Accept the proven zero-record body, preserve its pointer flag and reject populated or unexplained payloads. Do not transplant fresh constructor absence onto a saved input or infer that its runtime container was physically empty.

The [native field proof](../../../../../../re/solidworks/records/DrawingViewRendering2026.md) gives exact function bounds and count filtering. The [process receipt](../../../../../../re/solidworks/measurements/2026/DrawingViewRenderingRead01.json) binds complete read/store variants, original raw preservation and malformed-body rejection. Full original Definition admission remains blocked by the separate sheet-annotation guard.
