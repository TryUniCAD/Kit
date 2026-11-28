# SOLIDWORKS radial construction boundaries

Three research records now separate radial geometry references, tolerance ownership and attachment finalization in the pinned 2026 build.
These are static construction rules.
They do not add production write support.

The [arc-reference record](../../../../re/solidworks/records/ArcDimensionReferences2026.md)
traces retained radial creation, value-array append, temporary cleanup and constraint lookup.
One ordinary radial dimension adds one geometry constraint reference.
The optional lookup map registers only the first geometry handle.
Its stored index uses 16 bits, while append and direct lookup use the full array index.

The [parameter lifecycle record](../../../../re/solidworks/records/RadialParameterLifecycle2026.md#null-tolerance-and-retained-parameter-ownership)
now follows the null tolerance through construction, retained naming, repeated mode assignment and ordinary update guards.
The dimension owns its tolerance separately from its parameter.
The inspected null branch creates no replacement tolerance.

The [presentation record](../../../../re/solidworks/records/RadialPresentationConstruction2026.md#common-finalization-with-an-empty-attachment-list)
identifies the actual display attachment list and its empty constructor state.
The common finalizer returns without attachment processing when that list remains empty at entry.
This boundary does not prove that intervening operations preserve an empty list.

Use each record's concrete dispatch, field owner and operation bounds when extending the shared model.
The associated gotchas cover
[first-handle registration](../../../Gotchas/Conversion/Solidworks/Profile/RadialConstraintsRegisterOneGeometryHandle.md),
[index narrowing](../../../Gotchas/Conversion/Solidworks/Profile/ConstraintMapIndicesUseSixteenBits.md),
[nullable tolerance](../../../Gotchas/Conversion/Solidworks/Profile/RadialToleranceGettersDoNotAllocate.md)
and [shared getter addresses](../../../Gotchas/Conversion/Solidworks/Profile/DisplayGetterAliasesDoNotDetermineFieldOwnership.md).

Verification used exact instructions, concrete PE vtables, import and export metadata, and recorded method hashes from pinned 2026 modules.
No CAD process was accessed, no held-out stream was inspected, and no local tests ran.
Complete saved presentation state, later deletion and map rebuilds, curve source locking and native acceptance remain unfinished.
The production adapter remains read-only.
