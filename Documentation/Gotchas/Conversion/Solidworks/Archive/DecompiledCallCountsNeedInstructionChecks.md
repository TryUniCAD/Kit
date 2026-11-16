# Decompiled call counts need instruction checks

## Expectation

Each archive read shown in a decompiled serializer represents a distinct native
call and therefore another wire field.

## Actual behavior

One retained display-item listing duplicates a discarded u32 read in its historical
`0x1820..0x1828` branch. The actual native instructions contain exactly two calls,
at `0x4ba4cd53` and `0x4ba4cd60`.
These addresses belong to the pinned `sldmodu.dll`, SHA-256
`569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`.

The [material/display record](../../../../../re/solidworks/records/MaterialDisplayArchive2026.md)
retains the complete serializer identity and the ordinary 2026 field order.
The new display owner rejects other versions, so this finding does not establish
support for the historical branch.

## Workaround

Count actual call instructions and identify their arguments and control-flow
branches before translating a duplicated pseudocode operation into a schema.
Use the exact function and complete native extent.
Keep an unverified historical layout outside the admitted schema rather than
borrowing the current version's byte sequence.

See the [owner change](../../../../Changes/Solidworks/Model/SolidworksMaterialDisplayArchiveOwners.md).
