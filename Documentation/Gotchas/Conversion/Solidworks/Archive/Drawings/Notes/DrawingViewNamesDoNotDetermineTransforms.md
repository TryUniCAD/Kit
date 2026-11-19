# Drawing view names do not determine transforms

Expectation: ten views named `*Full Sheet` and `Unused` imply identity transforms, or saved ANSI standard zero implies the standard-zero dimetric branch.

Actual: all four disclosed note originals/edits have those drawing names and identity transforms, matching neither canonical part-view branch. The generated note's native-saved derivative acquires the same names while retaining every `MakeStdViews(1)` matrix exactly. At index nine its alternate-branch residual is `0.35355339067438263`.

Read names, IDs, matrix-presence branches, primary transforms and secondary transforms independently. Preserve the actual drawing constructor/refresh policy; do not recompute transforms from the saved standard or infer runtime initialization order. See [the complete comparison](../../../../../../../re/solidworks/records/DrawingPlainNotePresentation2026.md) and [native view rules](../../../../../../../re/solidworks/records/StandardViewsConstruction2026.md). This observation does not qualify a drawing writer.
