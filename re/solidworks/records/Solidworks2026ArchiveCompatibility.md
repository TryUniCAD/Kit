# SOLIDWORKS 2026 SP05.2 archive compatibility

The observations on this page apply to SOLIDWORKS 2026 SP05.2, build
`34.5.2.0604`. The [build manifest](../v2026/Manifest2026.json) records
`sldworks.exe` SHA-256
`3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe`
and lists the licensed modules by name, version, length and hash.

The [count-owner receipt](../measurements/2026/ReverificationCountOwners01.json)
records the offline comparison of eight external images to the manifest,
13 disclosed saved containers and five typed archive traces. It binds the
fixtures and the decoding source to [PR #121's measured revision](https://github.com/TryUniCAD/Kit/commit/960ffde7a866ba94a83043fc8a7d21d0b9edb882).
The [re-verification record](https://github.com/TryUniCAD/Kit/blob/e7bedf0df32d2e0b6defae065766b37f90a60e0f/re/solidworks/v2026/Reverification.md)
documents the wider comparison against the 2025 research.

## Container signatures

The 2026 `sldmfcu.dll` ID array starts at PE file offset `0x582ed0`. The
signature array starts at `0x583e70`. The first array contains 1,000
big-endian 32-bit IDs. The second contains 1,000 triplets of 32-bit words.
Reverse the bytes of each signature word to get its order in a saved container.

All 1,000 rows match the [2025 signature inventory](https://github.com/TryUniCAD/Kit/blob/960ffde7a866ba94a83043fc8a7d21d0b9edb882/re/data/Serialization/SignatureTable.json)
at the same indexes after the byte-order conversion. The two 2026 arrays
together have SHA-256
`315bebe5c09a28ba122f7095cffd53acad52a551956e2bb8c497f593fdb60f3f`.
All 13 disclosed containers use the three signatures selected by their
`file_id` and report container version 4. Their sampled archive
markers are `_MO_VERSION_19000` and `_DL_VERSION_19000`. The 11
part fixtures also report `swVersion="19000"` in their Features XML.

## Archive map

In the pinned `swccu.dll`, the character reader uses the cursor at
`this+0x38` and the buffer limit at `this+0x40`. The map-count
accessors use `this+0x50`. These are offsets inside `su_CArchive`.
`ReadClass` and `ReadObject` allocate one map slot for each new
class descriptor and one for each new object. References and null
leave the count unchanged. The [tag evidence](https://github.com/TryUniCAD/Kit/blob/e7bedf0df32d2e0b6defae065766b37f90a60e0f/re/solidworks/records/ArchiveTagGrammar2026.md)
records native branches and function-span hashes.

In the observed save path, the resolved-feature archive inherits its map
from `Config-0`. The native handoff copies the schema map, counter and active
store map. Its load counterpart copies the load array with the schema map
and counter. The first `u32` in the resolved-feature stream records the
inherited count. The [map handoff evidence](https://github.com/TryUniCAD/Kit/blob/e7bedf0df32d2e0b6defae065766b37f90a60e0f/re/solidworks/records/ArchiveMapConstruction2026.md)
identifies each native owner and the direct map entries for the header self
object and external file list.

CMgr started at map count 1 in all five traces. After the header bindings,
`Config-0` started at 4 in the four part traces and 5 in the A0 assembly
trace. These values describe the fixtures' header bindings. The native
direct-map helpers advance the current count for each object they bind.
In each trace the final configuration count equalled the resolved prefix.

## Count owners and counterexamples

The [typed configuration layout](https://github.com/TryUniCAD/Kit/blob/960ffde7a866ba94a83043fc8a7d21d0b9edb882/src/convert/adapters/solidworks/Archive/Bodies/Layouts/ConfigurationFields.py#L137)
reads `moBaseConfiguration_c.nb00` as the `u32` row count for `fb00`.
The [typed history layout](https://github.com/TryUniCAD/Kit/blob/960ffde7a866ba94a83043fc8a7d21d0b9edb882/src/convert/adapters/solidworks/Archive/Bodies/Layouts/Resolved/FolderFields.py#L49)
reads `moHistoryFolder_c.f3c8` through
[the archive count operation](https://github.com/TryUniCAD/Kit/blob/960ffde7a866ba94a83043fc8a7d21d0b9edb882/src/convert/adapters/solidworks/Archive/Bodies/Layouts/Resolved/CoreFields.py#L24).
Each decoded count matched the length of its own collection. The five traces
consumed their CMgr, Config-0 and resolved-feature streams in full.

| Fixture | CMgr `fb00` rows | CMgr count offset (bytes) | History items | Config start count | Config final count and resolved prefix |
| ------- | -----------------: | ------------------------: | ------------: | -----------------: | -------------------------------------: |
| E0 part |                  0 |                      1610 |             0 |                  4 |                                    103 |
| L1 part |                  1 |                      1610 |             2 |                  4 |                                    110 |
| L4 part |                  4 |                      1610 |             8 |                  4 |                                    113 |
| P04 part |                 1 |                      1662 |             0 |                  4 |                                    121 |
| A0 assembly |             0 |                       765 |             1 |                  5 |                                    103 |

The history count appeared at byte 604 in these traces. The one-boss P04
part had zero history items. Its CMgr byte 1610 belonged to `f82c`.
Use the typed owners when locating the counts.
[Feature ladder count gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Configuration/FeatureLadderCountsDependOnOwners.md)

The observed low word at byte 77 in the part ladder's ModelHeader and
Header2 came from `moHeader_c.f08`, the next persistent ID.
In the pinned `sldarchiveu.dll`, the getter at `0x31a05230` returns
`f08 - 1` as the highest ID. The allocator at `0x31a052d0` advances
`f08` and skips reserved IDs. The ladder's `24 + 2n` feature-count
correlation depends on the ladder's allocation history.
[Header field evidence](https://github.com/TryUniCAD/Kit/blob/e7bedf0df32d2e0b6defae065766b37f90a60e0f/re/solidworks/records/HeaderConstruction2026.md)

## Evidence limits

The comparison read external licensed images and disclosed tracked fixture
bytes offline. P04 is a SOLIDWORKS re-save of a generated tree and served as a
reader fixture. No native application ran as part of this comparison.
The receipt supplies static structure and sample correlation evidence.
Complete record semantics, held-out codec and native application acceptance,
and conversion coverage remain open under [PR #121](https://github.com/TryUniCAD/Kit/pull/121)
and the [conversion backlog](../../../Documentation/Maintenance/ConversionBacklog.md).
