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

| 2025 finding                                                                          | 2026 result                                                                                                                                  | evidence                                                                                                                                                                 |
| ------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| `file_id` → signature triplet is a 1000-row table in `sldmfcu.dll` `.rdata`           | **confirmed, moved.** The 16 000-byte id and signature arrays are byte-identical to 2025. File offset `0x566c40` (2025) → `0x582ed0` (2026). | byte compare of both DLLs; 2026 `smoke_box.SLDPRT` uses row 598 (`08627406` → `5abca36a 909b2b36 b0c1dc51`)                                                              |
| SOLIDWORKS reads with `su_CArchive` in `swccu.dll`, API exported by name              | **confirmed**                                                                                                                                | 2026 `swccu.dll` exports `?ReadObject@su_CArchive@@...`, `?ReadClass@...`, `?getMapCount@...` at ordinals 708, 937, 966                                                  |
| `m_lpBufCur 0x38`, `m_lpBufMax 0x40`, `m_nMapCount 0x50`                              | **confirmed**                                                                                                                                | 2026 `operator>>(char&)` reads `this+0x38` against `this+0x40`; `getMapCount` returns `*(uint*)(this+0x50)`; `setMapCount` writes it                                     |
| class tag grammar: `0xffff` new class, `0x8000                                        | i`class ref,`0x7fff`+`u32`wide escape,`0` null                                                                                               | **confirmed**                                                                                                                                                            | 2026 `su_CArchive::ReadClass` (`0x31a3a2d0`): reads `u16`, `0x7fff` → `u32`, `0xffff` → load runtime class, then `m_nMapCount++` and `InsertAt` |
| map-counter rule: new class +1, new object +1, existing object references and null +0 | **confirmed** in code and the eight-control archive instrument; declaring a new class and its first object therefore adds 2                  | `ReadClass` increments for a new class; `ReadObject` maps the new object; a class-reference instance adds only its new object                                            |
| `ResolvedFeatures@604` is `u16 2n`                                                    | **confirmed**                                                                                                                                | 2026 ladder `L1..L4`: 2, 4, 6, 8; empty part: 0                                                                                                                          |
| `ModelHeader@77` and `Header2@77` are `u16 24+2n`                                     | **refuted as a format rule.** Those are ladder observations of the next persistent-id allocator; they cannot supply a fresh writer formula   | `moHeader_c::getHighestID` at `0x31a05230` returns `f08-1`; allocation at `0x31a052d0` advances `f08` and skips reserved ids; see `../records/HeaderConstruction2026.md` |
| `CMgr@1414` is `u16 n`                                                                | **changed.** At 1414 the 2026 value is 0 for every part. The `u32` count is now at **1610**.                                                 | 2026 ladder `fieldscan`: offset 1610 is the only offset where `u16` = 0, 1, 2, 3, 4 for E0, L1..L4                                                                       |
| `swXmlContents/KeyWords` starts with `0x86`, CRLF line ends, no BOM                   | **confirmed**                                                                                                                                | 2026 `L1_boss`: first bytes `86 3c 3f 78`, two CRLF                                                                                                                      |
| `_MO_VERSION_18000`                                                                   | **changed** to `_MO_VERSION_19000`; `swXmlContents/Features` `swVersion="19000"`; `_DL_VERSION_19000`                                        | 2026 corpus                                                                                                                                                              |
| container version 4, nibble-swapped names, raw deflate                                | **confirmed**                                                                                                                                | Kit's `SldprtArchive` parses every 2026 file without change                                                                                                              |

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
count, not a fixed base or a function of feature count. The observed ladder
prefixes include 109 through 113. The native cache-copy rule is recorded in
[ArchiveMapConstruction2026.md](../records/ArchiveMapConstruction2026.md); its
linked-stream remote check is tracked separately from unlinked byte identity.

The regenerated 2026 class map is now recorded in `SerializeMapDiff.md`. This supersedes
the earlier pending map-generation note, but does not establish schema or writer coverage.
