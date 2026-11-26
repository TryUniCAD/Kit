<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Windows console records need path containment

## Expectation

The parent process creates temporary records for console custody, worker identities, and cancellation timing.
Passing their paths to a child does not constrain paths supplied directly to that child's command.

## Observed behavior

The [PR #271 merge-group Python analysis](https://github.com/TryUniCAD/Kit/actions/runs/45185017149/job/137728252719) reported five path-injection findings.
The findings affected `ExitLeader`, `JoinConsole`, `PipeChild`, `WaitForPids`, and `WriteSignal`.
The [following PR #272 candidate](https://github.com/TryUniCAD/Kit/actions/runs/45185080106/job/137728464405) inherited the same findings.
PR type and formatting checks did not exercise the deferred security analysis.

## Resolution

Pass each selected record through the existing `convert.Security.PathBoundary.ResolveTemp` boundary before reading or writing it.
Validate each derived sibling path as well as the initial selection.
The boundary resolves symlinks and requires containment beneath the operating system temporary root.
Keep the existing CodeQL query, threat model, and concrete boundary model unchanged.

The leader starts a base interpreter to preserve process identity.
Its descendant must inherit the leader's package search paths to load the same containment boundary.
Pass those paths through the child process environment; keep the existing direct interpreter and custody assertions.
The [current-head review](https://github.com/TryUniCAD/Kit/pull/271#discussion_r4666702779) identified this required package propagation.

The normal Windows console cases retain their custody, cancellation, timing, and worker-cleanup assertions.
Fresh merge-group security analysis and native Windows execution remain required for the repaired revision.
