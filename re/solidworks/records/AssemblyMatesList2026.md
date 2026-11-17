# SOLIDWORKS 2026 assembly mate-list stream handoff

The [synchronized discovery files](../v2026/corpus/assembly-synchronized/Manifest.json)
have six unmodified bytes in `Contents/Config-0-MatesList`. The container-only
observation and [resolved map receipt](../measurements/2026/AssemblySyncReadbackProcesses9c0.json)
agree independently:

| Native parent | Start of resolved map | End of resolved map | Mate-list prefix | List count |
| --- | ---: | ---: | ---: | ---: |
| Empty | 91 | 152 | 152 | 0 |
| Single occurrence | 103 | 164 | 164 | 0 |
| Repeated occurrence | 107 | 168 | 168 | 0 |

The resolved stream is 5,295 bytes in all three. Its map-dependent bytes and
initial counter differ. The mate lists differ only at the first byte of the
32-bit prefix. The six bytes do not encode the occurrence count or the active
persistent feature identifier.

## Original save and load

The verified `slduiu.dll` has preferred base `0x48ea0000`, SHA-256
`025917f6acd906e041652386c763a7f5dea8c2c1e8190f50265a6c51bd5d51d7`.
`uiModelDoc_c::saveMateList` spans `[0x49728480,0x497288e9)`, with code
SHA-256 `370ac58403f6bd9cbc7e79a2a855239dfc983903891f5bc7d8998b8cfb27d1c9`.
The operand at `0x49728585` points to `-MatesList`. The function copies the
actual group's list from runtime `+0x60` at `0x497287b9`–`0x497287dc`, and
enters `useCacheArchive_c` state 1 at `0x49728804`. It writes the resulting
archive map count at `+0x50` through the signed-long insertion operator at
`0x4972881b`, then directly calls `suObList::Serialize` at `0x4972882c`.
The observed valid map counts fit the positive signed range. No object tag
wraps the list in this stream.

The verified `sldmodu.dll` has preferred base `0x4b140000`, SHA-256
`569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`.
`moModel_c::loadMateList` spans `[0x4b587dd0,0x4b5882aa)`, with code SHA-256
`3f062f5baf7b24a8ef239a12c21c7106121c64c183898d80e07e2ab60fc562f1`.
It enters cache state 1, reads the signed-long prefix for versions from
`0x1bc7` into a temporary at `0x4b588126`, then loads the list at `0x4b588137`.
The temporary is not used by the following list call; map state has already
been copied by the cache helper. The [map record](ArchiveMapConstruction2026.md)
explains that copy. The `suObList::Serialize` export in `sldmfcu.dll` at
`0x3c8cd960` is a seven-byte thunk to the shared list implementation.

Original unwind metadata found no reverse-chained fragments for the listed
save and load ranges. The owned Hopper analysis independently recovered the
loader and the named mate-group construction wrapper. Its private receipt
`AssemblyMateLoadNative01.json` has SHA-256
`aadfca7d1172f0788c68d3f3fbd8a2029ea3a2105a86429fd752a0eb7722fda9`.

## Mate-group creation is conditional

Before opening the mate-list stream, the loader asks for the first mate group
at `0x4b587e3f`. If it is missing, it finds the preceding reference through
the concrete `moReference_c` class at `0x4b587e5f`. Failure to find a reference
returns before opening the stream. Otherwise the loader calls the named
mate-group constructor at `0x4b587e99` and adds it relative to the reference.
An empty assembly cannot use this missing-group repair branch. The six-byte
empty mate list is separate from the serialized mate-group feature and does
not construct a group by itself.

The writer rule for the ordinary no-mate subset is to carry the generated
resolved map forward and serialize its actual count followed by an empty
object list. Mate object identities, nonempty serialized rows, legacy modes
and full assembly acceptance remain outside this result.
