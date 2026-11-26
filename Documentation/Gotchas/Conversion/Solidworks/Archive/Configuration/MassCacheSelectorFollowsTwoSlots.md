# A mass cache trailer follows two slots

A part can store two mass cache slots with an empty first slot. The
ordinary version-19000 reader still consumes the signed `f1638` word
after the slots. A one-slot cache can contain mass properties and end
immediately after that slot. Counting populated slots or testing the
presence of mass properties would shift the following part fields.

Use the physical slot count to decide whether the trailer is present.
The decoded value preserves the signed word when present. The selector's
meaning and a rule for constructing it remain open.
[Native field order and controls](../../../../../../re/solidworks/records/ConfigCacheSlice2026.md)
