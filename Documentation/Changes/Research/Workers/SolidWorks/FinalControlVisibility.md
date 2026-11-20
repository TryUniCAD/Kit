<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Keep the final owned stock control invisible

Task A08f sets `DocumentVisible(false, swDocPART)` after all capture reads and before opening the final stock control.
Every document close records its actual `IModelDoc2.Visible` value in the result and flushed journal.
Current queued acceptance requires the final setting stage, an actual false visibility getter, the existing dirty/read-only/sole-document evidence, normal `QuitDoc`, empty-document state and normal owned application exit.
Capture order, source bytes, geometry/rebuild checks and global user preferences remain unchanged.

## Source-bound private observation

The private `HiddenObserved` comparison used registered build `34.4.1.1011`, committed base `56b2ad97b872789f00976a701060291ffaf5ac4a` and separately hashed private sources.
The private C# collector has SHA-256 `0b0ed266a53948bb4281776c567552b6a138745003aac803f0f398311680c836`.
Its immutable plan has SHA-256 `66b0f14a55073a3be5ec0280d26292f1345404ef9027801b29c8d7b10ebc7828`.
Exact PID, creation time, desktop session, image, named job, collector readiness and initial empty-document state were verified before native work.

All eleven capture observations and both stock controls passed.
Both controls had one solid body, volume `881814.3482038013 mm³` and center of mass approximately `[0.0000342258575562, -0.0000178782275778, 0.00988216068003808] m`.
The first control reported `Visible=false`; capture documents reported `Visible=true` after selection-based measurements.
After the scoped visibility setting, the final control reported `Visible=false`, `save_flag=true`, `read_only=true` and `document_count=1`.
Its exact `QuitDoc("control.SLDPRT")` returned in approximately `0.010002 s`.
The empty-session check, explicit `ExitApp` and normal exit through the retained process handle passed.
Both native and collector jobs were already empty before cleanup; no forced termination supplied this successful result.

| Evidence                                      | SHA-256                                                            |
| --------------------------------------------- | ------------------------------------------------------------------ |
| Private native receipt                        | `d50adfb282779641d22caf42bc5d967a3da0f847afc5592a5789ba17b15f630d` |
| Raw native result                             | `f8a08bdaf1d16601989d18958331a046f15e70b7a6849a341c97bcd74c437957` |
| Complete 309-event journal                    | `b596b375da36dddc74241732b583fd01388fc6f259f95b1d9f10a25469a2d695` |
| Identical before/after source-input manifests | `d80638680d101a644b1e3679b6e6f7151974eae216c00383567b3ef011baa3fd` |

All 3,768 source/input hashes and the private collector/launcher hashes were unchanged during observation.
The copied native inputs were rehashed afterward and remained identical.

## Order limitation and queued confirmation

The private plan's canonical serialization sorted its capture map.
That changed the read order from the queued receipt order; `units-inch` was last instead of `termination-through-all`.
The private host also used a held named job around its directly launched process.
These differences prevent attributing success exclusively to visibility.
The result proves the recorded private execution passed its native gates; it is not a queued controller acceptance or a universal cleanup claim.

The integrated change preserves the original queued capture order exactly.
Confirmation requires a new committed-source P04 queue run with that existing order, the actual final visibility getter and the original acceptance gates.
Earlier accepted P02 and P01–P03 cohorts remain retained and need no repetition.

## Original-order queued confirmation

The P04 queue run on `9fc3c9a238f3128691e6b6a90e7769fffdb82a65` completed with all eleven accepted capture observations and both healthy stock controls.
The unchanged receipt-driven order ended with `plane-yz` then `termination-through-all`.
The final control reported `Visible=false`, `save_flag=true`, `read_only=true` and `document_count=1`.
Its exact `QuitDoc` call returned in approximately `0.003996 s`.
The empty-document check, explicit `ExitApp` and held-process exit observation passed.
Controller acknowledgement and quarantine fence cleared normally; no recovery supplied this acceptance.

| Evidence                         | SHA-256                                                            |
| -------------------------------- | ------------------------------------------------------------------ |
| Controller receipt               | `457761181885a556a6cc4b2d7d687a3a5aade2dd556087ac3e59579cc56421f1` |
| Controller result                | `f7f654e4e8ca7c13b8c448f79b889905632290f00a5636c2e90acfab8e07f7d7` |
| Accepted measurements            | `4155be6166168634e5cc99b3ff9381f6cedce91ce54bc2a8407ba299972dfb12` |
| Complete 309-event journal       | `753c141b6cf75267b5c462a17c290cb5cdce31a766b85286bc3a842258480707` |
| Identical before/after manifests | `8d115986715dd3700d992001a57dd1c591b2f4cb49f73f236fe4f70be018fae7` |

All 3,768 source/input hashes were unchanged.
Elevated final inventory found no SOLIDWORKS process.
The accepted artifacts retain `native_qualified=false`; this is a completed bounded readback, not a universal translation claim.

## Focused verification

Real Windows process coverage carries the visibility-setting stage and getter through managed journal serialization and the Python queue boundary.
It refuses a visible final-control claim and a missing setting stage even when the event chain is recomputed consistently.
Historical collector provenance bundles remain explicit and unchanged.
