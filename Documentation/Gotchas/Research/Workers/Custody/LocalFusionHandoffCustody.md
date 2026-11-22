<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Local Fusion handoff custody

## Expectation

A missing commit in both public repositories can appear to mean that the original source and native evidence are unavailable.

## Observed behavior

The [original custody record](https://github.com/TryUniCAD/Kit/pull/94#issuecomment-6921995314) explicitly retained its source bundle and evidence archives locally.
The original source checkout and complete corrected Phase A/B run remained in an older task's temporary directories.
A search limited to current PR worktrees missed those directories.
The Fusion agent recovered their locations from the original task's result notes.

## Workaround

Trace the original custody record and task result notes before declaring the handoff unavailable.
Verify the recovered commit identities and independently recorded receipt seals.
Preserve the original checkout, including unrelated untracked files.
Copy only reviewed source into the current task branch.
Do not merge old ancestry or publish private native evidence as a substitute for custody verification.

The [recovered admission change](../../../../Changes/Research/Controller/Admission/RecoveredFusionEvidence.md) retains the verified scope and remaining qualification requirements.
