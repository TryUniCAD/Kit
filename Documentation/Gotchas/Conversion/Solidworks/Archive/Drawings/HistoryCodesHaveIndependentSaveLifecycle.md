# History codes have an independent save lifecycle

A native save does not necessarily replace the first version-history timestamp or create another version-state event.

In all four controlled epoch pairs, the native drawing save appends a new date-code-history entry while retaining the original first event and all six root provenance fields. The child changes its date-code list when the child itself is saved. Both lists then survive fresh reopen. The explicitly later History-event case also retains that distinct event time.

Keep the version event, date-code list and provenance fields as separate typed owners. Preserve their actual values during readback. Do not derive an event time from a build code, copy the observed native code as a writer default, or infer a signature/authenticity rule from this behavior.

The [native lifecycle record](../../../../../../re/solidworks/records/DrawingSourceEpochNativeLifecycle2026.md#independent-history-provenance) binds the exact packet, clocks and typed join. It describes this measured family and does not establish every History update path.
