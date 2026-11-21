# Internal blank drawing model construction

The SDK can now construct the full owning model graph for the bounded ordinary blank drawing from neutral inputs. Public writing remains disabled. UI and metadata composition remain separate work.

Use `DrawBuild` and `MakeDrawRoot` under `convert.adapters.solidworks.Drawing.Construction.Model`. Supply the model/sheet/support/folder names, typed style and unit settings, current feature target, creation epoch, an independent UUID4 and an explicit dimension-text-link preference. The factory returns `DrawRootGraph` with the actual model, measured sheet graph and persistent allocator.

The factory creates shared model state, document units, styles and canonical views. It binds the real drawing to its self component and relation manager. It creates three separate auxiliary lists, the native folder order, the active sheet and empty layer, property and block managers. The drawing has no part analysis-unit or model-visual object. It reads no saved file and calls no CAD runtime.

The final persistent boundary is computed from actual registrations. The root owns ID zero, its sheet/support reservation is bound to the same constructed objects, and the next value is nine. Transient block/review folders keep ID minus one. Preserve those owners when adding metadata or a linked model.

Admission is limited to the current archive-19000/SP05.2 target, the effective style profile, one unformatted ANSI A landscape sheet, matched semantic length units and empty managers. Invalid inputs fail explicitly. The factory does not supply an enclosing native file or silently omit unsupported content.

Four blank and two linked designs each pass two fresh processes with exact complete Definition bytes/maps, surrounding streams, SDK read/write and public projection. Eighteen construction rejection jobs and the existing four-process part-root regression also pass. All 34 processes retain zero runtime input reads. The shared model-owner guard adds only concrete schema-one drawing ownership; unresolved and older-schema owners remain rejected.

These are offline construction checks, without a new native acceptance run. See the [source ledger](../../../../re/solidworks/records/DrawingModelConstruction2026.md), [receipt](../../../../re/solidworks/measurements/2026/SdkDrawingModel01.json), [sheet factory](DrawingSheetConstruction.md) and [block identity gotcha](../../../Gotchas/Conversion/Solidworks/Archive/Drawings/DrawingBlockManagerAllocatesGuid.md).
