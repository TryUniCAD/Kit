# Loading constructors do not define the fresh graph

A loading constructor can leave references null because deserialization will
restore them. Treating those seeds as a complete new-model initializer can
omit native ownership and structural objects.

The 2026 new-model part and assembly constructors call shared initializer
`0x4c00d8f0`. It constructs a unit self component and a relation manager owned
by the actual model. The separate `0x4c00edb0` loading/default path leaves
those slots null. Active user-unit and empty-list allocations also differ.

The typed `suObList` pointer store passes the actual pointer to `WriteObject`.
It does not replace an empty allocated list with a null tag. The common model
loader separately recreates empty `fa48` and `fa50` lists when their stored
pointers are null; the same equivalence is not yet closed for `f9d8`.

Trace the actual constructor caller, typed pointer store and loader fixup.
Keep constructor state, legal absent input and measured acceptance as separate
evidence. Loading seeds alone cannot prove a complete fresh graph.

The [construction record](../../../../../re/solidworks/records/ModelConstruction2026.md#shared-and-concrete-fields)
records the active callers and the exact self-component assignment.
