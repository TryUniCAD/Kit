<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Accepted phase artifacts still need cross-record checks

## Expectation

An accepted Phase B observation describes the same saved archives as Phase A and the application process named by its dispatch.
A completed supervisor worker does not independently establish the application's normal exit.

## Original behavior

The A07 inference consumer checked dispatch and report process IDs without comparing the complete process birth.
It verified each phase's internal manifest but omitted the cross-phase archive comparison.
It also omitted the native worker's restart-handoff consistency checks.
Coherently rehashed synthetic process packets could therefore reach a parked observation with contradictory ownership or saved bytes.

## Repair and evidence

Use the [Fusion grid integrity implementation](../../../../Changes/Research/Controller/FusionGridEvidenceIntegrity.md).
It repeats the native contracts at the inference consumer boundary.
Retain the original archive records and controller receipts.
Submit changed definitions or new native evidence through the supported controller and supervisor.

The subprocess controls reproduce three original admissions and verify their refusal after repair.
Positive protocol controls remain parked and unqualified.
They contain authored protocol payloads, not fresh native evidence.
The saved automatic-versus-explicit policy still requires independent native proof.
