# Body-stamp counts are not body counts

A model with one final body can consume more than one body stamp while
creating or rebuilding it. The counter records allocations along native
operation paths, rather than the count of bodies in the final model.

The controlled 2026 authoring trace records two body-stamp allocations during
each extrusion and two more during its explicit rebuild. Distinct regeneration
and body-assignment call sites account for those allocations. Saving and
closing add no calls in those phases.

Compute bookkeeping from the actual operation lifecycle. Do not set the header
counter from final body count or copy the observed training counter values.
Constructor seeds and a completed native rebuild are separate states.

The [construction record](../../../../../re/solidworks/records/ModelConstruction2026.md#header-counter-and-save-lifecycle)
records the trace hash, phase counts, caller addresses and evidence limits.
