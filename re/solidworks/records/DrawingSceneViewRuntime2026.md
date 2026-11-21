# Drawing scene-view runtime ownership in SOLIDWORKS 2026

The bounded retry passed. Four fresh native processes completed ordinary COM checks and all 16 guarded memory snapshots. Renderer correctness remains unresolved.

Task: DRAWING-NOTES-C10, PR #121. Owner: `flag_ownership`; root owns native execution, integration and publication. This record completes the prepared [scene-view retry](DrawingSceneViewRetry2026.md). It does not qualify the drawing writer or original-source conversion.

## Exact execution

The raw result SHA-256 is `c8a6b996e77acc44b5cb85b03ebd314dd86ac8b3b6010553acf74364a28d1109`. The frozen job SHA-256 is `ece0432aba11e6af754c86593d3c82c0fede2773cbb2a37b8cd4cee9f3c16f9c`. The [sanitized receipt](../measurements/2026/DrawingSceneViewRuntime01.json) binds each phase and native record without runtime addresses.

The four roles are ControlBefore, NativeSource, Generated and ControlAfter. Each opened with errors/warnings `0/0`, rebuilt successfully, retained immutable input bytes and completed owned cleanup. Ordinary sheet/view, ordered tree, dependency, note text/name/position, geometry, display and preference checks completed. The overall exit was zero. Both healthy controls remain part of the evidence.

Each process was sampled after open, before rebuild, after rebuild and after redraw. Every snapshot passed the bounded tree, pointer, type, source-getter and consistency guards. The two unique role/type keys are:

- `uiDrawingView_c`, `moDrSheet`, no `moDrView`, and `gfxSgSheetView_c`.
- `uiDrawingView_c`, no sheet or drawing-view model key, and `gfxSgDrawingView_c`.

All eight unique source/generated role-and-stage comparisons report equal state. In each process, both keys alias one actual UI view and one scene engine. These objects remain stable across the four stages. The keys do not establish independent renderer objects.

## Actual engine and dispatch identity

All rows use the independently verified `slddrwu.dll` getter RVA `0x39d360` and read its actual receiver field `+0x478`. The nonnull result has type `uiDrawingSceneGraphEngine_c`. Its virtual `+0x78` target belongs to `slddrwu.dll`, RVA `0x4f26c4`, image SHA-256 `61c8481374431866f97416ce5109329f9c38e7e85b56a9f95d41bdf3122cdc47`.

This is measured object and target identity. The observer did not execute this virtual function or observe its invocation. A complete loaded-module memory digest was not measured; original file identity and the guarded getter body were verified separately.

The memory reader used query/read access `0x410` on the exact owned process. The packet performed no process writes, debugger attachment, breakpoint, injection, setting change, document save or bitmap save. Ordinary vendor calls remained with the root-owned lifecycle observer.

## Preserved first failure and limits

The earlier exit-3 report remains immutable at SHA-256 `8b72327abb9fa7b73fc5b1b1f880b8c7f0f0be750b7736393bef39cb425e716e`. Its guarded layer reads were unknown, and its native-source ordinary check failed on a repeated `GetFirstView`. The retry supplies new completed observations. It does not prove the RPC cause or a product repair.

This packet measured no raster output. Equal sampled engine pointers and target identities do not explain the existing generated-note rendering failure. Transient state between snapshots and the actual annotation publication path remain open. Hidden inputs were not read. Held-out acceptance and writer qualification remain false.
