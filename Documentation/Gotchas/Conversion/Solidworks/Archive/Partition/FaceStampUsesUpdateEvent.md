# Face stamp uses the current update event

The high word of `SWEntUnchanged` is the low 16 bits of the native face
tag. The low word is the model header's update counter when the face
stamp is assigned during the rebuild. Subsequent update steps can advance
the serialized header counter. L1 has a face stamp low word of 118 and
saved counter 120. Both linked child sources have low word 132 and saved
counter 134.

Pass the update-counter state at the face assignment to the typed
tracking helper. Use the final counter to write the saved header.
[Native call arguments and observations](../../../../../../re/solidworks/records/PopulatedPrismPartition2026.md#topology-and-ownership)
