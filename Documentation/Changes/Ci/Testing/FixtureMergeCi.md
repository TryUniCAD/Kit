<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Repair catalogue fixture merge checks

Task `PR-207-MERGE-CI` is owned by the PR repair agent.
The delivery is [PR #207](https://github.com/TryUniCAD/Kit/pull/207).
The scope covers fixture process failures, security findings, and integration with current queue scheduling.
Acceptance requires the updated candidate to pass every applicable PR and merge-group check.

Legacy Fusion phase workers load catalogue dependencies only for catalogue plans.
Process fixtures validate temporary paths and the exact supervised session before accessing their files.
The native environment fixture reports secret absence without printing secret values.
The provider cancellation fixture waits for an acknowledged turn before closing its actual owned process.

The native compiler fixture selects PowerShell through `GetSystemDirectoryW`.
It normalizes the child system-root environment from that trusted path.
Fixed PowerShell expressions receive file values through environment fields instead of constructing command text.
A Windows process check poisons the parent system-root setting and invokes the actual compiler launcher.
Invalid installation fixtures must fail before an application can start.
The existing shared Windows platform job executes this check.

The main integration retains its measured-part CLI case and platform sharding.
It also retains the PR authoring and builder process roster.
No acceptance assertion, security query, or required check is removed.

Local evidence includes 19 fixture transport and containment checks and 26 provider and broker process checks.
Full Mypy passed across 5,370 source files before the main integration.
Pyright reported zero errors on that revision.
The earlier [merge-group run](https://github.com/TryUniCAD/Kit/actions/runs/44973004408) passed its test shards and both platform jobs.
Its remaining system-root security finding prompted the trusted shell change.
The changed native launcher requires execution on the updated Windows candidate.
These results do not establish CAD translation or vendor acceptance.

See [session scratch containment](../../../Gotchas/Ci/Commands/SessionScratchRoot.md),
[Windows shell environment](../../../Gotchas/Ci/Windows/ShellSystemRoot.md),
and [pull base revision metadata](../../../Gotchas/Git/PullBaseSnapshotCanLag.md).
