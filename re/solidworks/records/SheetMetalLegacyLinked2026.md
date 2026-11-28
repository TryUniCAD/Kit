# Legacy sheet-metal linked folders

Build 34.4.1.1011 supplies two disclosed generation-19000 tutorial witnesses with populated direct sheet-metal masters and CMgr mode zero. The pinned [legacy linked probe](../../tooling/sw2026/sheetmetal/InspectLegacySheetMetal.py) checks these witnesses offline through the same configuration and inherited map path as the frozen Config probe. Every added layout remains provisional for product use.

## Loader dispatch

The installed SP04.1 `sldmodu.dll` digest is `2201734ebe0106efde5a93e306067b4b5e2fdb0ba70bf38ce9a59242b283cb99`. Addresses below are RVAs.

| Wire owner | Descriptor and factory | Concrete dispatch |
| --- | --- | --- |
| `moFtrFolder_c` | Vtable `0x1f31ab0` | Serializer `0x10e1860` shares the existing folder fields. Concept callbacks at slots `0x4b8`, `0x4c0`, `0x3e8` and `0x3f8` dispatch to `0x10383a0`, `0x1039160`, `0x9e9940` and `0xefc4e0`. Its `0xa40` callback at `0x13cc10` returns false. |
| `moConfigTableFolder_c` | Descriptor `0x29a4f90`, factory `0xd6c1a0`, vtable `0x1f28358` | Inherits the same concept callbacks and dispatches directly to `moFolder_c::Serialize` at `0xd70af0`. The base emits `moFeature_c` and signed words at `+0x360` and `+0x370`, with loader version gates `0xa93` and `0x27b4`. |
| `moNativeConfigurationTableFeature_c` | Descriptor `0x2981df0`, factory `0x451cd0`, vtable `0x1ce7f98` | Serializer `0x4525b0` calls `moModelFeature_c` at `0x9d8580`. The load gate `0x374e` introduces a string, two signed words, a signed count and pairs of strings, then an inline `su_CTime`. The matching current store lane writes the same sequence. |

The plain folder and the Notes folder inherit the same serializer, but the concrete Notes callback at `0x13e180` returns true. Reusing that true value for the plain folder produced a pointer refusal at byte 1790. The false callback reproduced the plain payload independently on both witnesses. The proposed `su_CTime` wire width is 32 bits, based on the installed `swccu.dll` SHA-256 `7254b30f4eb77fd5b49fdbb0a7ab499ba3bf1d39a3f8f18d72090c2568967b49` read and store entry points at `0x1bc60` and `0x1bcb0`. The field's timestamp semantics and the meaning and limits of the scalar values and string pairs remain open.

## Deterministic observation

The six disclosed-input verification passes used pinned compatibility revision `b87f3b12b72874f4289b627d56e3740da2ab725b`. The frozen probe SHA-256 is `bc23bf8744fe292081ae2780eb6adc41d05630323dec2fd5026efdf419d24558`. Its four modern Config, CMgr and ResolvedFeatures replays remain exact. Two independent single-body saves close the resolved map at 434 and the two different body orders close at 580. The modern captures supply author-phase saved sidecars and have recorded reopen failures. A separate positive-Z A-only witness has a healthy independent read-only reopen.

A second pinned process inspected the actual CMgr store on all six witnesses. Each attempted the SDK writer and used the compatibility store for its final bytes. Read and store agreed on bytes, counter, typed slot roster and each shared object identity. Class descriptors were reconstructed with equal values. The private custody receipt SHA-256 is `bc26e4e6640e468275fffd3994bd4582b915e1cfb1b1b900f774cd314199d999`.

The first additional legacy exploratory replays used the pre-normalization working-copy rule SHA-256 `3dc8e736530d49072e1a8244652b98c7b384d16c317979a8edede0c66e2968ee`. Each reported interval re-emits all bytes, preserves incoming object identities and reproduces the resulting map roster.

| Record | Cover bytes and map count | Plate bytes and map count |
| --- | --- | --- |
| Plain folder | [1514, 1721), 195 → 196 | [1514, 1721), 172 → 173 |
| Native table feature | [9053, 9264), 261 → 262 | [5703, 5914), 217 → 218 |
| Configuration table folder | [8966, 9387), 258 → 262 | [5616, 6037), 214 → 218 |

The cover and plate source SHA-256 values are `0ae11e59dcac0d88e6dacde4ebcfbc666da5df65d974863dce8609e0b62b3fbc` and `abaa90aac3955099d76e20c2e5f1e4cc97e65c6311d019ca1603ec4596f4c3da`. The cover Config and CMgr replay 28,839 and 2,759 bytes. Its 116,246-byte ResolvedFeatures stream starts from configuration map 169 and initially refused at byte 17,775 in `moSheetMetal_c.f808.bend_allow`. The current rule below resolves that boundary. The plate exactly replays 28,076 Config bytes, 3,316 CMgr bytes and all 26,559 resolved bytes. The last stream has SHA-256 `aad4d9a52fb02b8f582d018a5ece1b5a2a063e8c6cbd5bfe4460e52413da5a38`, 22 roots and final map count 372.

These observations establish bounded archive structure. Native feature and topology correspondence, controlled leaf suppression and driver edit, held-out verification, and production admission remain open. See the [capture and invocation procedure](SheetMetalCapture2026.md).

## Mode-zero bend allowance

In installed SP04.1 `sldsmmu.dll` SHA-256 `3299f8676485bab354704fb190cff768393bcf9a0ccd225ba6b29271e3b462ea`, load RVAs `0x52ddc3` and `0x52df6f` read the signed `+0x30` and `+0x34` members. The store matches at `0x52dbac` and `0x52dbb8`. At generation 19000 the old dimension special case is bypassed by the version guard at `0x52dfa4`. The matrix loops take their bounds from allocated axes `+0x50`, `+0x70` and `+0x60`, with store loop at `0x52daf5` and load loop at `0x52dfb3`. The proposed layout still refuses nonzero values in the three preceding axis headers. The signed members have unresolved meanings and remain explicit.

| Witness | Embedded payload and map count | Signed members | Payload SHA-256 |
| --- | --- | --- | --- |
| Cover | [14574, 17799), 311 → 327 | 2003968329, 0 | `0a35d6c287a98c2d387c34754e2c707aed1cd42f8832d5f3dc3a5f721edc61a7` |
| Plate | [14954, 18347), 297 → 312 | 0, 0 | `866c291e86e9d4d38157272e94c315abe5c21100535de1f1317949c8c5ee30e3` |

Both embedded payloads consume and re-emit with existing object identities and exact read and store rosters. These runs used rule SHA-256 `3622650d31d86fd4c01ba7719137c9b246cafdfec448ef2f2c56dc64f5fbe76e` and probe SHA-256 `13841e2b68bdd1618181f1adbfab8c28779d68909cfa2e905cf99a1e980517bd`. The cover now refuses at `moSketchBend_c` byte 21,202. The plate still fully replays to map 372. [Bend-allowance field gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/LegacyBendAllowanceSignedFields.md)

The next cover record dispatches to the `moSketchBend_c` descriptor at `0x780170`, vtable `0x618198` and serializer `0x53b3b0` in the same sheet-metal module. Its serializer calls `moOneBend_c` at `0x536070` before any subclass fields. That parent begins with `moSheetMetalCommon_c`, typed sketch, component and dimension objects, signed members, a 16-bit word, a double, and a byte. The next mode-zero lane reads a second typed sketch, with an inline line handle when the sketch is present, and then a typed list. The parent’s remaining records and their axis and handle semantics remain open.

## One-bend and sketch-bend records

In the same SP04.1 sheet-metal module, `moOneBend_c` enters `0x536070` from `moSketchBend_c` at `0x53b3b0`. The verified generation-19000 mode-zero parent reads `moSheetMetalCommon_c` then typed sketch, component and dimension objects, signed fields, a 16-bit word, a double and a byte. The mode-zero second sketch is followed by an inline line handle only when present. In the matching `sldmodu.dll`, the concrete handle constructor at `0x1497eb0` uses vtable `0x208b4f8` and the typed `sgEntHandle::Serialize` entry at `0x14458a0`. Its first cover handle has index 2, signed member −1 and zero second member, and adds no object slot. The following tagged `suObList` adds two slots. The parent has two nontrivial typed transforms. The four body-cache owner fields are zero in this witness and are guarded as unsupported when nonzero.

The subclass refuses the mode-seven inline feature and raw body lane. Its bounded suffix reads the tagged sketch, three typed handles, curve link and signed member in the loader order. The cover observes a point handle followed by two line handles, a null curve and zero signed member. The measurement establishes the structure of this disclosed branch while leaving its feature semantics unresolved.

| Disclosed cover payload | Incoming and outgoing map count | SHA-256 |
| --- | --- | --- |
| [21202, 31690) | 343 → 388 | `d0c27113639d48bdcb9862c5825e4ae2293fe72748ae343bee25becdd13bec53` |
| [31692, 40318) | 389 → 427 | `e5b42f86fc68251fab2e419007dc25b35b0c57141ec57e77dcfe55d37c844875` |
| [40320, 48946) | 428 → 466 | `65bfa54fb3b38f6f25d7aa563996c7ee1f4e1acfeebe7bc0cf7dadab4ad2a6a2` |

The two fresh process runs used rule SHA-256 `611e9356f07d59def3d87aff4d09645a65892b934002986d088d3c40c8eef731` and probe SHA-256 `19f48a7770fd92146604e6f715844115cb167bbaf5051e379411dbe10766d87a`. Each sketch-bend payload reproduced its source bytes, incoming identities and map roster. The cover's first remaining refusal in this revision is `moSMMiteredFlange_c` at byte 57,224. The plate still fully replays at map 372, and does not exercise this branch.
