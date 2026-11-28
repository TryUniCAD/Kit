# Empty exclusion lists retain constructor names

An empty serialized detail exclusion list does not necessarily produce an empty runtime list in SOLIDWORKS 2026.

The pinned `moDetailDefs_c` constructor installs its native unit-token exclusions. The ordinary current loader clears that list only when the incoming count is positive. A zero count leaves constructor rows intact. The completed disclosed pairs therefore change from a zero wire count to ten names after their first native save.

Supply an explicit positive authored exclusion set when that is the intended model state, and compare every row after a fresh native save/reopen. Do not ignore the difference, infer a generic empty-list repair from legacy code, or copy a saved list into a constructor. A promise to preserve a truly empty set still requires a supported representation and native proof.

The [exact constructor/load ledger](../../../../../../re/solidworks/records/DrawingDetailNormalization2026.md) includes the version guards, native literal/resource provenance and the separately frozen experiment. Its unrelated two-string authored case is intended to distinguish positive-count replacement from unconditional default insertion. That new native measurement remains pending.
