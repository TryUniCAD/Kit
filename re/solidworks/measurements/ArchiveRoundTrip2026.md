# SOLIDWORKS 2026 archive byte identity

Status: **failed instrument gate; no generated SOLIDWORKS output**.
This record concerns source-stream representation only.

## Initial remote run

Head: `c4c1dab545eda3c05eb70573d7c271541ec9af07`.
The [remote native-file job](https://github.com/TryUniCAD/Kit/actions/runs/43657489181/job/132639163406)
ran on Linux with Python 3.11.16.
It checked the eight redacted 2026 ladder controls from
`re/solidworks/v2026/corpus/ladder/Manifest.json`.
No tests ran locally.

| Stream                               | Exact, complete re-emissions | Result                                                          |
| ------------------------------------ | ---------------------------: | --------------------------------------------------------------- |
| `Contents/CMgr`                      |                          8/8 | pass                                                            |
| `Contents/Config-0-ModelHeader`      |                          8/8 | pass                                                            |
| `Contents/Config-0-ResolvedFeatures` |                          8/8 | pass                                                            |
| `Contents/Definition`                |                          8/8 | pass                                                            |
| `_MO_VERSION_19000/Biography`        |                          8/8 | pass                                                            |
| `_MO_VERSION_19000/History`          |                          8/8 | pass                                                            |
| `Contents/Config-0`                  |                          0/8 | section type 2 consumed four bytes fewer than its declared size |
| Total                                |                        48/56 | failed                                                          |

The process-boundary rejection checks for empty selection, missing streams and
a truncated real container passed. The native-file job as a whole reported
1 failed, 122 passed and 158 skipped. Those skips were existing fixture-dependent
checks; they are not additional 2026 acceptance evidence.

For `L1_boss`, the configuration stream has 25,390 bytes. Its second section
declares 22,334 bytes, but the schema consumed 22,330 and stopped at offset 25,386.
All eight configuration failures have the same four-byte deficit.
The schema rejects the discrepancy instead of accepting a copied tail or padding.

## Map bases observed in that run

The rooted CMgr, ModelHeader, Definition, Biography and History plans begin at
archive-map base 1. The reported final map counts include the classes and objects
that those streams define. They do not imply that a later fragment begins at 1.

ResolvedFeatures carries its map base in the stream. The observed bases include
109 for the undimensioned plain profile and 110, 111, 112 and 113 for the
dimensioned one-to-four-boss ladder. The shared parser reproduced those streams
without using a per-family recorded program.

## Remaining work

The missing field was recovered from the 2026 binaries after this run.
`sldmodu` instructions `0x4c238177`–`0x4c238180` pass the archive in `r8` to
bridge slot `+0x648`; the pseudocode omitted that argument.
In `sldsmmu`, vtable `0x3d9cca88` selects thunk `0x3d8e3150`, which calls
`0x3d773430`. The load reads an i32 count at `0x3d7734e7`, then tagged
`moPerBodySheetMetalDataNew_c` entries at `0x3d77350d`.
The store reads the array count from model `+0x16f8`, with pointer data at `+0x16f0`.
The field is present after version `0x1481`, between the two-map block and
the bounding-box cache. A zero entry count explains the four-byte deficit.
This is a counted array, not a proven constant or a padding span.
Nonzero entries still require their class schema and fail closed when it is absent.

Rerun the same remote checks with the typed count and array.
A successful follow-up must bind to its own exact head and keep
the initial failure above as history.
This gate does not prove field semantics, unrelated-design constants, held-out
generalization, neutral-model synthesis, or target-application acceptance.
