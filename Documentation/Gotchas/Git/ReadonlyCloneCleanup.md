<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Git object permissions can fail Windows fixture cleanup

## Expected behavior

A disposable clone is removed after its process assertions complete.
The source repository remains unchanged.

## Observed behavior

The Fusion admission fixture committed its verifier inputs in a private clone.
Windows then refused to unlink read-only Git loose objects during teardown.
All seven admission assertions passed, but each fixture produced `PermissionError` with `WinError 5`.
The error came from clone removal, not failed admission or insufficient native evidence.

## Workaround

Resolve and validate the exact task-owned clone boundary before recursive cleanup.
For a read-only regular file in that clone, add the write bit and retry unlinking once.
Keep unrelated errors visible.
Do not clear permissions recursively in the source repository or follow a target outside the temporary owner.

The [cleanup change](../../Changes/Research/Automation/FusionFixtureCleanup.md) records the actual process verification.
