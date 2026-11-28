# Generated distance mate edit probe

`InspectDistanceMateEdit.py` measures one authored planar distance assembly between two A18 controls. It opens a newly generated bundle at its exact encoded paths, edits the native assembly D1, compares the solved placement and geometry, saves the owned child and parent, and measures the persisted edit in a separate fresh process. The original candidate and its read-only evidence remain separate. [Open and solve evidence](../../../../../../../re/solidworks/records/GeneratedDistanceMateNativeOpen2026.md)

The observer derives child parameter expectations from the authored scope. This case uses a vertex-authored rectangle and one active boss depth. It checks that the two unrequested sketch parameters are absent and still measures the prism analytically. The owned child and parent must retain exact resolved identities, clean feature diagnostics, and synchronized save state. [Child parameter gotcha](../../../../../../Gotchas/Conversion/Solidworks/Oracle/Assembly/PrismSizesDoNotDeclareSketchDimensions.md)

Use `PrepareDistanceMateEdit.py prepare` with the frozen read-only trial, regenerated pair, sanitized native observation, and an unused output directory. After hash verification, run the frozen observer with `run EditTrial.json --packet-sha256 HASH` in the pinned oracle. Run the preparer's `check-saved` mode after a qualified batch to read the persisted D1 and selected planes directly from the saved bundle. The guarded regeneration and no-CAD packet verification passed. Native driving edit, save, fresh reopen, and held-out acceptance remain pending at freeze. [Preparer](../../../../../../../re/tooling/sw2026/PrepareDistanceMateEdit.py) · [Observer](../../../../../../../re/tooling/sw2026/InspectDistanceMateEdit.py)

The disclosed edit from `0.071375 m` to `0.088125 m` passed in the pinned
oracle. Both saves and the fresh reopen passed with zero errors and warnings.
The saved archive readback recovers the edited dimension and the original
two ordered plane references. Both A18 controls passed. Held-out acceptance
remains pending. [Native edit and typed readback](../../../../../../../re/solidworks/records/GeneratedDistanceMateEdit2026.md)
