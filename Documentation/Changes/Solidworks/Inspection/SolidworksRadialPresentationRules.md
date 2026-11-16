# SOLIDWORKS radial presentation construction rules

The [radial presentation record](../../../../re/solidworks/records/RadialPresentationConstruction2026.md)
derives ordinary radius and diameter prefixes from the 2026 constructor and resource vocabulary.
It maps the primary prefix to wire field `f7f8`.
It also classifies one radial mode bit and the instance-count flag.

Use these rules when extending the shared curve graph after its native source-family lock.
Keep runtime format selectors separate from serialized fields.
Preserve the remaining flag bits and their ordered mutations.

The [prefix gotcha](../../../Gotchas/Conversion/Solidworks/Profile/RadialConstructorsReplaceEmptyPrefixes.md)
explains why the base constructor's empty strings are insufficient for radial displays.
The production adapter remains read-only.
The complete radial display, curve writer and native acceptance remain unfinished.

Verification used the pinned 2026 modules, a read-only Ghidra database, PE vtables and direct instruction inspection.
REA supplied the complete resource inventory.
A bounded string decoder verified the selected payload hash and its exact consumed length.
No CAD application was accessed, and no local tests ran.

The documentation received source and link inspection.
Rendered review, reader task evaluation and complete standards-conformance evidence remain unavailable.

Direct 2026 RTTI subsequently corrected the retained handle's concrete label to
`moSkDimHandleRadial_c`, derived from ValG1. The actual virtual targets and prefix
rules remain unchanged. The [RTTI gotcha](../../../Gotchas/Conversion/Solidworks/Model/DerivedHandleVtablesNeedRtti.md)
records the locator hash and hierarchy; the existing shared codec already has the
correct parent link.
