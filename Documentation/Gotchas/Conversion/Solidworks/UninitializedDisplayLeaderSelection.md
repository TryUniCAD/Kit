# Display leader selection is not initialized

## Expectation

A fresh native display-dimension constructor supplies every field that its serializer stores

## Actual behavior

In the locked SOLIDWORKS 2026 `sldmodu.dll`, display constructors `0x4c86df20` and `0x4c86f550` initialize the shifted point at runtime `+0xf68` and `SetPoint` at `+0x650`
They do not initialize the separate `SelLeader` integer at `+0xf80`
The serializer stores that integer at `0x4c82e7ef`
The current schema calls it `ff80`

Setter `setForeshortenShiftedPoint` at `0x4c896990` writes a supplied leader index and point
It does not supply a default or change `SetPoint`
Zero found in a saved file would not establish a universal constructor constant

## Workaround

Require an explicit signed 32-bit presentation input while the semantic no-selection state or an independently verified neutral value remains unresolved
Do not substitute zero based on allocator behavior or saved controls
The research builder fails on a missing input and makes no generated-document acceptance claim

See [the constructor ledger](../../../../re/solidworks/records/ProfileConstruction2026.md) for the binary binding and remaining acceptance work
