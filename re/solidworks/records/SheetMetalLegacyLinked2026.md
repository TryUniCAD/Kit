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

The following additional legacy replays used rule SHA-256 `3dc8e736530d49072e1a8244652b98c7b384d16c317979a8edede0c66e2968ee`. Each reported interval re-emits all bytes, preserves incoming object identities and reproduces the resulting map roster.

| Record | Cover bytes and map count | Plate bytes and map count |
| --- | --- | --- |
| Plain folder | [1514, 1721), 195 → 196 | [1514, 1721), 172 → 173 |
| Native table feature | [9053, 9264), 261 → 262 | [5703, 5914), 217 → 218 |
| Configuration table folder | [8966, 9387), 258 → 262 | [5616, 6037), 214 → 218 |

The cover and plate source SHA-256 values are `0ae11e59dcac0d88e6dacde4ebcfbc666da5df65d974863dce8609e0b62b3fbc` and `abaa90aac3955099d76e20c2e5f1e4cc97e65c6311d019ca1603ec4596f4c3da`. The cover Config and CMgr replay 28,839 and 2,759 bytes. Its 116,246-byte ResolvedFeatures stream starts from configuration map 169 and refuses at byte 17,775 in `moSheetMetal_c.f808.bend_allow`. The next rule must establish the actual mode-zero bend record sequence before treating any observed word as an array count. The plate exactly replays 28,076 Config bytes, 3,316 CMgr bytes and all 26,559 resolved bytes. The last stream has SHA-256 `aad4d9a52fb02b8f582d018a5ece1b5a2a063e8c6cbd5bfe4460e52413da5a38`, 22 roots and final map count 372.

These observations establish bounded archive structure. Native feature and topology correspondence, controlled leaf suppression and driver edit, held-out verification, and production admission remain open. See the [capture and invocation procedure](SheetMetalCapture2026.md).
