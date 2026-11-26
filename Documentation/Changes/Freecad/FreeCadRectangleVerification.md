<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Current-head FreeCAD rectangle and saved-file verification

## Scope and source

This A16 verification uses public SDK revision `8509332301a665bf0e618f00089e185c8c3c7cd3`, tree `42b63f29b8b037315d7fb2aceac1327e15d692b5`, on 17 November 2026.
Installed FreeCAD 1.1.4 build `4fd3bf320d9566a27e60069fc8387448aaa3a094` is an isolated test oracle.
Production generation, native archive reads and replay run without the CAD application.
The [A16 register](../../Reference/Research/AutomationSteps.md#a16-freecad-end-owner-bindings) retains the broader qualification requirements.

Three caller-authored 37 × 21 mm rectangles cover forward, reversed and symmetric extrusion.
The initial two-length drivers are 11 mm forward and 5 mm reverse; symmetric thickness is 16 mm.
Each generated research package contains a calculated initial shape, a planar sketch and live spreadsheet dependencies.
Strict emission refuses before writing bytes.
Explicit research emission retains false `vendor_loadable` and `application_usable` result and metadata flags.
This verification does not promote those flags or qualify a general conversion route.

## Initial geometry, independent edits and fresh reopen

Each original package opened with one valid solid before explicit recompute.
All three measured 12,432 mm³, with XY centroid (18.5, 10.5) mm.

| Control   | Initial Z bounds, mm | Initial Z centroid, mm |
| --------- | -------------------- | ---------------------- |
| Forward   | [−5, 11]             | 3                      |
| Reversed  | [−11, 5]             | −3                     |
| Symmetric | [−8, 8]              | 0                      |

Initial `Touched` state was recorded separately from valid initial geometry.
Explicit recompute settled the feature to `Up-to-date`.
The native `RectangularBoss` is `Part::Extrusion`, linked to the four-entity, eight-constraint `Rectangle` sketch.
The document also retained `XY`, `Parameters`, `Bodies`, `Solid`, `Configurations`, `Default`, `FeatureTimeline`, `KitMetadata`, `Selections`, `Sketches` and `SupportPlanes`, with their recorded native types.
Two-length expressions remained `Parameters.depth_forward` and `Parameters.depth_reverse`; symmetric thickness retained its own driver.

Independent forward 11→14 mm and reverse 5→8 mm edits each produced 14,763 mm³ while preserving the other end.
The reversed control mirrored the cap positions and centroid.
Symmetric thickness 16→20 mm produced 15,540 mm³ with caps at −10 and 10 mm.
Each edit was restored and rebuilt before a distinct native save.
A second process reopened all three saved restorations at the original geometry and live expressions.
The two process births were distinct and ordered after normal exit of the first phase.
Both phases closed every owned document without stderr.
Four independent box controls and six native-authored extrusion controls passed.

An independent audit checked 37 geometry observations, all ten controls, five driving edits, vector cardinalities, source and artifact hashes, loaded native module hashes, process births, and initial-observation order before recompute.
Original packages and historical evidence remained unchanged.

## Persisted edits and native spreadsheet aliases

Five additional native saves retain deliberate driver changes before restoration: forward and reverse edits for each signed two-length control, plus symmetric thickness.
Their original embedded snapshots remain present.
A fresh process reopened all five with the edited geometry, cap positions, centroids and expressions before recompute.
The four two-length cases measured 14,763 mm³; symmetric thickness measured 15,540 mm³.
Both strict and permissive public reads refuse these stale inline snapshots with the expected differing `LengthFwd` or `LengthRev` reconciliation error.
This verifies the [inline snapshot guard](FreeCadInlineManifestGuard.md) on actual native saves.
It does not reconstruct an edited inline graph.

Three separately native-authored controls have no embedded Kit manifest.
Their direct expressions use actual `DepthInputs.FrontCap` and `DepthInputs.RearCap` aliases.

| Case                | Forward/reverse, mm | Actual forward/reverse cells | Volume, mm³ | Z centroid, mm |
| ------------------- | ------------------- | ---------------------------- | ----------- | -------------- |
| Mixed units         | 11 / 5              | D4 / B8                      | 12,432      | 3              |
| Equal and reordered | 7 / 7               | B9 / A2                      | 10,878      | 0              |
| Saved edit          | 14 / 5              | D4 / B8                      | 14,763      | 4.5            |

Mixed-unit cells retain their cm/mm spelling and typed units.
Equal values and reordered cells retain distinct end owners.
Native save and fresh reopen preserve the expected geometry and expressions.
Public reads recover the actual cell parameter IDs, current values and dependency IDs with no alias diagnostics.
Public unchanged-native writes reproduce each archive byte for byte.
This verifies the bounded [alias recovery](FreeCadNativeSheetAliases.md), independently of native body inventory or broader semantic admission.

## Evidence and reproduction

| Immutable private receipt               | SHA-256                                                            |
| --------------------------------------- | ------------------------------------------------------------------ |
| Rectangle preparation                   | `b3e9a27139af9f9dc7f50271e31fdb36b2f08bb7610171e7e4c78c91a406b691` |
| Rectangle edit phase                    | `bd7c3c411ec30392e23de037d09684906fff108c08b4cfebbdb51802051c2bfc` |
| Rectangle fresh reopen                  | `8d91893252fb3871de33dcd64899711deaf4541b16239f5ffe1ecd25a09c3675` |
| Audited rectangle report                | `964c96ba2d3980689e94c11419ffdbe14b4a2500dd24dbc8aeccfa2d10859f5c` |
| Persisted-edit and alias phase          | `03c604b9b3fa927b5244ea354a47f32834cca9037cf433a183998e9cd41730b6` |
| Persisted-edit and alias fresh reopen   | `0a453fbaa4dcc9d53d4735084f82b9aece0b05994903f6f6ffb1b32e361f631e` |
| Hardened rectangle audit                | `5ea5d557d9a240f24d7bcb75d347ba603c727e106947e31d1e5781d2c54961ec` |
| Hardened persisted-edit and alias audit | `d9e54ea9e4822c9412f438cd7492da87c31cb97bcde39ccd81626ff3b2d95da2` |

The operator retains the exact original collectors, raw receipts, configuration profiles, generated archives and failed attempts.
The [rectangle update](https://github.com/TryUniCAD/Kit/pull/158#issuecomment-6963455003) and [saved-case update](https://github.com/TryUniCAD/Kit/pull/158#issuecomment-6963514508) record the observed results before integration.
Reusable [oracle tools](../../../re/FreeCad/Oracle/) keep CAD execution outside production conversion.
Committed [native fixtures and provenance](../../../re/FreeCad/Verification/Provenance.md) support the [public process regression coverage](../../../tests/Research/Archives/FreeCadSaved/NativeSavedTests.py) without a CAD installation.
The parameterized public collectors are separate from the exact private scripts that produced the sealed measurements.
The public verifiers additionally enforce vector cardinality, finite measurements, source and script hashes, and Windows process-birth chronology.
Independent disposable process controls refused seventeen geometry, archive, source, module, script and process-birth tamper cases.

The seven existing A16 suites initially produced 119 passes and 23 native-alias replay failures in 1,011.98 seconds.
All failures occurred after a successful public read: the writer applied fresh reconstruction checks before selecting unchanged native replay.
The [scoped replay repair](FreeCadExactReplayOrdering.md) separates exact preservation from fresh reconstruction and keeps incomplete replay explicitly unqualified.
The nine committed native saved-file cases also passed at the integrated pre-repair source in 76.01 seconds.
They passed again after integration of the replay repair in 58.50 seconds, with zero forbidden CAD, process or network attempts.
Post-repair generation from the retained neutral documents reproduced all three original, natively measured packages byte for byte.
That check blocked native CAD imports, native CAD file reads, process launches and network calls before SDK import.
Strict generation wrote zero bytes in each case, research result and metadata flags remained false, and forbidden-operation attempts were zero.
The tested adapter source SHA-256 was `d029c0f89069f225269c75262b1145ebc475f48520a27b18f81b53ae0e1c7b01`.
This byte identity connects the unchanged generated geometry to its actual native-tested revision without rerunning unrelated CAD measurements.
The scoped recorded-payload check found no recorded writer payloads in 259 FreeCAD adapter source files.
The replay repair is source commit `810ba0038f63ffb4f9d2bcd0192c7b31f6eb3ca3`.
All 44 affected alias, replay and fresh-output/refusal case IDs passed, as recorded in the repair note; the final integrated 13-case replay suite passed in 80.89 seconds.
Together with the nine real saved-file cases, the focused repaired-source verification covers 53 passing cases.
The 119 earlier unaffected passes retain their original source and execution attribution; they were not presented as a new whole-suite run.

## Remaining boundaries

Edited inline graph reconstruction, cached BREP freshness, native body inventory, other initial-cache families, other application versions, held-out generalization and qualified cross-format routes remain separate work.
A13 and A15 retain their existing exit conditions.
The earlier witnesses and their limitations remain accurate for their original revisions.
