<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Hold the owned session across native readback

Task A08f now establishes explicit background lifetime control on the verified empty owned SOLIDWORKS process.
The collector records the initial `UserControl` and `UserControlBackground` values.
It sets `UserControlBackground` and reads back both values before opening any control.
The started and completed lifetime journal events retain those actual values if a later call stalls.
The queued worker requires that recorded background lifetime control is true.

Each document cleanup records the `GetTitle` stage and retains the exact title passed to `CloseDoc`.
The immutable journal carries that operand before and after the close call.
Acceptance requires empty-document checks, healthy controls, explicit `ExitApp` and exit observation through the retained native handle.

The API documents a lifetime interaction when closing the last document of a background session.
The background control property provides an explicit hidden-session lifetime mode.
The [lifetime gotcha](../../../../Gotchas/Research/Workers/SolidWorks/BackgroundDocumentLifetime.md) links the relevant API contracts.

## Preserved trace observation

The trace-enabled run used source `c572f1ac8dfa613e8ff6bf9ea99e2be375deb63c` and SOLIDWORKS build `34.4.1.1011`.
Its journal contains 118 complete, chained events with SHA-256 `ada732dbf204c43a1d8e31d469c70b87cd8635c32fb88f7d60c60210198e0d2b`.
All five circular capture calls completed.
The final control remained inside the `close_document` stage from `2026-11-17T20:53:31.0736547Z` until the bounded deadline.
The trace predates the separate title-operand record.
Its pending stack contains `control_after` and `close_document` for `control.SLDPRT`.

The controller accepted zero native observations and settled the job in `waiting_application`.
Exact-ticket recovery terminated only the directly owned process and observed its exit.
The final spool and quarantine were retained.
Computer-use inspection exposed no SOLIDWORKS window or education/license prompt.

| Evidence                         | SHA-256                                                            |
| -------------------------------- | ------------------------------------------------------------------ |
| Controller receipt               | `d043a1829d86af0c143e74c6c552b22ca690bc595f30c1d3556f6368a576b15b` |
| Controller result                | `7ff2e97bf51538fa79a6ef76684b3afd400dddb858dfab647ba0da38027cc9c5` |
| Native recovery                  | `43e2dd96d762ce24c41b8615fc52ad7056125c5947fda56675d09f7263a05774` |
| Before and after input manifests | `06097a5d2cc4e97c3d8d014489f952dd28c3fafb33e39214ada7aa65a5a25116` |

All 3,762 recorded source and input file hashes were unchanged.
The timeout establishes cleanup and stage-retention evidence.
The later committed-source observation accepted P02 and P01–P03 with normal close and exit; P04 retained a final-control close timeout.
The [final-control follow-up](FinalControlDiscard.md) records the separate results and their immutable receipts.

## Implementation verification

The modified collector and existing rectangular Boss witness compiled against the installed `34.4.1.1011` interop assemblies without launching CAD.
The managed-process coverage carries an actual close operand through the C# journal and Python queue boundary.
It also rejects a reported run that lacks verified background lifetime control.
The lifetime assertion was present in both accepted scopes, but all four observed lifetime flags were already true.
Those observations do not establish that the setter caused the earlier stalled close to return.
