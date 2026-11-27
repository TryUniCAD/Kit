<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Close the final owned read-only control without saving

Task A08f restricts the documented `QuitDoc` no-save operation to the final stock control after successful initial open verification.
Immediately before closing, the collector records the actual `GetSaveFlag`, read-only state and document count in both the result and the flushed progress journal.
It rechecks the exact owned scratch path, read-only state and sole-document count before `QuitDoc`.
The exact title operand is retained before and after the API call.
Ordinary captures, the first stock control and cleanup after failed initial open verification retain the existing `CloseDoc` path.

No global preferences, licensing options or save flags are changed.
Healthy controls, geometry checks, empty-document state, explicit `ExitApp` and normal exit through the retained process handle remain acceptance conditions.
The [background lifetime gotcha](../../../../Gotchas/Research/Workers/SolidWorks/BackgroundDocumentLifetime.md) links the API contracts.

## Committed lifetime observation

The private `LifetimeObserved` run used source `ee53cf759f08a1f5608311fea0447e97a4a681fa` and registered SOLIDWORKS build `34.4.1.1011`.
It continued through the same live process handles after temporary observation interruptions; no successful scope was repeated to repair reporting.

| Scope   | Captures accepted | Controls               | Application exit                | Journal events | Journal SHA-256                                                    |
| ------- | ----------------: | ---------------------- | ------------------------------- | -------------: | ------------------------------------------------------------------ |
| P02     |                 5 | Both observed          | Normal, held-handle observation |            147 | `ce04d282db0c220856ba0f69d8634890fd630a58dcbc0c40194e74111330af71` |
| P01–P03 |                14 | Both observed          | Normal, held-handle observation |            309 | `530cc5cd979c8dc9b2d7f2a5e8f927c9640c5001edc1bd8bd010a20616453e98` |
| P04     |                 0 | Final close incomplete | Exact-owner timeout recovery    |            244 | `353f2ecce0f0abd14bb55e8b711cf76e64e29c1c0ca25b06dddd2c540cbe4153` |

P02's final `CloseDoc` returned normally after 142.431 seconds.
P01–P03's final `CloseDoc` returned normally after 6.455 seconds.
Both calls received the independently observed title `control.SLDPRT`.
The initial `UserControl` and `UserControlBackground` values were both true; both remained true after the explicit lifetime assertion.
These successful observations do not establish why the earlier trace stalled or attribute the result to the setter.

| Scope   | Controller receipt SHA-256                                         | Controller result SHA-256                                          |
| ------- | ------------------------------------------------------------------ | ------------------------------------------------------------------ |
| P02     | `af152d82d0dda67875efa391cc242e646b9a9ff3adc9ac97e548eb97c5e395ba` | `c3036f6744c1a601049c850c84e0d41fd4b19c384c21ac4bdf7ce8af8a676152` |
| P01–P03 | `d225c6a368960498b0386125b28be1d70a63d6e486edd542a99c8b504579209b` | `551c64d349da54848dfd9377e3d32a0ffb2653f97e6f9ddaa13d28268d642044` |
| P04     | `56044067110e48648f608dca8489540e648a8318ab156839510622fe7c9c491f` | `3dbce642ef32a7b133d7d2a7c34170497c38281c49fc0463a9624d49b1b8e25a` |

P04 reached all eleven capture calls, then remained in the final control's actual `close_document` API call after `close_title` completed.
The pending event records operand `control.SLDPRT` at `2026-11-17T21:17:46.5119496Z`.
The bounded deadline produced `waiting_application` and retained quarantine.
Exact-ticket recovery terminated only the owned process and observed its exit; recovery SHA-256 is `59face847682757c78f4c04964d08d163f9885b69f7197736592fc19508ff56b`.
Elevated inventory then found no SOLIDWORKS process.
Computer-use inspection exposed no targetable SOLIDWORKS window or education/license prompt.

All 3,762 source and input hashes were unchanged.
Both manifest files have SHA-256 `269598375482fa91adaae6c479c4e69f844530c8899d37cf93a16e8bdde1c128`.
The accepted observations remain unqualified native research evidence and do not assert universal or lossless translation support.

## Focused verification

The real Windows process suite exercises managed journal serialization across the Python queue boundary, retaining the no-save stage, dirty/read-only/count state and exact operand.
It rejects a writable final-control claim and a mismatched operand even when the journal chain is recomputed consistently.
The complete collector and Boss witness compile against the installed interops without launching CAD.
The committed-source P04 run on `56b2ad97b872789f00976a701060291ffaf5ac4a` also timed out inside the exact final `QuitDoc` call.
Its flushed journal retained actual `save_flag=true`, `read_only=true` and `document_count=1` before the call.
The 270-event journal SHA-256 is `237b8bf2c44898676647e97499c98cc38b2cd070e8543f7f8c30d0380f001946`.
Exact-owner recovery SHA-256 is `15cfd38eb3e63069dcc148606edc69852a79b44e7302c85e1e83068ded4c47a6`.
Zero observations were accepted; all 3,768 recorded source and input hashes were unchanged.
The [private visibility follow-up](FinalControlVisibility.md) retains the next controlled observation and its order limitation.
