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

Copied read-only from `C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS` into `.rescratch/sw26/bin`
(not committed). Hashes are in `Manifest2026.json` beside this file.

| file              | bytes      | version       |
| ----------------- | ---------- | ------------- |
| `swccu.dll`       | 252 504    | `34.5.2.0604` |
| `sldarchiveu.dll` | 231 512    | `34.5.2.0604` |
| `sldmodu.dll`     | 46 536 280 | `34.5.2.0604` |
| `sldmfcu.dll`     | 8 274 520  | `34.5.2.0604` |

Ghidra 12.1.3 headless on macOS (`/opt/homebrew/Cellar/ghidra/12.1.3`, OpenJDK 21) analyses them;
the project lives under `.rescratch/sw26/gh` through a dot-free symlink because `analyzeHeadless`
rejects path elements that start with `.`.

## Results

| 2025 finding                                                                          | 2026 result                                                                                                                                  | evidence                                                                                                                             |
| ------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| `file_id` → signature triplet is a 1000-row table in `sldmfcu.dll` `.rdata`           | **confirmed, moved.** The 16 000-byte id and signature arrays are byte-identical to 2025. File offset `0x566c40` (2025) → `0x582ed0` (2026). | byte compare of both DLLs; 2026 `smoke_box.SLDPRT` uses row 598 (`08627406` → `5abca36a 909b2b36 b0c1dc51`)                          |
| SOLIDWORKS reads with `su_CArchive` in `swccu.dll`, API exported by name              | **confirmed**                                                                                                                                | 2026 `swccu.dll` exports `?ReadObject@su_CArchive@@...`, `?ReadClass@...`, `?getMapCount@...` at ordinals 708, 937, 966              |
| `m_lpBufCur 0x38`, `m_lpBufMax 0x40`, `m_nMapCount 0x50`                              | **confirmed**                                                                                                                                | 2026 `operator>>(char&)` reads `this+0x38` against `this+0x40`; `getMapCount` returns `*(uint*)(this+0x50)`; `setMapCount` writes it |
| class tag grammar: `0xffff` new class, `0x8000                                        | i`class ref,`0x7fff`+`u32`wide escape,`0` null                                                                                               | **confirmed**                                                                                                                        | 2026 `su_CArchive::ReadClass` (`0x31a3a2d0`): reads `u16`, `0x7fff` → `u32`, `0xffff` → load runtime class, then `m_nMapCount++` and `InsertAt` |
| map-counter rule: class definition +2, class reference +1, null 0, object reference 0 | **confirmed for class definitions in code**; full stream proof pending the 2026 object segmentation                                          | `ReadClass` increments the counter once for a new class; `ReadObject` maps the object                                                |
| `ResolvedFeatures@604` is `u16 2n`                                                    | **confirmed**                                                                                                                                | 2026 ladder `L1..L4`: 2, 4, 6, 8; empty part: 0                                                                                      |
| `ModelHeader@77` and `Header2@77` are `u16 24+2n`                                     | **confirmed**                                                                                                                                | 2026 ladder: 26, 28, 30, 32; empty part: 24                                                                                          |
| `CMgr@1414` is `u16 n`                                                                | **changed.** At 1414 the 2026 value is 0 for every part. The `u32` count is now at **1610**.                                                 | 2026 ladder `fieldscan`: offset 1610 is the only offset where `u16` = 0, 1, 2, 3, 4 for E0, L1..L4                                   |
| `swXmlContents/KeyWords` starts with `0x86`, CRLF line ends, no BOM                   | **confirmed**                                                                                                                                | 2026 `L1_boss`: first bytes `86 3c 3f 78`, two CRLF                                                                                  |
| `_MO_VERSION_18000`                                                                   | **changed** to `_MO_VERSION_19000`; `swXmlContents/Features` `swVersion="19000"`; `_DL_VERSION_19000`                                        | 2026 corpus                                                                                                                          |
| container version 4, nibble-swapped names, raw deflate                                | **confirmed**                                                                                                                                | Kit's `SldprtArchive` parses every 2026 file without change                                                                          |

## New 2026 streams

The 2026 part container has streams that the 2025 notes do not list:
`Contents/3DExperienceExchange2`, `Contents/3DExperienceExchange_ConfigHeader`,
`Contents/PMISemanticDataDB` (each 12 288 bytes in a new part), and `Contents/eModelLic`.
Their load criticality is measured in `Deletion2026.md`.

## Not yet re-verified

- Map-counter **bases** per stream (2025: 109/110/111 for `ResolvedFeatures`, 3 for `CMgr` and
  `ModelHeader`, 4 for `Config-0`). These need the 2026 object segmentation from the generative
  serializer.
- Full object-level byte identity and field classification across the 2026 corpus.

The regenerated 2026 class map is now recorded in `SerializeMapDiff.md`. This supersedes
the earlier pending map-generation note, but does not establish schema or writer coverage.
