<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Through-all direction needs a geometry witness

## Expectation

A negative through-all authoring request should produce an inward cut from the upper support cap.
The returned flag must be recorded separately from the physical direction.

## Observed behavior

Fusion 2706.1.17 reported a positive extent flag for the correctly authored inward scope cut.
The raw flag remained positive at the inspected timeline markers.
The previous hard false assertion rejected the study before archive publication.
Support at the pre-cut marker was also insufficient for the saved face relationship.
The pre-sketch marker resolved the upper cap correctly.

## Repair

Use the [bounded direction witness](../../../Changes/Research/FusionReadback/FusionNativeScopePrerequisites.md).
Retain the raw Boolean and both distinct rollback markers.
Prove direction from the verified support normal, the pre-cut half-space and measured material loss.
Retain all existing geometry and target checks.
Do not flip authoring direction to satisfy the returned flag.
Do not generalize this bounded witness to other shapes, orientations or builds without independent evidence.
Saved selection-policy proof and fresh accepted native Phase A/B remain separate requirements.
