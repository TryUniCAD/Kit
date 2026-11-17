<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Source-bound native FreeCAD replay

A16f and A16g now preserve an unchanged native FreeCAD archive even when its parsed feature graph cannot be reconstructed as editable output. The earlier writer ran the fresh-output feature gate before examining its retained source. All 23 source-authored alias process cases therefore read successfully but failed unchanged-byte replay. Their intentionally incomplete native observations are parser controls, not native application acceptance evidence.

The writer now selects exact replay only after its existing native-document payload, companion digest binding, recorded semantic digest and independent native reparse agree. The feature gate still runs. Unsupported feature labels can be reported for that proven replay route; malformed graphs and other emitter errors still propagate. Fresh writes, explicit rebuilds and changed native or typed semantics retain the rejecting feature gate.

A newly reachable incomplete replay keeps `mode: exact_native_roundtrip` and reproduces the source bytes, but sets `vendor_loadable` and `application_usable` to false in both the result and metadata. Every transfer is `carrier` with `source_opaque`. The `freecad.native_replay.unqualified` diagnostic and `unsupported_features` metadata list the unproven features. Strict public output refuses transactionally; explicit `AllowCarrier=True` permits byte preservation. Already admitted replay graphs retain their existing result flags, transfers and metadata keys.

The public transaction keeps existing destination bytes on refusal. Existing target and overwrite checks remain active. The repair adds no CAD dependency or new native qualification.

## Scope and delivery

Task: A16f/A16g regression; owner: jdharcourt with the A16 regression agent; delivery: [PR #158](https://github.com/TryUniCAD/Kit/pull/158). Dependencies are the retained native read/reparse contract and the public staged-write policy. The exit condition is passing all 23 alias process controls and focused replay, tamper and refusal controls without weakening fresh-output gates.

## Verification

The failure was reproduced at `8509332301a665bf0e618f00089e185c8c3c7cd3`. After the repair, all 23 alias process cases passed in 163.55 seconds. All 44 focused case IDs passed across verification: 23 alias cases, 13 replay transaction and tamper cases, and eight existing fresh-output/refusal cases. The combined run passed 42 cases in 170.31 seconds; the two strict controls correctly refused, but their harness initially expected the wrong exception class. After the harness used the registry's actual `UsabilityError`, both strict controls passed in 13.89 seconds. Production source remained unchanged between these runs.

The new process coverage includes incomplete byte replay with false flags and carrier transfers, compatibility with an already admitted sheet-only graph, strict stream and existing-file transactions, forced rebuild, fresh unsupported output, changed typed parameters, mismatched source hashes, mismatched companion bindings, changed replay snapshots, changed native XML with recomputed archive and binding hashes, and overwrite refusal or explicit replacement. It uses the actual public read/write entry points in separate processes. These source-authored controls do not establish native application acceptance.

See the [replay gate gotcha](../../Gotchas/Conversion/FreeCad/ExactReplayNeedsSeparateFeatureGate.md) and the [A16 register](../../Reference/Research/AutomationSteps.md#a16-freecad-end-owner-bindings).
