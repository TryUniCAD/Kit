# SOLIDWORKS drawing epoch native lifecycle

Four independently generated drawing/child pairs preserve their separate archive, root-event and History clocks through a controlled SOLIDWORKS 2026 lifecycle. The archive-before-creation, earlier root-event and later History-event cases all open, rebuild, accept a driving depth edit, save and reopen cleanly.

The [native receipt](../../../../../../re/solidworks/measurements/2026/DrawingSourceEpochNative01.json) records 18 distinct processes, healthy controls, 3,328 numeric checks and 20 separately replayed typed origin joins. Complete Definition bytes, actual child origin/event, component backlinks, native path, configuration-directory owner and clocks match their real sources.

The [field record](../../../../../../re/solidworks/records/DrawingSourceEpochNativeLifecycle2026.md) distinguishes stable creation/archive/event clocks from updated self, manager and child update times. History date-code lists append independently of their retained first event. Root captions can also differ from the renamed model while their actual id ownership persists.

The [separate host join deck](../../../../../../re/tooling/sw2026/epoch_join/MethodManifest.json) leaves the original native packet and collector immutable. It runs no CAD or VM calls. No SDK layout or public constructor is changed. The measured result is limited to these disclosed generated inputs; unsupported complete original sources and held-out qualification remain separate work.

See the [History code lifecycle](../../../../../Gotchas/Conversion/Solidworks/Archive/Drawings/HistoryCodesHaveIndependentSaveLifecycle.md) and [root log caption](../../../../../Gotchas/Conversion/Solidworks/Archive/Drawings/RootLogCaptionsCanSurviveModelRenaming.md) notes.
