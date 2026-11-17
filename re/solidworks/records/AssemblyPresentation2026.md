# Ordinary SOLIDWORKS 2026 assembly feature ownership

The [discovery receipt](../measurements/2026/AssemblySyncTreeTopology03.json)
records the API's stable 22-, 23- and 24-node trees across 15 snapshots. The
empty assembly already exposes a mate group. Ordinary component references
appear immediately before it. The `LiveSectionFolder` appears after Sensors;
markup remains the actual `InkMarkupFolder`. These observations do not imply
that every API node is a serialized top-level feature.

Original `sldmodu.dll` build `34.5.2.0604`, preferred base `0x4b140000`,
SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`.
The original unwind table shows no reverse-chained fragments for these ranges:

| Owner | Half-open range | Code SHA-256 | Observation |
| --- | --- | --- | --- |
| `moLiveSectionFolder_c` constructor | `[0x4beae1d0,0x4beae297)` | `b32a5928460835997dabeadfeb308f84f0459c9f5d1d781030957469d3933475` | Calls folder base at `0x4beae1dd`; sets runtime byte `+0x378` to 1 at `0x4beae1fb`; asks for caption `0x5f4a` at `0x4beae228` |
| `moModel_c::getLiveSectionFolder` | `[0x4c022280,0x4c0223e1)` | `bff629211b95d8cacfe9ab922bfa9e8ec27f68ad23827d475ea6da9eab2addaf` | Searches the concrete live-section class, then checks a plane-section folder branch; its creation branch requires the boolean argument 1 and calls the constructor at `0x4c022336` |
| `moModel_c::getMateGroup` | `[0x4c0229d0,0x4c022a31)` | `7b251b45c80356fe5294dd1a957c98f8f1be72e09551a35e151cced089516e12` | Searches the concrete mate-group class; this getter does not construct a replacement |
| Mate group default construction | `[0x4bc85bc0,0x4bc85d4c)` | `cead0e667ccd54336c00047b70a0884338a27e0a9df0fdfd8fb92f086c8d2a78` | The concrete runtime factory calls this entry; it invokes the model-feature base and initializes the list count and state before any mates |

The [folder serializer](AssemblyArchive2026.md#live-section-folder)
stores the live-section member as `(byte == 1)`. REA resource evidence
`ev_ea47e089ff4e53cf1ed30a8b369dea42107ff472de5a8f3f2e36886e10c2ae99`
identifies string block 1525 in the English `sldresu.dll`, SHA-256
`531cf5d1c913f60f707652f0ecae600313d0970f7e649dcadec64983c484e111`.
The selected block at file offset 1871488 has 1286 bytes and SHA-256
`fa37e3551492e41c792f55cfc9f90003f8247f8653f325dda3232d413332c579`.
Sixteen UTF-16 length-prefixed entries consume it exactly; index 10 is
`Live Section Planes`. This supports the English caption without transferring
any resource payload into the writer.
