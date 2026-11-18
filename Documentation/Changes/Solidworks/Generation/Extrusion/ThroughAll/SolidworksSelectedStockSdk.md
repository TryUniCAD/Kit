# SOLIDWORKS typed selected-stock construction

The internal SDK can construct one explicitly selected stock body for an ordinary version-19000 through-all circular cut. The result retains actual model and archive owners.

Call `MakeScopedThru` with a real `ThroughPartSpec`, `PartBuildInput` and `SelectedStock`. The selection must reference the input's actual single stock object. Missing, ambiguous, foreign and continuous automatic selection fails.

The constructor reuses the shared part, profile, end, atom, component-reference, stream and container models. It transmits no kernel body. Existing scope-zero output remains byte-identical.

All 62 guarded process checks pass. Three complete outputs match the earlier research constructor. The Front output matches the artifact measured in four healthy native processes and the six-stream saved audit.

Black, Ruff, steering, strict Mypy and strict Pyright pass for all twelve SDK files. The source donor scan is clean.

Public registry admission, original held-out qualification, multibody scope and continuous automatic selection remain open. [Constructor guide](../../../../../Reference/Research/Solidworks/Construction/SelectedStock.md) [Field and ownership evidence](../../../../../../re/solidworks/records/SdkSelectedStockConstruction2026.md) [Process receipt](../../../../../../re/solidworks/measurements/2026/SdkSelectedStockProcess01.json)
