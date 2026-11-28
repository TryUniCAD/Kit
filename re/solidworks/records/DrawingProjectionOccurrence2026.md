# Drawing-visible occurrence ownership

The second edge-observer attempt failed before parent/model or edge calls: both pristine native controls returned `IComponent2.IsRoot=False`. They still opened and rebuilt without warnings or errors, resolved the exact child bytes and authored configuration, and closed gracefully. No generated lane launched. [DrawingProjectionRootObserverNative01.json](../measurements/2026/DrawingProjectionRootObserverNative01.json) preserves this failure and refutes the preceding unit-root admission hypothesis; it does not qualify the annotation lifecycle.

## Actual native producer

The [source checkpoint](DrawingProjectionOccurrence2026.json) binds three complete original SP05.2 module hashes, complete unwind-owner fragments and exact table cells. The registered 2026 metadata gives IView.GetVisibleComponents offset 0xa00. RTTI identifies its actual auDrView XDispatch table 0x43244150, selecting 0x42bde860. The variant helper 0x42bde940 calls the fill routine 0x42c0a140; its projection/count helper 0x42c0a2d0 calls the imported `moDrView::createComponentForReference(view, actual component, 1, 0)` at 0x42c0a40d. The original import resolves to model 0x4c9947f0.

That factory creates the drawing-context reference chain, adds the view's model reference, constructs a moChainComponent and concatenates it with the actual child component. The ordinary valid-chain allocation branches in concat 0x4b82a1d0 install table 0x4ce9c808. This is not the child model's unit component. Its unit predicate +0x260 is false, its reference chain +0x278 is nonnull, and its resolved model +0xa8 can be nonnull. Under those conditions the exact IsRoot implementation stores false at 0x49120a6b. The observed false result therefore agrees with the native projection producer.

GetParent has separate semantics: it asks getMoComponentInstance, whose assembly configuration lookup uses the actual filed owner. Missing configuration ownership returns null. A drawing-owned context has no assembly configuration object. The public component model getter independently uses the nonroot component's resolved-model +0xa8 route. A null assembly parent and a resolved actual child are compatible; neither requires the root predicate to be true. The exact runtime class was not directly instrumented, so the construction path is labelled source evidence and the retry verifies observable ownership explicitly.

## Exact retry

NativePacket05 changes the expected IsRoot result to false for this ordinary projected-part profile. Parent must still be null. The component occurrence configuration must still be exactly empty. Its actual GetModelDoc2 result must be identical to IView.ReferencedDocument, both model types must be part=1, and the actual component model's active configuration must equal the explicit authored view configuration. All existing physical-path/hash, one-component/body, exact analytic edge, annotation, persistence, tree, geometry, rebuild and SaveAs/reopen gates remain unchanged. There is no wildcard, assembly profile or class-name substitution.

Trial SHA-256: `3224ebc2de12538b843206675b3dbad38791300b02dc2e995bc155c0c79d737c`.
Files SHA-256: `f85ce0e89b1244915f56d5fe4a9d7d502ddc89ce1c21f3ea5a3d5087556df080`.

The four CAD inputs, all case predictions, generated encoded paths and six unchanged helper tools are identical to the original packet. Packet03 and packet04, their failed receipts and their tool snapshots remain immutable. This new deck is pending native execution and makes no production or downstream-cache acceptance claim.

```powershell
python -B "\\Mac\Home\Documents\UniCAD\Oracle121Takeover\DrawingEdgeQualification01\NativePacket05\Tools\InspectDrawingEdgeQualification01.py" verify "\\Mac\Home\Documents\UniCAD\Oracle121Takeover\DrawingEdgeQualification01\NativePacket05\Trial.json" --sha256 3224ebc2de12538b843206675b3dbad38791300b02dc2e995bc155c0c79d737c
python -B "\\Mac\Home\Documents\UniCAD\Oracle121Takeover\DrawingEdgeQualification01\NativePacket05\Tools\InspectDrawingEdgeQualification01.py" run "\\Mac\Home\Documents\UniCAD\Oracle121Takeover\DrawingEdgeQualification01\NativePacket05\Trial.json" --sha256 3224ebc2de12538b843206675b3dbad38791300b02dc2e995bc155c0c79d737c
```

Only root executes these commands in the serialized reserved oracle after committing the independently authored tools. The new freezer takes an unused output plus `--source-root` for the private DrawingEdgeQualification01 directory. Host verify and syntax/F821 checks passed without CAD execution. The six-phase complete before/generated/after design and 240-second worker limits remain unchanged. An unhealthy observer bracket still skips generated phases. Progress and derivatives are only under NativePacket05/Inspection. The prior optional trace packet remains frozen and requires its own adaptation after a new baseline actually passes.
