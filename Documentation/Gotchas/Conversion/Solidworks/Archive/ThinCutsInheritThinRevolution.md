# Thin cuts inherit thin revolution

## Expectation

A thin revolution cut extends the ordinary cut class and appends thin-wall data.

## Actual behavior

The hash-bound SOLIDWORKS 2026 SP05.2 class metadata and direct RTTI reads establish
`moRevCutThin_c -> moRevolutionThin_c -> moRevolution_c`.
The thin cut does not inherit `moRevCut_c`.
Both thin feature vtables dispatch serialization to `0x4bb1e5f0` in
`sldmodu.dll`, SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`.
That method runs the shared regular-revolution serializer and then writes the
thin-spec object reference at runtime member `f8f0`.

The [native record](../../../../../re/solidworks/records/ThinRevolveArchive2026.md)
retains the concrete tables, RTTI locators, function fingerprints and field order.
These are static format facts. Native thin-file round trips and fresh construction
remain unproved.

## Workaround

Keep the semantic parent map consistent with the actual RTTI hierarchy.
Reuse the thin-revolution schema for thin cut, so the regular base and thin-spec
reference each appear once.
Preserve raw wire values separately from native load repairs and store-time
normalization.
Do not infer constructor defaults or numeric domains from class names or API enums.

The [change entry](../../../../Changes/Solidworks/Inspection/SolidworksThinRevolveArchive.md)
describes the version-19000 research-only extension and its acceptance limits.
