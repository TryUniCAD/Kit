# A repeated drawing sheet-view read can fail

## Expectation

Repeated `IDrawingDoc.GetFirstView` calls within one read-only inspection keep returning the active sheet view.

## Observed behavior

In the disclosed SOLIDWORKS 2026 SP05.2 scene-view run, the native note source opened `0/0`, rebuilt successfully and completed all four guarded memory snapshots. Five `GetFirstView` calls succeeded. After a post-redraw `GetAnnotations` returned one annotation, the sixth call failed with `RPC_S_UNKNOWN_IF`, HRESULT `0x800706b5`. Both pristine controls and the generated phase passed, inputs stayed immutable and owned cleanup succeeded. The cause is not established.

## Workaround

Preserve the failed run and unknown post-failure fields. For a separately frozen retry, acquire one fresh drawing/sheet-view interface per state and reuse its actual annotation collection for related checks. Do not swallow an RPC error or substitute earlier annotation data. Complete memory evidence may be reported independently, while full ordinary verification still fails until it completes.

This is a bounded observer-method change, not a proved product or RPC fix. [Exact first-run evidence and source boundary](../../../../../../re/solidworks/records/DrawingSceneViewRetry2026.md).
