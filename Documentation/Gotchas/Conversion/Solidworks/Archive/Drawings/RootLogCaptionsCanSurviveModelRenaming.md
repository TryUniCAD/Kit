# Root log captions can survive model renaming

An archived model name and its existing root revision-log caption need not stay equal.

The edited drawing derivatives in the controlled epoch batch contain model name `SavedDrawing` and root-log caption `EpochDrawing`. The log still belongs to the same actual model id, retains its event time and survives fresh reopen. The full typed origin, component and child/configuration joins pass.

Bind a revision log through its actual owned id and graph. Retain its caption separately. A fresh constructor can require matching authored names before emission, but that construction precondition must not become an unsupported universal read rule. Do not select a different root by matching captions or rewrite a saved caption to satisfy a reporter.

The [native lifecycle record](../../../../../../re/solidworks/records/DrawingSourceEpochNativeLifecycle2026.md#root-labels-and-attribution) records the phase-wide observation. It does not claim a particular live rename or setter call.
