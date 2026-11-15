# Resolved chains depend on store context

A resolved reference chain does not need mode 2 merely because a standalone
store would reject its runtime owner. Native persistence and contextual component
serialization provide separate valid paths.

The 2026 chain serializer checks `isPersistent`. That getter tests runtime
manager membership. Its exported implementation also has an unrelated bitmap
name, which a decompiler can display at the chain call site.

A context component can temporarily clear its chain's runtime owner before the
base store. With an existing owner, the normal archive branch clears it when
the chain is nonpersistent or the owner's part-type virtual predicate is true.
It restores the owner afterward. The wrapper does not directly rewrite the
mode, but its delegated chain serializer can normalize that mode.
Its construction helper only ensures that the feature list exists.

Keep manager membership, acquisition counts, path mode and archive owner
separate. Follow the enclosing native store path instead of forcing mode 2.
External feature entries must identify the document containing each path
reference. Their embedded file identity is distinct from the referenced part's
external-file record.

The [construction finding](../../../../../re/solidworks/records/AssemblyConstruction2026.md#reference-chain-persistence-and-saved-context)
records exact native addresses and remaining ownership constraints. These are
static findings. Complete generated component graphs and native acceptance remain
unproven.
