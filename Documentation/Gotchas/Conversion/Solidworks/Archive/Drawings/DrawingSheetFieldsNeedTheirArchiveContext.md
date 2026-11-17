# Sheet own fields require the inherited archive context

## Expectation

A typed sheet own-field writer can infer its child references and optional presence from field names alone.

## Actual behavior

The inherited `moModelFeature_c` serialization already stores the sheet's plane, profile and detail-folder nodes. The own fields refer back to that exact profile and folder and may allocate another empty object list. Starting a fresh map would lose those identities or serialize children again.

The generic optional-field executor also allows a missing presence flag to fall back to absent membership. A sheet with a real profile reference but no explicit `has_f408` could therefore omit its own alias. The new sheet boundary rejects missing native presence flags before emission rather than silently losing that reference.

## Correct use

Continue the caller's actual `BodyWriter` map after inherited fields have completed, retain the actual child nodes and supply explicit presence flags. The complete-process checks confirm profile/detail-folder aliases and map continuation, and reject missing flags without successful output. Use the ordinary version-19000 profile; unsupported format/annotation states and nonempty ink lists remain explicit failures.

The front bundle constructs a preliminary blank Definition and then a populated Definition. Both legitimate calls must be counted when instrumenting this boundary; only the final container is delivered.

See the [internal usage guide](../../../../../Reference/Research/Solidworks/DrawingSheetWriting.md), [source ledger](../../../../../../re/solidworks/records/DrawingSheetWriter2026.md) and [process proof](../../../../../../re/solidworks/measurements/2026/SdkDrawingSheetWrite01.json).
