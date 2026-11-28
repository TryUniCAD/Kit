# Plain note API delegates and text owners

A public note call can appear to be a direct native-document virtual call, and its text position can appear interchangeable with its attachment cache. Both assumptions lose the actual owner.

In the pinned 2026 build, public `auModelDocWrapper.f50` is a QI-acquired inner API interface. Its virtual `+1440` reaches a model API dispatch, which gets the actual drawing UI document and invokes **that** document's `+2be0`. Applying `+1440` to the native document selects an unrelated method. The note is allocated during command setup before the API text is assigned.

Later registration retains the real display and local detail-item aliases in a typed detail-folder notes collection. `setAttachLocationWorstCase` updates existing display/cache points without allocating an attachment. The text point lives in the inherited text owner and participates in actual frame/direction/distance handling. `getDimText` does not install GenericText `f170`.

Use the [exact source ledger](../../../../../../../re/solidworks/records/DrawingPlainNoteApiOwnership2026.md) to keep these domains separate. A rendering repair that sets a null `f170` requires an actual sketch-block note and does not supply an ordinary sheet-note default. Keep the latter producer explicitly unresolved until its actual source path or a scoped native trace is bound. This checkpoint changes no public admission.
