# Entity line-type field

Adjacent entity fields `f34` and `f38` can appear to be two forms of solver status because the fresh constructor sets both to one.

In the locked 2026 `sldmodu.dll`, serializer `0x4c583460` labels `+0x34` as `ConstraintStatus` and `+0x38` as `LineType`. Instruction `0x4c58387a` loads the ASCII `LineType` string at `0x4d1c90b8`; `0x4c5838a7` reads the u16 at entity `+0x38`, and `0x4c5838ae` emits it. The current constraint-status setter `0x4c5d5370` writes `+0x34` only.

Keep `f38` as the native constructor's line-type choice for this fresh branch. Derive solver state through its actual consumer and setter instead of treating nearby fields as aliases. Sketch `f128` is a separate saved-status field on a different class.

See [the construction evidence](../../../../../re/solidworks/records/ProfileConstruction2026.md) and [the locked binary manifest](../../../../../re/solidworks/v2026/Manifest2026.json).
