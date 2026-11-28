# A part model index can mirror the assembly name

In some SOLIDWORKS 2026 saves, the root assembly `swModel` and the linked part `swModel` both have the assembly filename stem in `swName`. The actual linked part has a separate `swFileRef` and its own file identity. Both direct occurrences in D01 reference the same child file and preserve their component labels separately.

Follow the model's file binding for the resolved ordinary external part when the stored model label mirrors the assembly filename. Retain the original `swName` for audit and preserve a distinct index label when it exists. [Typed file ownership and process evidence](../../../../../re/solidworks/records/ConcentricDefinitionNames2026.md)
