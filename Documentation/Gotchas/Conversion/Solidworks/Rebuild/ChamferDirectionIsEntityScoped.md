# Chamfer direction is scoped to the selected entity

The registered SOLIDWORKS 2026 SP05.2 type library exposes `IChamferFeatureData2.GetIsFlipped(Entity)` with a required `IDispatch` input and a Boolean result. A preflight expecting a zero-argument getter rejected the first disclosed source packet before either candidate started. [Native failure and type-library receipt](../../../../../re/solidworks/records/EdgeChamferSource2026.md#registered-api-correction)

Resolve the actual source edge after `AccessSelections`. Confirm the definition's edge matches the independently identified stock edge before passing it to `GetIsFlipped`. This preserves the orientation check on the owning edge and keeps the query inside the rollback scope.
