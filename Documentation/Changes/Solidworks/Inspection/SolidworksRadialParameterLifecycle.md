# SOLIDWORKS radial parameter lifecycle rules

The [radial lifecycle record](../../../../re/solidworks/records/RadialParameterLifecycle2026.md)
traces the retained local radial dimension through construction, display-handle copying, naming and ordinary archive operations.
It separates the dimension's reference count from the parameter's runtime connections and persistent IDs.

For the recorded operation sequence, the circle dimension's actual virtual reference methods preserve count zero.
Its private parameter retains one runtime connection.
The dimension's persistent ID comes from the shared model-header allocator during naming.
The parameter node's ID remains independent.

Use the concrete class's dispatch and each field's actual owner when extending the shared graph.
The [reference-count gotcha](../../../Gotchas/Conversion/Solidworks/Profile/ReferenceCountsFollowConcreteVirtualSlots.md)
explains why feature-dimension handle counts cannot be transferred to sketch circle dimensions.

Verification used pinned 2026 modules, PE vtables, direct instructions and recorded method digests.
No CAD application was accessed, no held-out stream was inspected, and no local tests ran.
General naming collisions, shared parameters, later presentation mutations and final native acceptance remain unfinished.
The production adapter remains read-only.

Direct 2026 RTTI subsequently corrected vtable `0x4d242c18` to the concrete
radial-handle class, whose immediate parent is ValG1. The existing codec's
hierarchy and verified virtual targets remain valid. The [RTTI gotcha](../../../Gotchas/Conversion/Solidworks/Model/DerivedHandleVtablesNeedRtti.md)
retains the exact locator, hierarchy and hash evidence.
