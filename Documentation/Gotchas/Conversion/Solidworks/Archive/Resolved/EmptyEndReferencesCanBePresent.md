# Native saves can serialize present empty end-reference arrays

Freshly constructed ordinary boss specifications omit both reference
arrays. A SOLIDWORKS 2026 SP05.2 save of four disclosed bosses writes
`has_f28=1` and `has_f48=1`. Both serialized arrays have count zero and no
members. The corresponding reversed-blind, mid-plane and two-direction
semantics survive the save unchanged.

A decoder that requires the presence flags to be zero drops otherwise
qualified editable depth semantics. Check the flag together with the
covered count and member array. The reader admits the verified absent
form and the verified present-empty form. Nonempty arrays retain their
separate reference semantics and stay outside the ordinary end projection.

The [native and typed readback receipt](../../../../../../re/solidworks/measurements/2026/SdkCircleEndConditions01.json)
binds both archive states.
