<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# A private console must enable Ctrl+C before launch

## Observed failure

The [PR #271 native Windows shard](https://github.com/TryUniCAD/Kit/actions/runs/45193381516/job/137758518302) failed `CheckNativeStop[CTRL_C_EVENT]`.
The installed CLI returned zero, but shutdown took 61.14 seconds after the recorded cancellation request.
The required limit is 15 seconds. The independent maximum runtime is 60 seconds.
This result does not establish successful cancellation.

## API contract

[Microsoft documents](https://learn.microsoft.com/en-us/windows/console/setconsolectrlhandler) an inheritable attribute that makes a process ignore Ctrl+C.
Registering a custom handler does not clear that attribute.
`SetConsoleCtrlHandler(None, False)` enables normal processing for the caller and its future children.
The [control-event contract](https://learn.microsoft.com/en-us/windows/console/generateconsolectrlevent) states that Ctrl+Break still reaches handlers when Ctrl+C is disabled.

The inherited attribute explains why a handler registration alone cannot establish delivery.
The failed run did not record that attribute directly.

The pinned pywin32 type stub omits the documented `None` handler mode.
`EnableCtrlInput` supplies that narrow call signature at the actual API boundary.
The [pywin32 implementation](https://github.com/mhammond/pywin32/blob/main/win32/src/win32apimodule.cpp) handles `None` separately before checking callable handlers.

## Repair and verification

The disposable observer explicitly enables Ctrl+C before it starts the installed CLI.
Its custom handler still protects only the observer.
The supervisor retains its separate process group, and native break events still target their launcher group.
Keep the existing 15-second limit, shutdown receipt, and worker-cleanup assertions.

Formatting, typing, and source checks do not verify native console delivery.
Fresh execution through the existing Windows merge-queue roster remains required for this repair.
