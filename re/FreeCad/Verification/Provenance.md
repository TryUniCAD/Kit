<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# FreeCAD saved-control provenance

These nine small native CAD files are immutable test evidence, totaling 71,805 bytes.
They are not writer templates or runtime package data.
Their SHA-256 values, original relative filenames, expected parameter owners,
values, units and dependencies are in [Cases.py](Cases.py).
Every copy is byte-identical to its closed source file.
Archive inspection found CAD document, shape, shape-map and string-hasher data;
no vendor software or persisted user home paths are included.

## Source and native witness

The source revision is `8509332301a665bf0e618f00089e185c8c3c7cd3`,
tree `42b63f29b8b037315d7fb2aceac1327e15d692b5`, on PR #158.
FreeCAD 1.1.4 was used only by the separate oracle owner.
The private custody directory is `.rescratch/A16FreeCad-85093323-20261117`.

| Native receipt                 | SHA-256                                                            |
| ------------------------------ | ------------------------------------------------------------------ |
| `VerifiedInitialGeometry.json` | `964c96ba2d3980689e94c11419ffdbe14b4a2500dd24dbc8aeccfa2d10859f5c` |
| `SavedAlias-edit.json`         | `03c604b9b3fa927b5244ea354a47f32834cca9037cf433a183998e9cd41730b6` |
| `SavedAlias-reopen.json`       | `0a453fbaa4dcc9d53d4735084f82b9aece0b05994903f6f6ffb1b32e361f631e` |

`RestoredForward.FCStd` is the closed native restoration from the rectangular
11/5 mm forward control. It retains its original inline manifests and parameters.
The original 37 × 21 mm profile, 12,432 mm³ volume and centroid
(18.5, 10.5, 3) mm were measured by the native lifecycle witness.

Five edited controls retain their original inline manifests while their actual
native spreadsheet values and extrusion geometry remain edited at save:
forward and reversed cases independently edit the forward and reverse drivers,
and the symmetric case edits its total thickness.
The separate fresh native process reopened every edited save.
These files establish saved-edit refusal controls; they do not implement edited
graph reconstruction.

Three alias controls were independently authored through the native API, without
either Kit manifest representation. The actual sheet object is `DepthInputs`.
The `LengthFwd` and `LengthRev` expressions refer to `FrontCap` and `RearCap`.
A separate label decoy does not acquire ownership.

| File                | Forward cell | Reverse cell | Saved native lengths, mm | Native volume, mm³ | Native centroid, mm |
| ------------------- | ------------ | ------------ | ------------------------ | ------------------ | ------------------- |
| `AliasMixed.FCStd`  | D4, `1.1 cm` | B8, `5 mm`   | 11 / 5                   | 12,432             | (18.5, 10.5, 3)     |
| `AliasEqual.FCStd`  | B9, `7 mm`   | A2, `0.7 cm` | 7 / 7                    | 10,878             | (18.5, 10.5, 0)     |
| `AliasEdited.FCStd` | D4, `14 mm`  | B8, `5 mm`   | 14 / 5                   | 14,763             | (18.5, 10.5, 4.5)   |

Each alias control has one valid solid and a live native extrusion tree. The rear
alias was assigned before the forward alias. The equal case also changes cell
addresses and physical unit spelling. Current saved native properties corroborate
the typed cell quantities; numeric equality or row order does not choose a driver.

## Offline process coverage

[NativeSavedTests.py](../../../tests/Research/Archives/FreeCadSaved/NativeSavedTests.py)
launches [CheckReadback.py](CheckReadback.py) in a fresh Python process per fixture.
The checker installs an audit fence before importing the public SDK, refusing
CAD-module imports, process launches and network operations. It then verifies
the source hash and manifest contract and performs actual public reads in both
strict and permissive modes.

The unchanged restoration retains its original typed driver values and owners.
All five edited inline saves refuse explicitly with unsupported edit reconciliation.
All three native alias saves recover the expected distinct cell identities,
authored units, current property values and exact expression dependencies.
Each native-only read writes a byte-identical unchanged-native replay.
Every source remains unchanged and forbidden-operation attempts remain zero.

Nine process cases passed in 62.77 seconds on the pinned research Python
environment, using the `85093323` public SDK. The command was:

```powershell
$env:PYTHONPATH = '<checkout>/src;<checkout>'
<PrCompletionEnvironment>/Scripts/python.exe -B -m pytest -p no:cacheprovider --import-mode=importlib -q --tb=short tests/Research/Archives/FreeCadSaved/NativeSavedTests.py
```

The process suite is collected through the existing test planner and merge-queue
suite; it requires no FreeCAD installation or private custody path.
This evidence covers the named controls only. It does not qualify the route,
promote public usability/loadability flags, reconstruct edited graphs, prove
cached BREP freshness or complete the broader A16/A13/A15 acceptance gates.
