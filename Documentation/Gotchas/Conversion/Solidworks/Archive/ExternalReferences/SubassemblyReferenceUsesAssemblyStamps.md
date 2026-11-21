# A subassembly reference uses assembly stamp getters

The same ordinary reference class stores both part and subassembly placements. Its target model controls the geometry and transform stamp getters. The part geometry stamp reads the part's local geometry counter. The assembly geometry stamp traverses its resolved references. The assembly transform stamp folds its direct placement stamps. The assembly branch also selects `fc48` for its configuration options, while the part branch selects `fc50`.

Use the target's concrete model and its actual dependency state when constructing a reference. The pinned instruction trace identifies the separate getters. The native nested cohort will check their persisted values. [2026 native branch evidence](../../../../../../re/solidworks/records/NestedAssemblyReferenceState2026.md)
