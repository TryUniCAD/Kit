# Populated ghost-body records in the SDK Config codec

The existing manager grammar reached its inline row and stopped at
`moGhostBodyObject_c.FUN_4bf05390`. The SDK now uses the actual inline
field order for version 19000. Its Config map carries the same owner
identities into linked Resolved reading and writing.

| Owning field | Serialized rule |
| --- | --- |
| `f08, f0c, f10, fc0` | Four ordered signed integers retained by the typed row. Their complete generation semantics remain open. |
| `nb0, fa0` | Signed count and one signed identifier per row. The original method admits the array from version `0xf6d`. |
| `has_f50, f50` | Signed presence scalar and an actual native object tag when nonzero. Presence permits a null object tag. The original method introduces this field from `0xf81`. |
| `nf0, ff0` | Signed point count and the native `mgPoint_c.restore` field order per row, from `0xf8c`. |

The installed SP05.2 `sldmodu.dll` SHA-256 is
`569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`.
The complete exception range is `[0x4bf05390,0x4bf05784)`, SHA-256
`2c04d213d52ff74e4980b965a4d0113221dea5fe359bf9bc90b325844fe2729d`.
The three branch thresholds occur at `0x4bf05432, 0x4bf054b2, 0x4bf054fe`
and `0x4bf055ad, 0x4bf0561e, 0x4bf0566f` in the two directions.
The REA module identity evidence is
`ev_dce068421fbd5576d2d720304f0a68a8019d0cd19d551e09922617c41adf388d`.
The [earlier wire-state ledger](ArchiveWireState2026.md) separates the
presence value from the object itself.

`SdkGhostReadProof.py` exercises the complete linked SDK ingestion and
re-emission. The [disclosed receipt](../measurements/2026/SdkGhostBodyConfig01.json)
binds the corner original and width/height native saves. All six streams
and maps match. Each disclosed case carries a row with one identifier
and empty optional members. These measurements qualify persisted codec
handling for the observed shapes. Fresh part construction uses its
already verified empty ghost-body manager.
