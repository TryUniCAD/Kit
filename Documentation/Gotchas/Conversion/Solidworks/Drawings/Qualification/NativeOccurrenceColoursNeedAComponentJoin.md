# Native occurrence colours need a component join

A typed drawing colour-map row is not yet a resolved portable component appearance. The 2026 accessor identifies the key as a signed native occurrence number and the value as an unsigned colour word; the rows themselves contain no tagged object reference.

Preserve every key, word and count. Expose `drawing.occurrence_colours` as unprojected until the native occurrence-to-child component association and colour interpretation are proved. Do not label the key a feature ID, infer RGB encoding, copy an observed colour as a default or discard the row because it is a cache.

The [native owner proof](../../../../../../re/solidworks/records/DrawingViewRendering2026.md) and [exact-source process receipt](../../../../../../re/solidworks/measurements/2026/DrawingViewRenderingRead01.json) cover retention and integer domains. They do not establish a portable appearance join or full original drawing qualification.
