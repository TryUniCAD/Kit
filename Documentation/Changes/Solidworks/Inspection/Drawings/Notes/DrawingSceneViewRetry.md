# Retry the drawing scene-view diagnostic with its concrete override

The first disclosed observer run retained all 16 guarded memory snapshots but stopped during the native source's post-redraw repeated `GetFirstView` call. The new receipt preserves that failure, healthy controls and the exact equal-versus-unknown boundary.

A fresh private successor source-binds the actual `uiDrawingView_c` getter in `slddrwu.dll` while retaining the original `slduiu` branch and every traversal/read guard. Its ordinary helper obtains one fresh sheet-view/annotation collection per state, preserving all existing checks. It does not retry or suppress COM errors. Complete memory comparisons and complete ordinary verification are reported independently; a COM failure still yields exit 3.

Static preparation parsed 18 tools, preserved all 15 earlier hashes and verified two native leaf bodies, two RTTI spans and the actual virtual cell. The note geometry assertions were retained by AST comparison. No runtime or local tests were executed here, and native/rendering/full-source qualification remains pending.

[Exact findings and retry limits](../../../../../../re/solidworks/records/DrawingSceneViewRetry2026.md)

[Preparation receipt](../../../../../../re/solidworks/measurements/2026/DrawingSceneViewRetryPreparation01.json)

[Repeated sheet-view API gotcha](../../../../../Gotchas/Conversion/Solidworks/Oracle/Drawings/RepeatedDrawingSheetViewReadCanFail.md)
