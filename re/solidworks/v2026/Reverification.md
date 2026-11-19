# SOLIDWORKS 2026 re-verification of the 2025 findings

Oracle: SOLIDWORKS 2026 SP05.2, `sldworks.exe` `34.5.2.0604`, `RevisionNumber()` = `34.5.2`, in the
Parallels VM "Windows 11" (ARM64 host, x64 emulation). Driven from macOS with
`prlctl exec "Windows 11" --current-user ...` and COM ProgID `SldWorks.Application.34`
(`re/tooling/sw2026/Swapp.py`).

Every 2025 statement below was checked against 2026 binaries or 2026-saved files before reuse.
Status words follow `Documentation/Reference/Research/Methodology.md`: **confirmed**, **partial**,
**changed** (held in 2025, different in 2026), **refuted**.

## Gotcha: `prlctl exec` argument order

`prlctl exec --current-user "Windows 11" ...` fails with "The virtual machine could not be found".
The flag must follow the VM name: `prlctl exec "Windows 11" --current-user cmd /c "..."`.
Without `--current-user` the command runs as `nt authority\system`, which cannot reach the
interactive SOLIDWORKS COM server.

## 2026 binaries

Read-only analysis inputs came from
`C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS`. The private inputs were moved
outside repository checkouts to
`/Users/odin/Documents/UniCAD/Sw2026Research01a1dc84/bin` under the current
research artifact policy. The external relocation manifest preserves every
file's size and SHA-256. Version identities are in `Manifest2026.json` beside
this file; no vendor software is distributed here.

| file              | bytes      | version       |
| ----------------- | ---------- | ------------- |
| `swccu.dll`       | 252 504    | `34.5.2.0604` |
| `sldarchiveu.dll` | 231 512    | `34.5.2.0604` |
| `sldmodu.dll`     | 46 536 280 | `34.5.2.0604` |
| `sldmfcu.dll`     | 8 274 520  | `34.5.2.0604` |

Ghidra 12.1.3 headless on macOS (`/opt/homebrew/Cellar/ghidra/12.1.3`, OpenJDK 21) analyses them;
the private analysis project and decompiler inputs now live under the external
`Sw2026Research01a1dc84/gh` directory. Earlier runs required a dot-free path
because `analyzeHeadless` rejects path elements that start with `.`. Existing
recorded addresses and binary digests are unchanged by the relocation.

## Results

| 2025 finding or observation | SOLIDWORKS 2026 SP05.2 result | Evidence |
| --- | --- | --- |
| `file_id` selects a signature triplet from a 1,000-row table in `sldmfcu.dll` `.rdata` at file offset `0x566c40`. | **Confirmed, moved.** The arrays occupy 16,000 bytes. The ID array starts at file offset `0x582ed0` and the triplet array starts at `0x583e70`. | All 1,000 rows match the recorded 2025 table at the same indexes, after normalizing signature byte order. All 13 case triplets match their ID's row. The earlier `smoke_box.SLDPRT` observation used row 598. |
| SOLIDWORKS uses `su_CArchive` in `swccu.dll`. | **Confirmed.** The archive methods are exported by name. | `ReadObject`, `ReadClass` and `getMapCount` exports have ordinals 708, 937 and 966. |
| `m_lpBufCur` at `0x38`, `m_lpBufMax` at `0x40`, `m_nMapCount` at `0x50`. | **Confirmed.** The character reader compares the cursor with the limit. The map-count accessors use `this+0x50`. | `swccu.dll` character reader, `getMapCount` and `setMapCount`. |
| Archive tag grammar uses `0xffff` for a new class, the `0x8000` class bit, `0x7fff` for a wide escape and zero for null. | **Confirmed.** The wide escape consumes a `u32`. | `ReadClass` at `0x31a3a2d0` and the [archive tag grammar](../records/ArchiveTagGrammar2026.md). |
| A new class and a new object each add one map slot. Existing object references and null add zero. | **Confirmed.** The first instance of an unregistered class adds two slots. A new instance of a registered class adds one. | `ReadClass` inserts the new descriptor and `ReadObject` maps the new object. The eight-control instrument confirms the rule. |
| The `u16` at `ResolvedFeatures` byte 604 equalled twice the feature count on the ladder. | **Confirmed for the ladder.** The field is the archive count of `moHistoryFolder_c.f3c8` items. | The values are 2, 4, 6 and 8 in L1 through L4 and zero in E0. The one-boss P04 fixture has zero items. The A0 assembly has one. |
| The low `u16` at `ModelHeader` and `Header2` byte 77 followed `24 + 2n` on the ladder. | **Refuted as a format rule.** The header field is the next persistent ID. | `moHeader_c::getHighestID` at `0x31a05230` returns `f08 - 1`. The allocator at `0x31a052d0` advances `f08` and skips reserved IDs. See the [header field record](../records/HeaderConstruction2026.md). |
| The `u16` at `CMgr` byte 1414 equalled the feature count on the ladder. | **Changed.** The sample's matching field is now the `u32` `moBaseConfiguration_c.nb00`, which counts the entries in `fb00`. | E0 and L1 through L4 have values 0 through 4 at byte 1610. The actual P04 count is 1 at byte 1662. Byte 1610 in P04 belongs to `f82c`. |
| `swXmlContents/KeyWords` starts with `0x86` and uses CRLF with no BOM. | **Confirmed for the sampled parts and assemblies.** It has a UTF-8 XML declaration and two CRLF pairs. | All 13 inspected fixtures have the prefix, two CRLF pairs, zero bare LF bytes and no BOM before or after the prefix. |
| Nominal model version marker `_MO_VERSION_18000`. | **Changed** to `_MO_VERSION_19000` with `_DL_VERSION_19000`. The sampled parts' Features XML declares `swVersion="19000"`. | Stream names and XML in the sampled 2026 corpus. Effective configuration context remains a separate field. |
| Container version 4, nibble-swapped names and raw deflate. | **Confirmed.** | Kit's `SldprtArchive` reads the 2026 framing. All 13 sampled containers have version 4. |

The [count-owner receipt](../measurements/2026/ReverificationCountOwners01.json) binds the
exact 2026 image hashes, the 2025 table export, and the disclosed fixtures at PR #121 head
`960ffde7a866ba94a83043fc8a7d21d0b9edb882`. The 2026 arrays have combined SHA-256
`315bebe5c09a28ba122f7095cffd53acad52a551956e2bb8c497f593fdb60f3f`.

The byte positions above describe the sampled streams. Use the typed
[configuration fields](../../../src/convert/adapters/solidworks/Archive/Bodies/Layouts/ConfigurationFields.py#L137)
for the `fb00` row count and the typed
[history-folder field](../../../src/convert/adapters/solidworks/Archive/Bodies/Layouts/Resolved/FolderFields.py#L49)
and [array count operation](../../../src/convert/adapters/solidworks/Archive/Bodies/Layouts/Resolved/CoreFields.py#L24)
for the history item count. The history field uses the vendor archive count width
rule. See the [count gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/FeatureLadderCountsDependOnOwners.md).

The five typed cursor traces consumed their CMgr, Config-0 and ResolvedFeatures
streams without a remainder. The probe observed existing schemas and disclosed
fixtures only. It did not re-emit the streams, use a held-out case or run SOLIDWORKS.
The meaning and construction of every `fb00` row across feature families remain open.
The [metadata finding](../records/MetadataConstruction2026.md#keywords-framing-and-evidence-limits)
records the separate work on KeyWords subtype and child-link grammar.

## New 2026 streams

The 2026 part container has streams that the 2025 notes do not list:
`Contents/3DExperienceExchange2`, `Contents/3DExperienceExchange_ConfigHeader`,
`Contents/PMISemanticDataDB` (each 12 288 bytes in a new part), and `Contents/eModelLic`.
Their load criticality is measured in `Deletion2026.md`.

## Not yet re-verified

- Object-level byte identity and field classification across the full, varied 2026 corpus.
  The eight-control instrument passed 56 critical-stream comparisons at head
  `66fd65e181af98583e51c5b570b90adbe25897d7`; this does not cover every real part or assembly.

The rooted instrument's CMgr, ModelHeader, Definition, Biography and History
archives start at map counter 1. Config-0 adds its direct external-object bindings
while loading. The resolved stream's prefix is the inherited configuration map
count, not a fixed base or a function of feature count. It includes the actual
header file-object bindings. Traced Config-0 maps started at 4 for the sampled
parts and 5 for A0 after the direct bindings. The observed nonempty ladder
prefixes include 109 through 113. In P04 the prefix is 121 and in A0 it is 103.
Each resolved read inherited the corresponding configuration's actual map.
The native cache-copy rule is recorded in
[ArchiveMapConstruction2026.md](../records/ArchiveMapConstruction2026.md); its
linked-stream remote check is tracked separately from unlinked byte identity.

The regenerated 2026 class map is now recorded in `SerializeMapDiff.md`. This supersedes
the earlier pending map-generation note, but does not establish schema or writer coverage.
