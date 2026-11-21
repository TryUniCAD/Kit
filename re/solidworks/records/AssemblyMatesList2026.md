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

The writer rule is to carry the generated resolved map forward and serialize
its actual count followed by the object list. The initial no-mate writer
supplies an empty list through the same codec.

## Populated planar mates

The [disclosed archive check](../measurements/2026/AssemblyPlanarMateArchive01.json)
verifies A17, A18, A19 and their synchronized child parts against the
[source lock](../v2026/heldout/AssemblyPlanarMateSourceLock01.json). It
reconstructs 51 logical streams byte for byte. All three resolved mate
groups have empty children and empty `f4e8`. Each separate list has one
complete mate and uses the resolved stream's final map.

| Mate | List bytes | Initial map count | Final map count |
| --- | ---: | ---: | ---: |
| Coincident | 3304 | 168 | 196 |
| Distance | 5117 | 168 | 207 |
| Parallel | 3234 | 168 | 196 |

Each `f3c8` row holds a detached plane wrapper under the endpoint ordinal.
It contains its own anonymous `moRefPlane_c` with persistent ID -1,
a unit component, and zero surface bounds. The matching `f410` row
carries the same point and normal and binds to an actual `moReference_c`.
Its `moCompRefPlane_c` refers to an occurrence chain whose external-feature
entry is the exact `occurrence.f4f8` object retained in the inherited map.
That entry's `f50` points to the occurrence itself.

The resolved component plane's `ff0.f00` matches the child's datum feature
ID. Its wrapper's `f08` matches the child model header update stamp and
`occurrence.f3e0`. The wrapper's `f74` matches the mate ID and `f78` and
`f7c` match the endpoint ordinal. Both transform fields `f10` and `f18`
match the occurrence transform. The tangent basis and normal come from
the datum frame rotated by that occurrence. The wrapper's `f100` is the
inverse of that world-space plane frame, including translation terms
`-dot(origin, axis)` for each of the rotated frame axes.

The driving distance is in the display's `f850` handle list.
`moFeatureDimHandle_c.ff0` owns the `ParallelPlaneDistanceDim_c`, whose
`f28` parameter's `f58` matches both the independent design length and
the display's `fad0`. It measures 0.06323 m in A18.

The pinned 2026 read and store proof now qualifies `moChainComponent_c`,
`moExtFeatureList_c` and `moReferenceChain_c` for the ordinary object archive.
All 51 disclosed stream comparisons still match. Every executed method in each
populated mate-list stream is proven for this archive version. Other parent
streams still reach provisional schemas. Fresh mate construction and native
acceptance remain open. [Reference-chain proof](PlanarMateReferenceChains2026.md)

The [wrapper construction trace](PlanarMateWrapperWriteState2026.md)
classifies the fresh resolved and detached endpoint state. The
[input translation trace](PlanarMateInputTranslation2026.md) binds
explicit alignment and the ordinary plane-distance options through the
native command and model setters. The exposed solver states require a
complete generated mate and controlled native measurement.

The [coincident registration and publication trace](CoincidentMatePublication2026.md)
separately binds resolved wrapper ordinals and the assembly-wide
reference counter. It relates the mate ID and creation log to both
headers, the active configuration and the independent mate-list stream.

Run from the repository root with the authorized disclosed source directory:

```sh
PYTHONPATH=src:re/tooling/sw2026/serial python3.14 re/tooling/sw2026/serial/PlanarMateSources.py \
  --source-root /absolute/path/to/disclosed-source-batch \
  --report /tmp/AssemblyPlanarMateArchive01.json
```
